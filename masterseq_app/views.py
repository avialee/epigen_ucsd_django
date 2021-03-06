from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SampleCreationForm, LibraryCreationForm, SeqCreationForm,\
    SamplesCreationForm, LibsCreationForm, SeqsCreationForm, SeqsCreationForm,\
    LibsCreationForm_wetlab, SeqsCreationForm_wetlab, BulkUpdateForm, EncodeDataForm
from .models import SampleInfo, LibraryInfo, SeqInfo, ProtocalInfo, \
    SeqMachineInfo, SeqBioInfo, choice_for_preparation, choice_for_fixation,\
    choice_for_unit, choice_for_sample_type
from django.contrib.auth.models import User, Group
from nextseq_app.models import Barcode
from epigen_ucsd_django.shared import datetransform
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from epigen_ucsd_django.models import CollaboratorPersonInfo
import xlwt
from django.db.models import Prefetch
import re
import secrets
import string
from random import randint
from django.conf import settings
import os
from setqc_app.models import LibrariesSetQC
from singlecell_app.views import get_tenx_status, get_cooladmin_status, check_cooladmin_time, getReferenceUsed
from singlecell_app.models import CoolAdminSubmission
import subprocess
import datetime
from django.core.exceptions import PermissionDenied


def nonetolist(inputthing):
    if not inputthing:
        return []
    else:
        return inputthing


def removenone(inputlist):
    # remove None and duplicate value in inputlist, e.g. ['fe',None,'','gg'] to ['fe','gg']
    if not inputlist:
        return []
    else:
        y = [x for x in inputlist if x]
        return list(sorted(set(y), key=y.index))

def load_protocals(request):
    """ We did not use the ProtocalInfo in the later development, could consider removing this
    """
    exptype = request.GET.get('exptype')
    protocals = ProtocalInfo.objects.filter(
        experiment_type=exptype).order_by('protocal_name')
    print(protocals)
    return render(request, 'masterseq_app/protocal_dropdown_list_options.html', {'protocals': protocals})


@transaction.atomic
def BulkUpdateView(request):
    update_form = BulkUpdateForm(request.POST or None)
    i = 0
    titleinfo = {}
    colinfo = {}
    """
    The field name in template is not always the same with that in the model. 

    """
    title2field_seq = {
        'label (for qc report)': 'default_label',
        'team member intials': 'team_member_initails',
        'date submitted for sequencing': 'date_submitted_for_sequencing',
        'date': 'date_submitted_for_sequencing',
        'library id': 'libraryinfo',
        'sequening length': 'read_length',
        'read type': 'read_type',
        'portion of lane': 'portion_of_lane',
        'i7 index (if applicable)': 'i7index',
        'i5 index (or single index)': 'i5index',
        'notes': 'notes',
        'i7 index': 'i7index',
        'i5 index': 'i5index',
        'label': 'default_label',
        'sequencing length': 'read_length',
        'team member initials': 'team_member_initails',
    }
    title2field_lib = {
        'sample id (must match column i in sample sheet)': 'sampleinfo',
        'library description': 'library_description',
        'team member intials': 'team_member_initails',
        'date experiment started': 'date_started',
        'date experiment completed': 'date_completed',
        'experiment type': 'experiment_type',
        'protocol used': 'protocal_used',
        'reference to notebook and page number': 'reference_to_notebook_and_page_number',
        'notes': 'notes',
        'sample id': 'sampleinfo',
        'team member initials': 'team_member_initails',
    }
    title2field_sam = {
        'date': 'date',
        'sample description': 'description',
        'species': 'species',
        'sample type': 'sample_type',
        'preperation': 'preparation',
        'fixation?': 'fixation',
        'sample amount': 'sample_amount',
        'units': 'unit',
        'unit': 'unit',
        'service requested': 'service_requested',
        'sequencing depth to target': 'seq_depth_to_target',
        'sequencing length requested': 'seq_length_requested',
        'sequencing type requested': 'seq_type_requested',
        'notes': 'notes',
        'date sample received': 'date_received',
        'initials of reciever': 'team_member',
        'storage location': 'storage',
        'internal notes': 'internal_notes',
    }

    if update_form.is_valid():
        updateinfo = update_form.cleaned_data['updateinfo']
        for lineitem in updateinfo.strip().split('\n'):
            fields = lineitem.strip('\n').split('\t')
            if i == 0:
                for k in range(len(fields)):
                    titleinfo[k] = fields[k].strip().lower()
                    colinfo[k] = []

            else:
                for k in range(len(fields)):
                    colinfo[k].append(fields[k])
            i = i+1
        keytitle = titleinfo[0]
        if keytitle == 'sequencing id':
            cores_tm = {}
            machines_tm = {}
            for k in range(len(titleinfo)-1):
                if titleinfo[k+1] in ['team member intials', 'team member initials']:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_seq = SeqInfo.objects.get(seq_id=item[0])
                        current_seq.team_member_initails = User.objects.get(
                            username=item[1].strip())
                        current_seq.save()
                elif titleinfo[k+1] in ['date submitted for sequencing', 'date']:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_seq = SeqInfo.objects.get(seq_id=item[0])
                        current_seq.date_submitted_for_sequencing = datetransform(
                            item[1].strip())
                        current_seq.save()
                elif titleinfo[k+1] == 'library id':
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_seq = SeqInfo.objects.get(seq_id=item[0])
                        current_seq.libraryinfo = LibraryInfo.objects.get(
                            library_id=item[1].strip())
                        current_seq.save()
                elif titleinfo[k+1] == 'portion of lane':
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_seq = SeqInfo.objects.get(seq_id=item[0])
                        current_seq.portion_of_lane = float(item[1].strip())
                        current_seq.save()
                elif titleinfo[k+1] in ['i7 index (if applicable)', 'i7 index']:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_seq = SeqInfo.objects.get(seq_id=item[0])
                        if item[1].strip():
                            current_seq.i7index = Barcode.objects.get(
                                indexid=item[1].strip())
                        else:
                            current_seq.i7index = None
                        current_seq.save()
                elif titleinfo[k+1] in ['i5 index (or single index)', 'i5 index']:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_seq = SeqInfo.objects.get(seq_id=item[0])
                        if item[1].strip():
                            current_seq.i5index = Barcode.objects.get(
                                indexid=item[1].strip())
                        else:
                            current_seq.i5index = None
                        current_seq.save()
                elif titleinfo[k+1] not in ['sequencing core', 'sequening core', 'machine']:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_seq = SeqInfo.objects.get(seq_id=item[0])
                        setattr(
                            current_seq, title2field_seq[titleinfo[k+1]], item[1].strip())
                        current_seq.save()
                else:
                    if titleinfo[k+1] in ['sequencing core', 'sequening core']:
                        cores_tm[colinfo[0]] = colinfo[k+1]
                    elif titleinfo[k+1] == 'machine':
                        machines_tm[colinfo[0]] = colinfo[k+1]
            for k in cores_tm.keys():
                current_seq = SeqInfo.objects.get(seq_id=k)
                current_seq.machine = SeqMachineInfo.objects.get(
                    sequencing_core=item[0], machine_name=item[1])
                current_seq.save()
        elif keytitle in ['library id (if library generated)', 'library id']:
            for k in range(len(titleinfo)-1):
                if titleinfo[k+1] in ['sample id (must match column i in sample sheet)', 'sample id']:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_lib = LibraryInfo.objects.get(
                            library_id=item[0])
                        current_lib.sampleinfo = SampleInfo.objects.get(
                            sample_id=item[1].strip())
                        current_lib.save()
                elif titleinfo[k+1] in ['team member intials', 'team member initials']:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_lib = LibraryInfo.objects.get(
                            library_id=item[0])
                        current_lib.team_member_initails = User.objects.get(
                            username=item[1].strip())
                        current_lib.save()
                elif titleinfo[k+1] == 'date experiment started':
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_lib = LibraryInfo.objects.get(
                            library_id=item[0])
                        current_lib.date_started = datetransform(
                            item[1].strip())
                        current_lib.save()
                elif titleinfo[k+1] == 'date experiment completed':
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_lib = LibraryInfo.objects.get(
                            library_id=item[0])
                        current_lib.date_completed = datetransform(
                            item[1].strip())
                        current_lib.save()
                else:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_lib = LibraryInfo.objects.get(
                            library_id=item[0])
                        setattr(
                            current_lib, title2field_lib[titleinfo[k+1]], item[1].strip())
                        current_lib.save()
        elif keytitle == 'sample id':
            for k in range(len(titleinfo)-1):
                if titleinfo[k+1] == 'date':
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_sam = SampleInfo.objects.get(sample_id=item[0])
                        current_sam.date = datetransform(item[1].strip())
                        current_sam.save()
                elif titleinfo[k+1] == 'date sample received':
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_sam = SampleInfo.objects.get(sample_id=item[0])
                        current_sam.date_received = datetransform(
                            item[1].strip())
                        current_sam.save()
                elif titleinfo[k+1] == 'initials of reciever':
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_sam = SampleInfo.objects.get(sample_id=item[0])
                        current_sam.team_member = User.objects.get(
                            username=item[1].strip())
                        current_sam.save()
                else:
                    for item in zip(colinfo[0], colinfo[k+1]):
                        current_sam = SampleInfo.objects.get(sample_id=item[0])
                        setattr(
                            current_sam, title2field_sam[titleinfo[k+1]], item[1].strip())
                        current_sam.save()
        return redirect('masterseq_app:index')

    context = {
        'update_form': update_form,
    }

    return render(request, 'masterseq_app/bulkupdate.html', context)


@transaction.atomic
def SamplesCreateView(request):
    """
    Steps in creating new samples:
    1). Will add the research person to database automatically if the person is new
    2). Will add the phone, email to the research person if they are new info to the research person
    3). Will add the fiscal person to database automatically if the person is new
    4). Will add the index, email to the fiscal person if they are new info to the fiscal person
    5). Will add the sample info
    """
    sample_form = SamplesCreationForm(request.POST or None)
    tosave_list = []
    data = {}

    # these 2 flags are used to decide whether show some segment in the pop up preview window
    newuserrequired = 0
    newinforequired = 0

    alreadynewuser = []
    if sample_form.is_valid():
        sampleinfo = sample_form.cleaned_data['samplesinfo']
        # assign SAMP- number for each sample
        all_index = list(SampleInfo.objects.values_list(
            'sample_index', flat=True))
        max_index = max([int(x.split('-')[1])
                         for x in all_index if x.startswith('SAMP-') and '&' not in x])
        for lineitem in sampleinfo.strip().split('\n'):
            lineitem = lineitem+'\t'*20
            fields = lineitem.strip('\n').split('\t')

            financial_unit = fields[8].strip() if fields[8].strip() not in ['NA', 'N/A'] else '' 
            project_n = fields[9].strip() if fields[8].strip() not in ['NA', 'N/A'] else ''
            task_n = fields[10].strip() if fields[9].strip() not in ['NA', 'N/A'] else ''
            funding_source_n = fields[11].strip() if fields[10].strip() not in ['NA', 'N/A'] else ''
            
            del fields[8:12]

            samindex = 'SAMP-'+str(max_index + 1)
            max_index = max_index + 1
            # these 2 flags are used to decide whether show some segment in the pop up preview window
            newresuserflag = 0
            newresinfoflag = 0

            user_first_name = ''
            user_last_name = ''
            user_username = '',
            user_email = '',
            user_phone = '',
            user_index = '',
            new_email = ''
            new_phone = ''
            new_index = ''

            # these 2 flags are used to decide whether show some segment in the pop up preview window
            newfisuserflag = 0
            newfisinfoflag = 0
            fisuser_first_name = ''
            fisuser_last_name = ''
            fisuser_username = '',
            fisuser_email = '',
            fisuser_phone = '',
            fisuser_index = '',
            fisnew_email = ''
            fisnew_phone = ''
            fisnew_index = ''
            gname = fields[1].strip() if fields[1].strip() not in [
                'NA', 'N/A'] else ''

            # step1,2: research person part
            resname = fields[2].strip() if fields[2].strip() not in [
                'NA', 'N/A'] else ''
            resemail = fields[3].strip().lower() if fields[3].strip() not in [
                'NA', 'N/A'] else ''
            resphone = re.sub(
                '-| |\.|\(|\)|ext', '', fields[4].strip()) if fields[4].strip() not in ['NA', 'N/A'] else ''
            print(f'{gname}, {resname}, {resemail}, {resphone}')            
            if resemail:
                thisgroup = Group.objects.get(name=gname)
                if thisgroup.collaboratorpersoninfo_set.all().filter(email__contains=[resemail]).exists():
                    resperson = thisgroup.collaboratorpersoninfo_set.all().get(
                        email__contains=[resemail])
                    resname = resperson.person_id.first_name+' '+resperson.person_id.last_name
                    user_first_name = resname.split(' ')[0]
                    user_last_name = resname.split(' ')[-1]
                    if resphone:
                        if not resperson.phone or resphone not in resperson.phone:
                            newinforequired = 1
                            newresinfoflag = 1
                            new_phone = resphone

                else:
                    user_first_name = resname.split(' ')[0]
                    user_last_name = resname.split(' ')[-1]
                    try:
                        resuser = User.objects.filter(groups__name__in=[gname]).get(
                            first_name=resname.split(' ')[0], last_name=resname.split(' ')[-1])
                        resperson, created = CollaboratorPersonInfo.objects.get_or_create(
                            person_id=resuser, group=thisgroup)
                        newinforequired = 1
                        newresinfoflag = 1
                        new_email = resemail
                        if resphone:
                            if not resperson.phone or resphone not in resperson.phone:
                                new_phone = resphone

                    except:
                        newuserrequired = 1
                        if user_first_name+' '+user_last_name not in alreadynewuser:
                            alreadynewuser.append(
                                user_first_name+' '+user_last_name)
                            newresuserflag = 1
                            user_username = user_first_name[0].lower(
                            )+user_last_name.lower()
                            if User.objects.filter(username=user_username).exists():
                                user_username = user_first_name[0]+str(
                                    randint(0, 9))+user_last_name.lower()

            elif resname:
                user_first_name = resname.split(' ')[0]
                user_last_name = resname.split(' ')[-1]
                try:
                    resuser = User.objects.filter(groups__name__in=[gname]).get(
                        first_name=resname.split(' ')[0], last_name=resname.split(' ')[-1])
                    resperson, created = CollaboratorPersonInfo.objects.get_or_create(
                        person_id=resuser, group=thisgroup)
                    newinforequired = 1
                    newresinfoflag = 1
                    new_email = ''
                    if resphone:
                        if not resperson.phone or resphone not in resperson.phone:
                            new_phone = resphone
                except:
                    newuserrequired = 1
                    if user_first_name+' '+user_last_name not in alreadynewuser:
                        alreadynewuser.append(
                            user_first_name+' '+user_last_name)
                        newresuserflag = 1
                        user_username = user_first_name[0].lower(
                        )+user_last_name.lower()
                        if User.objects.filter(username=user_username).exists():
                            user_username = user_first_name[0] + \
                                str(randint(0, 9))+user_last_name.lower()

            # step3,4: fiscal person part
            fisname = fields[5].strip() if fields[5].strip() not in [
                'NA', 'N/A'] else ''
            fisemail = fields[6].strip().lower() if fields[6].strip() not in [
                'NA', 'N/A'] else ''
            indname = fields[7].strip() if fields[7].strip() not in [
                'NA', 'N/A'] else ''
            if fisemail:
                thisgroup = Group.objects.get(name=gname)
                if thisgroup.collaboratorpersoninfo_set.all().filter(email__contains=[fisemail]).exists():
                    fisperson = thisgroup.collaboratorpersoninfo_set.all().get(
                        email__contains=[fisemail])
                    fisname = fisperson.person_id.first_name+' '+fisperson.person_id.last_name
                    fisuser_first_name = fisname.split(' ')[0]
                    fisuser_last_name = fisname.split(' ')[-1]
                    if indname:
                        if not fisperson.index or indname not in fisperson.index:
                            newinforequired = 1
                            newfisinfoflag = 1
                            fisnew_index = indname

                else:
                    fisuser_first_name = fisname.split(' ')[0]
                    fisuser_last_name = fisname.split(' ')[-1]
                    try:
                        fisuser = User.objects.filter(groups__name__in=[gname]).get(
                            first_name=fisname.split(' ')[0], last_name=fisname.split(' ')[-1])
                        fisperson, created = CollaboratorPersonInfo.objects.get_or_create(
                            person_id=fisuser, group=thisgroup)
                        newinforequired = 1
                        newfisinfoflag = 1
                        fisnew_email = fisemail
                        if indname:
                            if not fisperson.index or indname not in fisperson.index:
                                fisnew_index = indname

                    except:
                        newuserrequired = 1
                        if fisuser_first_name+' '+fisuser_last_name not in alreadynewuser:
                            alreadynewuser.append(
                                fisuser_first_name+' '+fisuser_last_name)
                            newfisuserflag = 1
                            fisuser_username = fisuser_first_name[0].lower(
                            )+fisuser_last_name.lower()
                            if User.objects.filter(username=fisuser_username).exists():
                                fisuser_username = fisuser_first_name[0]+str(
                                    randint(0, 9))+fisuser_last_name.lower()

            elif fisname:
                fisuser_first_name = fisname.split(' ')[0]
                fisuser_last_name = fisname.split(' ')[-1]
                try:
                    fisuser = User.objects.filter(groups__name__in=[gname]).get(
                        first_name=fisname.split(' ')[0], last_name=fisname.split(' ')[-1])
                    fisperson, created = CollaboratorPersonInfo.objects.get_or_create(
                        person_id=fisuser, group=thisgroup)
                    newinforequired = 1
                    newfisinfoflag = 1
                    fisnew_email = ''
                    if indname:
                        if not fisperson.index or indname not in fisperson.index:
                            fisnew_index = indname
                except:
                    newuserrequired = 1
                    if fisuser_first_name+' '+fisuser_last_name not in alreadynewuser:
                        alreadynewuser.append(
                            fisuser_first_name+' '+fisuser_last_name)
                        newfisuserflag = 1
                        fisuser_username = fisuser_first_name[0].lower(
                        )+fisuser_last_name.lower()
                        if User.objects.filter(username=fisuser_username).exists():
                            fisuser_username = fisuser_first_name[0]+str(
                                randint(0, 9))+fisuser_last_name.lower()

            # step5, other fields of samples
            samnotes = fields[20].strip()
            try:
                saminternalnotes = fields[24].strip()
            except:
                saminternalnotes = ''
            try:
                membername = fields[22].strip()
                if membername == '':
                    membername = request.user.username
            except:
                membername = request.user.username
            try:
                storage_tm = fields[23].strip()
            except:
                storage_tm = ''
            service_requested_tm = fields[16].strip()
            seq_depth_to_target_tm = fields[17].strip()
            seq_length_requested_tm = fields[18].strip()
            seq_type_requested_tm = fields[19].strip()
            samprep = fields[12].strip().lower().replace(
                'crypreserant', 'cryopreservant')
            if samprep not in [x[0].split('(')[0].strip() for x in choice_for_preparation]:
                if samprep.lower().startswith('other'):
                    samprep = 'other (please explain in notes)'
                else:
                    if samprep:
                        samnotes = ';'.join(
                            [samnotes, 'sample preparation:'+samprep]).strip(';')
                    samprep = 'other (please explain in notes)'
            samtype = fields[11].split('(')[0].strip().lower()
            samspecies = fields[10].split('(')[0].lower().strip()
            unit = fields[15].split('(')[0].strip().lower()
            fixation = fields[13].strip().lower()
            if fixation == 'yes (1% fa)':
                fixation = 'Yes (1% FA)'
            elif fixation == 'no':
                fixation = 'No'
            if service_requested_tm.lower().startswith('other'):
                service_requested_tm = 'other (please explain in notes)'
            sample_amount = fields[14].strip()
            samdescript = fields[9].strip()
            samid = fields[8].strip()
            samdate = datetransform(fields[0].strip())
            try:
                date_received = datetransform(fields[21].strip())
            except:
                date_received = None
            data[samid] = {}
            data[samid] = {
                'sample_index': samindex,
                'group': gname,
                'research_name': resname,
                'research_email': resemail,
                'research_phone': resphone,
                'user_index': '',
                'fiscal_name': fisname,
                'fiscal_email': fisemail,
                'fiscal_phone': '',
                'fiscal_index': indname,
                'team_member': membername,
                'date': samdate,
                'date_received': date_received,
                'species': samspecies,
                'sample_type': samtype,
                'preparation': samprep,
                'fixation': fixation,
                'sample_amount': sample_amount,
                'unit': unit,
                'description': samdescript,
                'storage': storage_tm,
                'notes': samnotes,
                'internal_notes': saminternalnotes,
                'service_requested': service_requested_tm,
                'seq_depth_to_target': seq_depth_to_target_tm,
                'seq_length_requested': seq_length_requested_tm,
                'seq_type_requested': seq_type_requested_tm,
                'newresuserflag': newresuserflag,
                'newresinfoflag': newresinfoflag,
                'newfisuserflag': newfisuserflag,
                'newfisinfoflag': newfisinfoflag,
                'user_first_name': user_first_name,
                'user_last_name': user_last_name,
                'user_username': user_username,
                'user_email': resemail,
                'user_phone': resphone,
                'user_index': '',
                'new_email': new_email,
                'new_phone': new_phone,
                'new_index': new_index,
                'fisuser_first_name': fisuser_first_name,
                'fisuser_last_name': fisuser_last_name,
                'fisuser_username': fisuser_username,
                'fisuser_email': fisemail,
                'fisuser_phone': '',
                'fisuser_index': indname,
                'fisnew_email': fisnew_email,
                'fisnew_phone': fisnew_phone,
                'fisnew_index': fisnew_index,
                'financial_unit': financial_unit,
                'project_number':project_n,
                'task_number':task_n,
                'funding_source_number':funding_source_n,
            }
        # to save the new samples
        if 'Save' in request.POST:
            for k, v in data.items():
                if v['group']:
                    group_tm = Group.objects.get(name=v['group'])
                else:
                    group_tm = None
                if v['newresuserflag'] == 1:
                    alphabet = string.ascii_letters + string.digits
                    passwordrand = ''.join(secrets.choice(alphabet)
                                           for i in range(10))
                    resaccount = User.objects.create_user(
                        username=v['user_username'],
                        first_name=v['user_first_name'],
                        last_name=v['user_last_name'],
                        password=passwordrand,
                    )
                    group_tm.user_set.add(resaccount)
                    resperson = CollaboratorPersonInfo.objects.create(
                        person_id=resaccount,
                        group=group_tm,
                        email=removenone([v['research_email']]),
                        phone=removenone([v['research_phone']]),
                    )
                if v['newfisuserflag'] == 1:
                    alphabet = string.ascii_letters + string.digits
                    passwordrand = ''.join(secrets.choice(alphabet)
                                           for i in range(10))
                    fisaccount = User.objects.create_user(
                        username=v['fisuser_username'],
                        first_name=v['fisuser_first_name'],
                        last_name=v['fisuser_last_name'],
                        password=passwordrand,
                    )
                    group_tm.user_set.add(fisaccount)
                    fisperson = CollaboratorPersonInfo.objects.create(
                        person_id=fisaccount,
                        group=group_tm,
                        email=removenone([v['fiscal_email']]),
                        index=removenone([v['fiscal_index']]),
                    )
                if v['newresinfoflag'] == 1:
                    resuser = User.objects.filter(groups__name__in=[v['group']]).\
                        get(first_name=v['research_name'].split(' ')[
                            0], last_name=v['research_name'].split(' ')[1])
                    resperson = CollaboratorPersonInfo.objects.get(
                        person_id=resuser, group=group_tm)
                    if v['new_email']:
                        current_email = nonetolist(resperson.email)
                        current_email.insert(0, v['new_email'])
                        resperson.email = removenone(current_email)
                    if v['new_phone']:
                        current_phone = nonetolist(resperson.phone)
                        current_phone.insert(0, v['new_phone'])
                        resperson.phone = removenone(current_phone)
                    resperson.save()

                if v['newfisinfoflag'] == 1:
                    fisuser = User.objects.filter(groups__name__in=[v['group']]).\
                        get(first_name=v['fiscal_name'].split(' ')[
                            0], last_name=v['fiscal_name'].split(' ')[1])
                    fisperson = CollaboratorPersonInfo.objects.get(person_id=fisuser, group=group_tm
                                                                   )

                    if v['fisnew_email']:
                        current_email = nonetolist(fisperson.email)
                        current_email.insert(0, v['fisnew_email'])
                        fisperson.email = removenone(current_email)
                    if v['fisnew_index']:
                        current_index = nonetolist(fisperson.index)
                        current_index.insert(0, v['fisnew_index'])
                        fisperson.index = removenone(current_index)
                    fisperson.save()

                tosave_item = SampleInfo(
                    sample_index=v['sample_index'],
                    group=group_tm,
                    research_name=v['research_name'],
                    research_email=v['research_email'],
                    research_phone=v['research_phone'],
                    fiscal_name=v['fiscal_name'],
                    fiscal_email=v['fiscal_email'],
                    fiscal_index=v['fiscal_index'],
                    financial_unit=v['financial_unit'],
                    project_number = v['project_number'],
                    task_number = v['task_number'],
                    funding_source_number=v['funding_source_number'], 
                    sample_id=k,
                    species=v['species'],
                    sample_type=v['sample_type'],
                    preparation=v['preparation'],
                    description=v['description'],
                    unit=v['unit'],
                    sample_amount=v['sample_amount'],
                    fixation=v['fixation'],
                    notes=v['notes'],
                    internal_notes=v['internal_notes'],
                    team_member=User.objects.get(username=v['team_member']),
                    date=v['date'],
                    date_received=v['date_received'],
                    storage=v['storage'],
                    service_requested=v['service_requested'],
                    seq_depth_to_target=v['seq_depth_to_target'],
                    seq_length_requested=v['seq_length_requested'],
                    seq_type_requested=v['seq_type_requested'],
                )
                tosave_list.append(tosave_item)
            SampleInfo.objects.bulk_create(tosave_list)
            return redirect('masterseq_app:index')
        # to show the to be added info in a pop-up preview window before saving
        if 'Preview' in request.POST:
            displayorder = ['sample_index', 'group', 'research_name', 'research_email',
                            'research_phone', 'fiscal_name', 'fiscal_email', 'fiscal_index','financial_unit','project_number',\
                            'task_number','funding_source_number', 'description',
                            'date', 'species', 'sample_type',
                            'preparation', 'fixation', 'sample_amount', 'unit',
                            'notes', 'service_requested', 'seq_depth_to_target',
                            'seq_length_requested', 'seq_type_requested', 'date_received', 'team_member', 'storage', 'internal_notes']
            displayorder2 = ['user_username', 'user_first_name', 'user_last_name',
                             'user_email', 'user_phone', 'user_index']
            displayorder3 = ['fisuser_username', 'fisuser_first_name', 'fisuser_last_name',
                             'fisuser_email', 'fisuser_phone', 'fisuser_index']
            displayorder4 = ['group', 'user_first_name',
                             'user_last_name', 'new_email', 'new_phone', 'new_index']
            displayorder5 = ['group', 'fisuser_first_name', 'fisuser_last_name',
                             'fisnew_email', 'fisnew_phone', 'fisnew_index']



            context = {
                'newuserrequired': newuserrequired,
                'newinforequired': newinforequired,
                'sample_form': sample_form,
                'modalshowplus': 1,
                'displayorder': displayorder,
                'displayorder2': displayorder2,
                'displayorder3': displayorder3,
                'displayorder4': displayorder4,
                'displayorder5': displayorder5,
                'data': data,
            }

            return render(request, 'masterseq_app/samplesadd.html', context)
    context = {
        'sample_form': sample_form,
    }

    return render(request, 'masterseq_app/samplesadd.html', context)


@transaction.atomic
def LibrariesCreateView(request):
    """
    The view to add new libraries. 
    It will link the library to the sample through the sample id column in the template.
    For the user not in the bioinformatics group, the sample should be already in the database
    first. When user is in bioinformatics group, allow the sample be new, and it will add the
    pseudo sample (detected by SAMPNA-) along with the library to the database automatically. 
    The pseudo part is typically if the user wants to add the public data and get it through own
    pipeline
    """
    if request.user.groups.filter(name='bioinformatics').exists():
        library_form = LibsCreationForm(request.POST or None)
    else:
        library_form = LibsCreationForm_wetlab(request.POST or None)
    tosave_list = []
    data = {}
    pseudorequired = 0
    if library_form.is_valid():
        libsinfo = library_form.cleaned_data['libsinfo']
        sampid = {}
        samp_indexes = list(SampleInfo.objects.values_list(
            'sample_index', flat=True))
        existingmaxindex = max([int(x.split('-')[1])
                                for x in samp_indexes if x.startswith('SAMPNA')])

        exp_indexes = list(LibraryInfo.objects.values_list(
            'experiment_index', flat=True))
        existingexpmaxindex = max([int(x.split('-')[1])
                                   for x in exp_indexes if x.startswith('EXP-')])

        for lineitem in libsinfo.strip().split('\n'):
            lineitem = lineitem+'\t'*10
            fields = lineitem.strip('\n').split('\t')
            libid = fields[8].strip()
            sampid = fields[0].strip()
            if not SampleInfo.objects.filter(sample_id=sampid).exists():
                pseudorequired = 1
                pseudoflag = 1
                sampindex = 'SAMPNA-'+str(existingmaxindex+1)
                existingmaxindex += 1
                if sampid.strip().lower() in ['', 'na', 'other', 'n/a']:
                    sampid = sampindex

            else:
                pseudoflag = 0
                samtm = SampleInfo.objects.get(sample_id=sampid)
                sampindex = samtm.sample_index
            expindex = 'EXP-'+str(existingexpmaxindex+1)
            existingexpmaxindex = existingexpmaxindex+1
            data[libid] = {}
            datestart = datetransform(fields[3].strip())
            dateend = datetransform(fields[4].strip())
            libexp = fields[5].strip()
            refnotebook = fields[7].strip()
            libnote = fields[9].strip()
            data[libid] = {
                'pseudoflag': pseudoflag,
                'sampleinfo': sampid,
                'sample_index': sampindex,
                'sample_id': sampid,
                'lib_description': fields[1].strip(),
                'team_member_initails': fields[2].strip(),
                'experiment_index': expindex,
                'date_started': datestart,
                'date_completed': dateend,
                'experiment_type': libexp,
                'protocal_name': fields[6].strip(),
                'reference_to_notebook_and_page_number': fields[7].strip(),
                'notes': libnote
            }

        if 'Save' in request.POST:
            for k, v in data.items():
                if v['pseudoflag'] == 1:
                    SampleInfo.objects.create(
                        sample_id=v['sample_id'],
                        sample_index=v['sample_index'],
                        team_member=User.objects.get(
                            username=v['team_member_initails']),
                    )
                tosave_item = LibraryInfo(
                    library_id=k,
                    library_description=v['lib_description'],
                    sampleinfo=SampleInfo.objects.get(
                        sample_id=v['sampleinfo']),
                    experiment_index=v['experiment_index'],
                    experiment_type=v['experiment_type'],
                    protocal_used=v['protocal_name'],
                    reference_to_notebook_and_page_number=v['reference_to_notebook_and_page_number'],
                    date_started=v['date_started'],
                    date_completed=v['date_completed'],
                    team_member_initails=User.objects.get(
                        username=v['team_member_initails']),
                    notes=v['notes']
                )
                tosave_list.append(tosave_item)
            LibraryInfo.objects.bulk_create(tosave_list)
            return redirect('masterseq_app:index')
        if 'Preview' in request.POST:
            displayorder = ['sampleinfo', 'lib_description', 'team_member_initails', 'experiment_index', 'date_started',
                            'date_completed', 'experiment_type', 'protocal_name', 'reference_to_notebook_and_page_number',
                            'notes']
            if pseudorequired == 1:
                displayorder2 = ['sample_index',
                                 'sample_id', 'team_member_initails']
                context = {
                    'library_form': library_form,
                    'modalshowplus': 1,
                    'displayorder': displayorder,
                    'displayorder2': displayorder2,
                    'data': data,
                }

                return render(request, 'masterseq_app/libsadd.html', context)

            else:
                context = {
                    'library_form': library_form,
                    'modalshow': 1,
                    'displayorder': displayorder,
                    'data': data,
                }

                return render(request, 'masterseq_app/libsadd.html', context)

        if 'PreviewfromWarning' in request.POST:
            displayorder = ['sampleinfo', 'lib_description', 'team_member_initails', 'experiment_index', 'date_started',
                            'date_completed', 'experiment_type', 'protocal_name', 'reference_to_notebook_and_page_number',
                            'notes']
            displayorder2 = ['sample_index',
                             'sample_id', 'team_member_initails']
            context = {
                'library_form': library_form,
                'modalshowplusfromwarning': 1,
                'displayorder': displayorder,
                'displayorder2': displayorder2,
                'data': data,
            }

            return render(request, 'masterseq_app/libsadd.html', context)

        if 'Warning' in request.POST:
            displayorder3 = ['sample_id']
            context = {
                'library_form': library_form,
                'warningmodalshow': 1,
                'displayorder3': displayorder3,
                'data': data,
            }

            return render(request, 'masterseq_app/libsadd.html', context)

    context = {
        'library_form': library_form,
    }

    return render(request, 'masterseq_app/libsadd.html', context)


@transaction.atomic
def SeqsCreateView(request):
    """
    The view to add new seqs. 
    Same as the LibrariesCreateView, it allows the bioinformatics user to create a 
    pseudo sample or pseudo library.
    """
    if request.user.groups.filter(name='bioinformatics').exists():
        seqs_form = SeqsCreationForm(request.POST or None)
    else:
        seqs_form = SeqsCreationForm_wetlab(request.POST or None)
    tosave_list = []
    data = {}
    updatesamprequired = 0
    pseudosamprequired = 0
    pseudolibrequired = 0
    if seqs_form.is_valid():
        seqsinfo = seqs_form.cleaned_data['seqsinfo']
        samp_indexes = list(SampleInfo.objects.values_list(
            'sample_index', flat=True))

        existingmaxsampindex = max([int(x.split('-')[1])
                                    for x in samp_indexes if x.startswith('SAMPNA')])

        lib_indexes = list(LibraryInfo.objects.values_list(
            'experiment_index', flat=True))

        existingmaxlibindex = max([int(x.split('-')[1])
                                   for x in lib_indexes if x.startswith('EXPNA')])

        for lineitem in seqsinfo.strip().split('\n'):
            lineitem = lineitem+'\t'*20
            fields = lineitem.split('\t')
            updatesampflag = 0
            pseudolibflag = 0
            pseudosamflag = 0
            #samindex = fields[0].strip()
            sampid = fields[0].strip()
            sampspecies = fields[2].strip().lower()
            seqid = fields[6].strip()
            #expindex = fields[4].strip()
            libraryid = fields[5].strip()
            exptype = fields[7].strip()
            data[seqid] = {}
            if not LibraryInfo.objects.filter(library_id=libraryid).exists():
                pseudolibrequired = 1
                pseudolibflag = 1
                expindex = 'EXPNA-'+str(existingmaxlibindex+1)
                existingmaxlibindex += 1
                if not SampleInfo.objects.filter(sample_id=sampid).exists():
                    pseudosamprequired = 1
                    pseudosamflag = 1
                    sampindex = 'SAMPNA-'+str(existingmaxsampindex+1)
                    existingmaxsampindex += 1
                    if sampid.strip().lower() in ['', 'na', 'other', 'n/a']:
                        sampid = sampindex
                else:
                    sampinfo = SampleInfo.objects.get(sample_id=sampid)
                    sampindex = sampinfo.sample_index
                    if not sampinfo.species and sampspecies:
                        updatesampflag = 1
                        updatesamprequired = 1
            else:
                libinfo = LibraryInfo.objects.select_related(
                    'sampleinfo').get(library_id=libraryid)
                sampinfo = libinfo.sampleinfo
                sampindex = sampinfo.sample_index
                sampid = sampinfo.sample_id
                expindex = libinfo.experiment_index

                if not sampinfo.species and sampspecies:
                    updatesampflag = 1
                    updatesamprequired = 1

            if '-' in fields[4].strip():
                datesub = fields[4].strip()
            else:
                datesub = datetransform(fields[4].strip())
            memebername = User.objects.get(username=fields[3].strip())
            indexname = fields[13].strip()
            if indexname and indexname not in ['NA', 'Other (please explain in notes)', 'N/A']:
                i7index = Barcode.objects.get(indexid=indexname)
            else:
                i7index = None
            indexname2 = fields[14].strip()
            if indexname2 and indexname2 not in ['NA', 'Other (please explain in notes)', 'N/A']:
                i5index = Barcode.objects.get(indexid=indexname2)
            else:
                i5index = None
            polane = fields[12].strip()
            if polane and polane not in ['NA', 'Other (please explain in notes)', 'N/A']:
                polane = float(polane)
            else:
                polane = None
            seqid = fields[6].strip()
            seqcore = fields[8].split('(')[0].strip()
            seqmachine = fields[9].split('(')[0].strip()
            machineused = SeqMachineInfo.objects.get(
                sequencing_core=seqcore, machine_name=seqmachine)
            data[seqid] = {
                'updatesampflag': updatesampflag,
                'pseudolibflag': pseudolibflag,
                'pseudosamflag': pseudosamflag,
                'sample_index': sampindex,
                'sampleinfo': sampid,
                'sample_id': sampid,
                'species': sampspecies,
                'experiment_index': expindex,
                'experiment_type': exptype,
                'libraryinfo': fields[5].strip(),
                'library_id': libraryid,
                'default_label': fields[1].strip(),
                'team_member_initails': fields[3].strip(),
                'read_length': fields[10].strip(),
                'read_type': fields[11].strip(),
                'portion_of_lane': polane,
                'seqcore': fields[8].split('(')[0].strip(),
                'machine': seqmachine,
                'i7index': indexname,
                'i5index': indexname2,
                'indexname': indexname,
                'indexname2': indexname2,
                'date_submitted': datesub,
                'notes': fields[15].strip(),
            }
        if 'Save' in request.POST:

            for k, v in data.items():
                if v['pseudolibflag'] == 1:
                    if v['pseudosamflag'] == 1:
                        SampleInfo.objects.create(
                            sample_id=v['sample_id'],
                            sample_index=v['sample_index'],
                            species=v['species'],
                            team_member=User.objects.get(
                                username=v['team_member_initails']),
                        )

                    LibraryInfo.objects.create(
                        library_id=v['library_id'],
                        experiment_index=v['experiment_index'],
                        experiment_type=v['experiment_type'],
                        sampleinfo=SampleInfo.objects.get(
                            sample_index=v['sample_index']),
                        team_member_initails=User.objects.get(
                            username=v['team_member_initails']),
                    )
                if v['updatesampflag'] == 1:
                    sampleinfo = SampleInfo.objects.get(
                        sample_index=v['sample_index'])
                    sampleinfo.species = v['species']
                    sampleinfo.save()
                if v['indexname'] and v['indexname'] not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    i7index = Barcode.objects.get(indexid=v['indexname'])
                else:
                    i7index = None
                if v['indexname2'] and v['indexname2'] not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    i5index = Barcode.objects.get(indexid=v['indexname2'])
                else:
                    i5index = None
                tosave_item = SeqInfo(
                    seq_id=k,
                    libraryinfo=LibraryInfo.objects.get(
                        library_id=v['library_id']),
                    team_member_initails=User.objects.get(
                        username=v['team_member_initails']),
                    read_length=v['read_length'],
                    read_type=v['read_type'],
                    portion_of_lane=v['portion_of_lane'],
                    notes=v['notes'],
                    machine=SeqMachineInfo.objects.get(
                        sequencing_core=v['seqcore'], machine_name=v['machine']),
                    i7index=i7index,
                    i5index=i5index,
                    default_label=v['default_label'],
                    date_submitted_for_sequencing=v['date_submitted'],
                )
                tosave_item.save()
                tosave_list.append(tosave_item)

            # SeqInfo.objects.bulk_create(tosave_list)           

            return redirect('masterseq_app:index')
        if 'Preview' in request.POST:
            displayorder = ['libraryinfo', 'default_label', 'date_submitted', 'team_member_initails', 'read_length',
                            'read_type', 'portion_of_lane', 'seqcore', 'machine', 'i7index', 'i5index', 'notes']
            displayorder2 = ['sample_index', 'sample_id',
                             'species', 'team_member_initails']
            displayorder3 = ['library_id', 'sampleinfo',
                             'experiment_index', 'experiment_type', 'team_member_initails']
            context = {
                'updatesamprequired': updatesamprequired,
                'pseudosamprequired': pseudosamprequired,
                'pseudolibrequired': pseudolibrequired,
                'seqs_form': seqs_form,
                'modalshowplus': 1,
                'displayorder': displayorder,
                'displayorder2': displayorder2,
                'displayorder3': displayorder3,
                'data': data,
            }

            return render(request, 'masterseq_app/seqsadd.html', context)
        if 'PreviewfromWarning' in request.POST:
            displayorder = ['libraryinfo', 'default_label', 'date_submitted', 'team_member_initails', 'read_length',
                            'read_type', 'portion_of_lane', 'seqcore', 'machine', 'i7index', 'i5index', 'notes']
            displayorder2 = ['sample_index', 'sample_id',
                             'species', 'team_member_initails']
            displayorder3 = ['library_id', 'sampleinfo',
                             'experiment_index', 'experiment_type', 'team_member_initails']
            context = {
                'updatesamprequired': updatesamprequired,
                'pseudosamprequired': pseudosamprequired,
                'pseudolibrequired': pseudolibrequired,
                'seqs_form': seqs_form,
                'modalshowplusfromwarning': 1,
                'displayorder': displayorder,
                'displayorder2': displayorder2,
                'displayorder3': displayorder3,
                'data': data,
            }

            return render(request, 'masterseq_app/seqsadd.html', context)

        if 'Warning' in request.POST:
            displayorder4 = ['library_id']
            displayorder5 = ['sample_id']
            context = {
                'pseudosamprequired': pseudosamprequired,
                'seqs_form': seqs_form,
                'warningmodalshow': 1,
                'displayorder4': displayorder4,
                'displayorder5': displayorder5,
                'data': data,
            }

            return render(request, 'masterseq_app/seqsadd.html', context)

    context = {
        'seqs_form': seqs_form,
    }

    return render(request, 'masterseq_app/seqsadd.html', context)


def SampleDataView(request):
    """ called in ajax way, see epigen.js file:
    $('#metadata_samples_bio').DataTable({})
    """
    Samples_list = SampleInfo.objects.all().select_related('group').values(
        'pk', 'sample_id', 'description', 'date', 'sample_type', 'group__name', 'status')
    for sample in Samples_list:
        try:
            sample['group__name'] = sample['group__name'].replace(
                '_group', '').replace('_', ' ')
        except:
            pass
    data = list(Samples_list)

    return JsonResponse(data, safe=False)


def LibDataView(request):
    """ called in ajax way, see epigen.js file:
    $('#metadata_libs').DataTable({})
    """
    Libs_list = LibraryInfo.objects.all().select_related('sampleinfo__group').values(
        'pk', 'library_id', 'library_description', 'sampleinfo__id', 'sampleinfo__sample_type', 'sampleinfo__sample_id', 'sampleinfo__description',
        'sampleinfo__species', 'sampleinfo__group__name', 'date_started', 'experiment_type')
    data = list(Libs_list)

    return JsonResponse(data, safe=False)


def SeqDataView(request):
    """ called in ajax way, see epigen.js file:
    $('#metadata_seqs').DataTable({})
    """
    Seqs_list = SeqInfo.objects.all().select_related('libraryinfo__sampleinfo__group').values(
        'pk', 'seq_id', 'libraryinfo__library_description', 'libraryinfo__sampleinfo__id', 'libraryinfo__sampleinfo__sample_id',
        'libraryinfo__sampleinfo__description', 'libraryinfo__sampleinfo__group__name',
        'date_submitted_for_sequencing', 'machine__sequencing_core',
        'machine__machine_name', 'portion_of_lane', 'read_length', 'read_type')
    data = list(Seqs_list)

    return JsonResponse(data, safe=False)


def UserSampleDataView(request):
    """ called in ajax way, see epigen.js file:
    $('#metadata_samples_bio').DataTable({})
    """
    Samples_list = SampleInfo.objects.filter(team_member=request.user).values(
        'pk', 'sample_id', 'description', 'date', 'sample_type', 'group__name', 'status')
    for sample in Samples_list:
        try:
            sample['group__name'] = sample['group__name'].replace(
                '_group', '').replace('_', ' ')
        except:
            pass
    data = list(Samples_list)

    return JsonResponse(data, safe=False)


def UserLibDataView(request):
    """ called in ajax way, see epigen.js file:
    $('#metadata_libs_bio').DataTable({})
    """
    Libs_list = LibraryInfo.objects.filter(team_member_initails=request.user)\
        .select_related('sampleinfo__group').values(
            'pk', 'library_description', 'library_id', 'sampleinfo__id',  'sampleinfo__sample_type', 'sampleinfo__sample_id', 'sampleinfo__description',
        'sampleinfo__species', 'sampleinfo__group__name', 'date_started', 'experiment_type')
    data = list(Libs_list)

    return JsonResponse(data, safe=False)


def UserSeqDataView(request):
    """ called in ajax way, see epigen.js file:
    $('#metadata_seqs_bio').DataTable({})
    """
    Seqs_list = SeqInfo.objects.filter(team_member_initails=request.user)\
        .select_related('libraryinfo__sampleinfo__group', 'machine').values(
        'pk', 'seq_id', 'libraryinfo__library_description', 'libraryinfo__sampleinfo__id', 'libraryinfo__sampleinfo__sample_id',
        'libraryinfo__sampleinfo__description', 'libraryinfo__sampleinfo__group__name',
        'date_submitted_for_sequencing', 'machine__sequencing_core',
        'machine__machine_name', 'portion_of_lane', 'read_length', 'read_type')
    data = list(Seqs_list)

    return JsonResponse(data, safe=False)


def IndexView(request):
    if not request.user.groups.filter(name='bioinformatics').exists():
        return render(request, 'masterseq_app/metadata.html')
    else:
        return render(request, 'masterseq_app/metadata_bio.html')


def UserMetaDataView(request):
    if not request.user.groups.filter(name='bioinformatics').exists():
        return render(request, 'masterseq_app/metadata.html')
    else:
        return render(request, 'masterseq_app/metadata_bio.html')


def SampleDeleteView(request, pk):
    """ View to delete a sample, only allow bioinformatics user or the owner to delete the sample
    """
    sampleinfo = get_object_or_404(SampleInfo, pk=pk)
    if sampleinfo.team_member != request.user and not request.user.groups.filter(name='bioinformatics').exists():
        raise PermissionDenied
    sampleinfo.delete()
    return redirect('masterseq_app:user_metadata')


def LibDeleteView(request, pk):
    """ View to delete a library, only allow bioinformatics user or the owner to delete the library
    """
    libinfo = get_object_or_404(LibraryInfo, pk=pk)
    if libinfo.team_member_initails != request.user and not request.user.groups.filter(name='bioinformatics').exists():
        raise PermissionDenied
    libinfo.delete()
    return redirect('masterseq_app:user_metadata')


def SeqDeleteView(request, pk):
    """ View to delete a sequencing, only allow bioinformatics user or the owner to delete the sequencing
    """
    seqinfo = get_object_or_404(SeqInfo, pk=pk)
    if seqinfo.team_member_initails != request.user and not request.user.groups.filter(name='bioinformatics').exists():
        raise PermissionDenied
    seqinfo.delete()
    return redirect('masterseq_app:user_metadata')


@transaction.atomic
def SampleUpdateView(request, pk):
    sampleinfo = get_object_or_404(SampleInfo, pk=pk)
    orig_team_member = sampleinfo.team_member
    if sampleinfo.team_member != request.user and not request.user.groups.filter(name='bioinformatics').exists():
        raise PermissionDenied
    sample_form = SampleCreationForm(request.POST or None, instance=sampleinfo)
    if sample_form.is_valid():
        sampleinfo = sample_form.save(commit=False)
        sampleinfo.team_member = orig_team_member
        sampleinfo.save()
        return redirect('masterseq_app:user_metadata')
    context = {
        'sample_form': sample_form,
        'sampleinfo': sampleinfo,
    }

    return render(request, 'masterseq_app/sampleupdate.html', context)


@transaction.atomic
def LibUpdateView(request, pk):
    libinfo = get_object_or_404(LibraryInfo, pk=pk)
    if libinfo.team_member_initails != request.user and not request.user.groups.filter(name='bioinformatics').exists():
        raise PermissionDenied

    if request.method == 'POST':
        post = request.POST.copy()
        obj = get_object_or_404(
            SampleInfo, sample_index=post['sampleinfo'].split(':')[0])
        post['sampleinfo'] = obj.id
        library_form = LibraryCreationForm(post, instance=libinfo)
        if library_form.is_valid():
            libinfo = library_form.save(commit=False)
            libinfo.team_member_initails = request.user
            libinfo.save()
            return redirect('masterseq_app:user_metadata')
    else:
        library_form = LibraryCreationForm(instance=libinfo)

    context = {
        'library_form': library_form,
        'libinfo': libinfo,
    }

    return render(request, 'masterseq_app/libraryupdate.html', context)


@transaction.atomic
def SeqUpdateView(request, pk):
    seqinfo = get_object_or_404(SeqInfo, pk=pk)
    if seqinfo.team_member_initails != request.user and not request.user.groups.filter(name='bioinformatics').exists():
        raise PermissionDenied

    if request.method == 'POST':
        post = request.POST.copy()
        obj = get_object_or_404(LibraryInfo, library_id=post['libraryinfo'])
        post['libraryinfo'] = obj.id
        seq_form = SeqCreationForm(post, instance=seqinfo)
        if seq_form.is_valid():
            seqinfo = seq_form.save(commit=False)
            seqinfo.team_member_initails = request.user
            seqinfo.save()
            # update es index, dispatch signal
            return redirect('masterseq_app:user_metadata')
    else:
        seq_form = SeqCreationForm(instance=seqinfo)

    context = {
        'seq_form': seq_form,
        'seqinfo': seqinfo,
    }

    return render(request, 'masterseq_app/sequpdate.html', context)


def SampleDetailView(request, pk):
    sampleinfo = get_object_or_404(SampleInfo.objects.select_related(
        'team_member', 'research_person__person_id', 'fiscal_person__person_id'), pk=pk)
    summaryfield = ['status', 'sample_index', 'sample_id', 'description', 'date', 'species',
                    'sample_type', 'preparation', 'fixation', 'sample_amount', 'unit', 'notes', 'date_received', 'team_member', 'storage', 'internal_notes']
    requestedfield = ['date', 'service_requested', 'seq_depth_to_target',
                      'seq_length_requested', 'seq_type_requested']
    libfield = ['library_id', 'experiment_type',
                'protocalinfo', 'reference_to_notebook_and_page_number']
    seqfield = ['seq_id', 'default_label', 'machine',
                'read_length', 'read_type', 'total_reads']
    libinfo = sampleinfo.libraryinfo_set.all().select_related('protocalinfo')
    seqs = SeqInfo.objects.none()
    try:
        researchperson = CollaboratorPersonInfo.objects.get(
            email__contains=[sampleinfo.research_email])
        researchperson_name = researchperson.person_id.first_name + \
            ' '+researchperson.person_id.last_name
    except:
        researchperson_name = ''
    try:
        fiscalperson = CollaboratorPersonInfo.objects.get(
            email__contains=[sampleinfo.fiscal_email])
        fiscalperson_name = fiscalperson.person_id.first_name + \
            ' '+fiscalperson.person_id.last_name
    except:
        fiscalperson_name = ''
    for lib in libinfo:
        seqinfo = lib.seqinfo_set.all().select_related('machine')
        seqs = seqs | seqinfo
    groupinfo = sampleinfo.group
    piname = []

    if groupinfo:
        for user in groupinfo.user_set.all():
            for person in user.collaboratorpersoninfo_set.all():
                if 'PI' in person.role:
                    piname.append(user.first_name + ' ' + user.last_name)

    context = {
        'groupinfo': groupinfo,
        'piname': ';'.join(piname),
        'researchperson_name': researchperson_name,
        'fiscalperson_name': fiscalperson_name,
        'summaryfield': summaryfield,
        'requestedfield': requestedfield,
        'sampleinfo': sampleinfo,
        'libfield': libfield,
        'seqfield': seqfield,
        'libinfo': libinfo.order_by('library_id'),
        'seqs': seqs.order_by('seq_id'),
    }
    return render(request, 'masterseq_app/sampledetail.html', context=context)


def LibDetailView(request, pk):
    libinfo = get_object_or_404(LibraryInfo.objects.select_related('sampleinfo',
                                                                   'protocalinfo', 'team_member_initails'), pk=pk)
    sampleinfo = libinfo.sampleinfo
    summaryfield = ['library_id', 'library_description', 'sampleinfo', 'date_started', 'date_completed',
                    'team_member_initails', 'experiment_type', 'protocal_used',
                    'reference_to_notebook_and_page_number', 'notes']
    seqfield = ['seq_id', 'default_label', 'machine',
                'read_length', 'read_type', 'total_reads']
    relateseq = libinfo.seqinfo_set.all().only(
        'seq_id', 'machine', 'read_length', 'read_type', 'total_reads')
    context = {
        'libinfo': libinfo,
        'sampleinfo': sampleinfo,
        'summaryfield': summaryfield,
        'relateseq': relateseq.order_by('seq_id'),
        'seqfield': seqfield
    }
    return render(request, 'masterseq_app/libdetail.html', context=context)


def SeqDetailView(request, pk):
    """ Seq detail page thtough the primary key
    """
    seqinfo = get_object_or_404(SeqInfo.objects.select_related('libraryinfo',
                                                               'machine', 'i7index', 'i5index', 'team_member_initails'), pk=pk)
    libinfo = seqinfo.libraryinfo
    saminfo = libinfo.sampleinfo
    summaryfield = ['seq_id', 'sampleinfo', 'libraryinfo', 'default_label', 'team_member_initails',
                    'date_submitted_for_sequencing', 'machine', 'read_length', 'read_type', 'portion_of_lane',
                    'i7index', 'i5index', 'total_reads', 'notes']
    bioinfofield = ['genome', 'pipeline_version', 'final_reads', 'final_yield', 'mito_frac',
                    'tss_enrichment', 'frop']
    singlecellfield = ['10x Results','10x RefGenome','CoolAdmin Results', 'CoolAdmin RefGenome', 'CoolAdmin Date']
    #changed
    singlecelldata = get_singlecell_data(seqinfo, seqinfo.id)
    seqbioinfos = seqinfo.seqbioinfo_set.all().select_related('genome')
    setqcfield = ['set_id', 'set_name',
                  'experiment_type', 'url', 'date_requested']
    setqcs = LibrariesSetQC.objects.filter(libraries_to_include=seqinfo)

    context = {
        'libinfo': libinfo,
        'saminfo': saminfo,
        'seqinfo': seqinfo,
        'summaryfield': summaryfield,
        'seqbioinfos': seqbioinfos,
        'bioinfofield': bioinfofield,
        'setqcs': setqcs,
        'setqcfield': setqcfield,
        'singlecellfield': singlecellfield,
        'singlecelldata': singlecelldata,

    }
    return render(request, 'masterseq_app/seqdetail.html', context=context)


def SeqDetail2View(request, seqid):
    """ Seq detail page thtough the seq id
    """
    seqinfo = get_object_or_404(SeqInfo.objects.select_related('libraryinfo',
                                                               'machine', 'i7index', 'i5index', 'team_member_initails'), seq_id=seqid)
    libinfo = seqinfo.libraryinfo
    saminfo = libinfo.sampleinfo
    summaryfield = ['seq_id', 'sampleinfo', 'libraryinfo', 'default_label', 'team_member_initails',
                    'date_submitted_for_sequencing', 'machine', 'read_length', 'read_type', 'portion_of_lane',
                    'i7index', 'i5index', 'total_reads', 'notes']
    bioinfofield = ['genome', 'pipeline_version', 'final_reads', 'final_yield', 'mito_frac',
                    'tss_enrichment', 'frop']
    seqbioinfos = seqinfo.seqbioinfo_set.all().select_related('genome')
    setqcfield = ['set_id', 'set_name',
                  'experiment_type', 'url', 'date_requested']
    setqcs = LibrariesSetQC.objects.filter(libraries_to_include=seqinfo)
    context = {
        'libinfo': libinfo,
        'saminfo': saminfo,
        'seqinfo': seqinfo,
        'summaryfield': summaryfield,
        'seqbioinfos': seqbioinfos,
        'bioinfofield': bioinfofield,
        'setqcs': setqcs,
        'setqcfield': setqcfield

    }
    return render(request, 'masterseq_app/seqdetail.html', context=context)


def load_samples(request):
    """ Used in ajax loading samples by autocompleting what user input when updating a library
    """
    q = request.GET.get('term', '')
    samples = SampleInfo.objects.filter(Q(sample_id__icontains=q) | Q(
        sample_index__icontains=q)).values('sample_index', 'sample_id')[:20]
    results = []
    for sample in samples:
        samplesearch = {}
        samplesearch['id'] = sample['sample_index']+':'+sample['sample_id']
        samplesearch['label'] = sample['sample_index']+':'+sample['sample_id']
        samplesearch['value'] = sample['sample_index']+':'+sample['sample_id']
        results.append(samplesearch)
    return JsonResponse(results, safe=False)


def load_libs(request):
    """ Used in ajax loading libraries by autocompleting what user input when updating a sequencing
    """
    q = request.GET.get('term', '')
    libs = LibraryInfo.objects.filter(
        library_id__icontains=q).values('library_id')[:20]
    results = []
    for lib in libs:
        libsearch = {}
        libsearch['id'] = lib['library_id']
        libsearch['label'] = lib['library_id']
        libsearch['value'] = lib['library_id']
        results.append(libsearch)
    return JsonResponse(results, safe=False)


def SaveMyMetaDataExcel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="MyMetaData.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Samples')
    row_num = 0
    style = xlwt.XFStyle()
    style.font.bold = True
    style.alignment.wrap = 1
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['turquoise']
    style.pattern = pattern
    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    style.borders = borders

    row_num = 0
    ws.row(row_num).height_mismatch = True
    ws.row(row_num).height = 256*1
    ws.write_merge(0, 0, 0, 24, 'From sample submission form', style)
    style = xlwt.XFStyle()
    style.font.bold = True
    style.alignment.wrap = 1
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['light_green']
    style.pattern = pattern
    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    style.borders = borders

    row_num = 0
    ws.row(row_num).height_mismatch = True
    ws.row(row_num).height = 256*1
    ws.write_merge(0, 0, 25, 28, 'To be entered upon reciept', style)
    row_num = 1
    columns_width = [15, 15, 15, 21, 15, 15, 21, 15, 15, 15, 15, 15, 25, 30, 12,
                     15, 15, 11, 12, 12, 12, 12, 12, 12, 30, 15, 15, 15, 25]
    columns = ['Date', 'PI', 'Research contact name', 'Research contact e-mail',
               'Research contact phone', 'Fiscal contact name', 'Fiscal conact e-mail', 'Index for payment','Financial Unit','Project number','Task number','Funding Source Number (if sponsored research)',
               'Sample ID', 'Sample description', 'Species', 'Sample type', 'Preperation',
               'Fixation?', 'Sample amount', 'Units', 'Service requested', 'Sequencing depth to target',
               'Sequencing length requested', 'Sequencing type requested', 'Notes',
               'Date sample received', 'team member', 'Storage location', 'Internal_Notes']

    for col_num in range(len(columns)):
        ws.col(col_num).width = 256*columns_width[col_num]
        if col_num == 12:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            ws.row(row_num).height_mismatch = True
            ws.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 5
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
            ws.write(row_num, col_num, columns[col_num], style)

        else:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            ws.row(row_num).height_mismatch = True
            ws.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 22
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
            ws.write(row_num, col_num, columns[col_num], style)
    Samples_list = SampleInfo.objects.filter(team_member=request.user).order_by('pk').select_related('group',
                                                                                                     'team_member').values_list('date', 'group__name',
                                                                                                                                'research_name', 'research_email', 'research_phone', 'fiscal_name', 'fiscal_email', 'fiscal_index', 'financial_unit',
                                                                                                                                'project_number','task_number','funding_source_number',
                                                                                                                                'sample_id', 'description', 'species', 'sample_type',
                                                                                                                                'preparation', 'fixation', 'sample_amount', 'unit', 'service_requested', 'seq_depth_to_target',
                                                                                                                                'seq_length_requested', 'seq_type_requested', 'notes', 'date_received',
                                                                                                                                'team_member__username', 'storage', 'internal_notes'
                                                                                                                                )
    # print(list(Samples_list))
    # print(len(Samples_list))
    rows = Samples_list
    font_style = xlwt.XFStyle()
    #rows = User.objects.all().values_list('username', 'first_name', 'last_name', 'email')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str((row[col_num] or '')), font_style)
    wl = wb.add_sheet('Libraries')
    row_num = 0

    columns_width = [30, 25, 12, 15, 15, 15, 20, 20, 15, 30]
    columns = ['Sample ID (Must Match Column I in Sample Sheet)', 'Library description', 'Team member intials', 'Date experiment started', 'Date experiment completed',
               'Experiment type', 'Protocol used', 'Reference to notebook and page number', 'library_id',
               'notes']

    for col_num in range(len(columns)):
        wl.col(col_num).width = 256*columns_width[col_num]
        if col_num == 0:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            wl.row(row_num).height_mismatch = True
            wl.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 5
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders

        else:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            wl.row(row_num).height_mismatch = True
            wl.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 22
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
        wl.write(row_num, col_num, columns[col_num], style)
    Libraries_list = LibraryInfo.objects.filter(team_member_initails=request.user).order_by('pk').select_related(
        'team_member_initails', 'sampleinfo').values_list('sampleinfo__sample_id', 'library_description', 'team_member_initails__username', 'date_started',
                                                          'date_completed', 'experiment_type', 'protocal_used',
                                                          'reference_to_notebook_and_page_number', 'library_id', 'notes')

    rows = Libraries_list
    font_style = xlwt.XFStyle()
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            wl.write(row_num, col_num, str((row[col_num] or '')), font_style)

    we = wb.add_sheet('Sequencings')
    row_num = 0

    columns_width = [30, 25, 12, 12, 20, 15, 15, 15, 15, 15,
                     15, 12, 10, 12, 12, 30, 15, 15, 15, 15, 15, 15, 15, 15]
    columns = ['Sample ID (Must Match Column I in Sample Sheet)', 'Label (for QC report)', 'Species',
               'Team member intials', 'Date submitted for sequencing', 'Library ID', 'Sequencing ID', 'Experiment type',
               'Sequening core', 'Machine', 'Sequening length', 'Read type', 'Portion of lane',
               'i7 index (if applicable)', 'i5 Index (or single index', 'Notes', 'pipeline_version', 'Genome', 'total_reads',
               'final_reads', 'final_yield', 'mito_frac', 'tss_enrichment', 'frop']
    for col_num in range(len(columns)):
        we.col(col_num).width = 256*columns_width[col_num]
        if col_num == 0:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            we.row(row_num).height_mismatch = True
            we.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 5
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders

        else:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            we.row(row_num).height_mismatch = True
            we.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 22
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
        we.write(row_num, col_num, columns[col_num], style)
    Seqs_list = SeqInfo.objects.filter(team_member_initails=request.user).order_by('pk').select_related('libraryinfo',
                                                                                                        'libraryinfo__sampleinfo', 'team_member_initails', 'machine', 'i7index', 'i5index').\
        prefetch_related(Prefetch('seqbioinfo_set__genome')).values_list(
        'libraryinfo__sampleinfo__sample_id',
        'default_label', 'libraryinfo__sampleinfo__species',
        'team_member_initails__username', 'date_submitted_for_sequencing',
        'libraryinfo__library_id', 'seq_id', 'libraryinfo__experiment_type',
        'machine__sequencing_core', 'machine__machine_name', 'read_length', 'read_type',
        'portion_of_lane', 'i7index__indexid', 'i5index__indexid', 'notes',
        'seqbioinfo__pipeline_version', 'seqbioinfo__genome__genome_name',
        'total_reads', 'seqbioinfo__final_reads', 'seqbioinfo__final_yield',
        'seqbioinfo__mito_frac', 'seqbioinfo__tss_enrichment', 'seqbioinfo__frop')
    # print(list(Seqs_list))
    # print(len(Seqs_list))
    rows = Seqs_list
    font_style = xlwt.XFStyle()
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            we.write(row_num, col_num, str((row[col_num] or '')), font_style)
    wb.save(response)
    return response


def SaveAllMetaDataExcel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="AllMetaData.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Samples')
    row_num = 0
    style = xlwt.XFStyle()
    style.font.bold = True
    style.alignment.wrap = 1
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['turquoise']
    style.pattern = pattern
    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    style.borders = borders

    row_num = 0
    ws.row(row_num).height_mismatch = True
    ws.row(row_num).height = 256*1
    ws.write_merge(0, 0, 0, 24, 'From sample submission form', style)
    style = xlwt.XFStyle()
    style.font.bold = True
    style.alignment.wrap = 1
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['light_green']
    style.pattern = pattern
    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    style.borders = borders

    row_num = 0
    ws.row(row_num).height_mismatch = True
    ws.row(row_num).height = 256*1
    ws.write_merge(0, 0, 25, 28, 'To be entered upon reciept', style)
    row_num = 1
    columns_width = [15, 15, 15, 21, 15, 15, 21, 15, 15, 15, 15, 15, 25, 30, 12,
                     15, 15, 11, 12, 12, 12, 12, 12, 12, 30, 15, 15, 15, 25]
    columns = ['Date', 'PI', 'Research contact name', 'Research contact e-mail',
               'Research contact phone', 'Fiscal contact name', 'Fiscal conact e-mail', 'Index for payment','Financial Unit','Project number','Task number','Funding Source Number (if sponsored research)',
               'Sample ID', 'Sample description', 'Species', 'Sample type', 'Preperation',
               'Fixation?', 'Sample amount', 'Units', 'Service requested', 'Sequencing depth to target',
               'Sequencing length requested', 'Sequencing type requested', 'Notes',
               'Date sample received', 'team member', 'Storage location', 'Internal Notes']

    for col_num in range(len(columns)):
        ws.col(col_num).width = 256*columns_width[col_num]
        if col_num == 12:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            ws.row(row_num).height_mismatch = True
            ws.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 5
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
            ws.write(row_num, col_num, columns[col_num], style)

        else:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            ws.row(row_num).height_mismatch = True
            ws.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 22
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
            ws.write(row_num, col_num, columns[col_num], style)

    Samples_list = SampleInfo.objects.all().order_by('pk').select_related('group',
                                                                          'team_member').values_list('date', 'group__name',
                                                                                                     'research_name', 'research_email', 'research_phone', 'fiscal_name', 'fiscal_email', 'fiscal_index', 'financial_unit',
                                                                                                     'project_number','task_number','funding_source_number',
                                                                                                     'sample_id', 'description', 'species', 'sample_type',
                                                                                                     'preparation', 'fixation', 'sample_amount', 'unit', 'service_requested', 'seq_depth_to_target',
                                                                                                     'seq_length_requested', 'seq_type_requested', 'notes', 'date_received',
                                                                                                     'team_member__username', 'storage', 'internal_notes'
                                                                                                     )
    # print(list(Samples_list))
    # print(len(Samples_list))
    rows = Samples_list
    font_style = xlwt.XFStyle()
    #rows = User.objects.all().values_list('username', 'first_name', 'last_name', 'email')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str((row[col_num] or '')), font_style)
    wl = wb.add_sheet('Libraries')
    row_num = 0

    columns_width = [30, 25, 12, 15, 15, 15, 20, 20, 15, 30]
    columns = ['Sample ID (Must Match Column I in Sample Sheet)', 'Library description', 'Team member intials', 'Date experiment started', 'Date experiment completed',
               'Experiment type', 'Protocol used', 'Reference to notebook and page number', 'library_id',
               'notes']
    for col_num in range(len(columns)):
        wl.col(col_num).width = 256*columns_width[col_num]
        if col_num == 0:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            wl.row(row_num).height_mismatch = True
            wl.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 5
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders

        else:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            wl.row(row_num).height_mismatch = True
            wl.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 22
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
        wl.write(row_num, col_num, columns[col_num], style)
    Libraries_list = LibraryInfo.objects.all().order_by('pk').select_related(
        'team_member_initails', 'sampleinfo').values_list('sampleinfo__sample_id',
                                                          'library_description', 'team_member_initails__username', 'date_started',
                                                          'date_completed', 'experiment_type', 'protocal_used',
                                                          'reference_to_notebook_and_page_number', 'library_id', 'notes')
    # print(list(Libraries_list))
    # print(len(Libraries_list))
    rows = Libraries_list
    font_style = xlwt.XFStyle()
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            wl.write(row_num, col_num, str((row[col_num] or '')), font_style)

    we = wb.add_sheet('Sequencings')
    row_num = 0

    columns_width = [30, 25, 12, 12, 20, 15, 15, 15, 15, 15,
                     15, 12, 10, 12, 12, 30, 15, 15, 15, 15, 15, 15, 15, 15]
    columns = ['Sample ID (Must Match Column I in Sample Sheet)', 'Label (for QC report)', 'Species',
               'Team member intials', 'Date submitted for sequencing', 'Library ID', 'Sequencing ID', 'Experiment type',
               'Sequening core', 'Machine', 'Sequening length', 'Read type', 'Portion of lane',
               'i7 index (if applicable)', 'i5 Index (or single index', 'Notes', 'pipeline_version', 'Genome', 'total_reads',
               'final_reads', 'final_yield', 'mito_frac', 'tss_enrichment', 'frop']
    for col_num in range(len(columns)):
        we.col(col_num).width = 256*columns_width[col_num]
        if col_num == 0:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            we.row(row_num).height_mismatch = True
            we.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 5
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders

        else:
            style = xlwt.XFStyle()
            style.alignment.wrap = 1
            style.font.bold = True
            #first_col = ws.col(0)
            #first_col.width = 256 * 6
            we.row(row_num).height_mismatch = True
            we.row(row_num).height = 256*3
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_fore_colour = 22
            style.pattern = pattern
            borders = xlwt.Borders()
            borders.left = 1
            borders.right = 1
            borders.top = 1
            borders.bottom = 1
            style.borders = borders
        we.write(row_num, col_num, columns[col_num], style)
    Seqs_list = SeqInfo.objects.all().order_by('pk').select_related('libraryinfo',
                                                                    'libraryinfo__sampleinfo', 'team_member_initails', 'machine', 'i7index', 'i5index').\
        prefetch_related(Prefetch('seqbioinfo_set__genome')).values_list(
        'libraryinfo__sampleinfo__sample_id',
        'default_label', 'libraryinfo__sampleinfo__species',
        'team_member_initails__username', 'date_submitted_for_sequencing',
        'libraryinfo__library_id', 'seq_id', 'libraryinfo__experiment_type',
        'machine__sequencing_core', 'machine__machine_name', 'read_length', 'read_type',
        'portion_of_lane', 'i7index__indexid', 'i5index__indexid', 'notes',
        'seqbioinfo__pipeline_version', 'seqbioinfo__genome__genome_name',
        'total_reads', 'seqbioinfo__final_reads', 'seqbioinfo__final_yield',
        'seqbioinfo__mito_frac', 'seqbioinfo__tss_enrichment', 'seqbioinfo__frop')
    # print(list(Seqs_list))
    # print(len(Seqs_list))
    rows = Seqs_list
    font_style = xlwt.XFStyle()
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            we.write(row_num, col_num, str((row[col_num] or '')), font_style)
    wb.save(response)
    return response

def load_researchcontact(request):
    groupname = request.GET.get('group')
    researchcontact = CollaboratorPersonInfo.objects.\
        filter(person_id__groups__name__in=[groupname]).prefetch_related(
            Prefetch('person_id__groups'))
    return render(request, 'masterseq_app/researchcontact_dropdown_list_options.html', {'researchcontact': researchcontact})

def download(request, path):
    #file_path = os.path.join(settings.MEDIA_ROOT, path)
    dbfolder = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'data/masterseq_app')
    file_path = os.path.join(dbfolder, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(
                fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + \
                os.path.basename(file_path)
            return response
    raise Http404


def get_singlecell_data(seq_info, seq_pk):
    """
    Need to return:
    singlecellfield = ['10x Results','10x RefGenome','CoolAdmin Status', 'CoolAdmin RefGenome', 'CoolAdmin Date']
    """
    seq_id = seq_info.seq_id
    exptype = seq_info.libraryinfo.experiment_type
    tenx_status = get_tenx_status(seq_id, exptype)
    tenx_refgenome = getReferenceUsed(seq_id)
    cooladmin_objects = CoolAdminSubmission.objects.all()
    # TODO in future get time and status from database
    cooladmin_date_modified = check_cooladmin_time(seq_pk, cooladmin_objects)
    cooladmin_results = get_cooladmin_status(seq_id, seq_pk)
    if cooladmin_results == 'ClickToSubmit':
        cooladmin_results = 'Not Submitted'
    cooladmin_refgenome = get_cooladmin_genome(seq_pk, cooladmin_objects)
    data = {}
    data['10x Results'] = tenx_status
    data['10x RefGenome'] = tenx_refgenome
    data['CoolAdmin Results'] = cooladmin_results
    data['CoolAdmin RefGenome'] = cooladmin_refgenome
    data['CoolAdmin Date'] = cooladmin_date_modified
    print(data)
    return data

# Should be in database


def get_cooladmin_genome(seq_pk, cooladmin_objects):
    if cooladmin_objects.filter(seqinfo=seq_pk).exists():
        print('ca obj exists')
        ca = cooladmin_objects.get(seqinfo=seq_pk)
        return ca.refgenome
    else:
        return 'N/A'


@transaction.atomic
def EncodeDataSaveView(request):
    encode_data_form = EncodeDataForm(request.POST or None)
    if request.method == 'POST':
        if encode_data_form.is_valid():
            data = encode_data_form.cleaned_data['encode_link']
            data_sam = {}
            data_lib = {}
            data_seq = {}

            # First, biosamples.... ================================

            samp_indexes = list(SampleInfo.objects.values_list(
                'sample_index', flat=True))
            existingmaxindex = max([int(x.split('-')[1])
                                    for x in samp_indexes if x.startswith('SAMPNA')])

            for sample in data['samples'].keys():
                today = datetime.date.today()
                if not SampleInfo.objects.filter(sample_id=sample).exists():
                    data_sam[sample] = {}
                    data_sam[sample] = {
                        'group': 'David Gorkin',
                        'team_member': request.user.username,
                        'species': data['samples'][sample]['species'],
                        'sample_type': data['samples'][sample]['sample_type'],
                        'description': data['samples'][sample]['description'],
                        'notes': data['samples'][sample]['notes'],
                        'date': str(today),
                        'sample_index': 'SAMPNA-'+str(existingmaxindex+1)

                    }
                    existingmaxindex += 1

            # Next, libraries.... ================================

            exp_indexes = list(LibraryInfo.objects.values_list(
                'experiment_index', flat=True))
            existingmaxexpindex = max([int(x.split('-')[1])
                                       for x in exp_indexes if x.startswith('EXPNA')])

            lib_new_name = {}
            lib_ids = list(LibraryInfo.objects.values_list(
                'library_id', flat=True))
            maxid = max([int(x.split('_')[1])
                         for x in lib_ids if x.startswith('ENCODE')]+[0])
            curren_maxid = maxid
            for library in data['libraries'].keys():
                existing_flag = 0
                sam_id = data['libraries'][library]['sampleinfo']
                if SampleInfo.objects.filter(sample_id=sam_id).exists():
                    thissample = SampleInfo.objects.get(sample_id=sam_id)
                    for item in thissample.libraryinfo_set.all():
                        if (len(item.notes.split(';')[1].split(':')) < 2):
                            #print('failed libs:')
                            # print(library)
                            # print(item.notes)
                            break
                        if library == item.notes.split(';')[1].split(':')[1]:
                            #print('successful libs:')
                            # print(library)
                            # print(item.notes)
                            lib_new_name[library] = item.library_id
                            existing_flag = 1
                            break
                        else:
                            existing_flag = 0

                if existing_flag == 0:
                    curren_maxid += 1
                    libid_new = '_'.join(['ENCODE', str(curren_maxid)])
                    lib_new_name[library] = libid_new
                    data_lib[libid_new] = {}
                    data_lib[libid_new] = {
                        'sampleinfo': sam_id,
                        'lib_description': data['libraries'][library]['library_description'],
                        'experiment_type': data['libraries'][library]['experiment_type'],
                        'notes': data['libraries'][library]['notes'],
                        'team_member_initails': request.user.username,
                        'experiment_index': 'EXPNA-'+str(existingmaxexpindex+1)
                    }
                    existingmaxexpindex += 1

            # Finally, sequencings... ================================

            current_counts = {}
            for seq in data['sequencings'].keys():
                existing_flag = 0
                lib_id = data['sequencings'][seq]['libraryinfo']
                if LibraryInfo.objects.filter(library_id=lib_new_name[lib_id]).exists():
                    libraryinfo = LibraryInfo.objects.get(
                        library_id=lib_new_name[lib_id])
                    for item in libraryinfo.seqinfo_set.all():
                        if seq == item.notes.split(';')[0].split(':')[1]:
                            existing_flag = 1
                            print(seq+'___ooooo___'+item.seq_id)
                            break
                        else:
                            existing_flag = 0
                if existing_flag == 0:
                    if lib_new_name[lib_id] not in current_counts.keys():
                        try:
                            libraryinfo = LibraryInfo.objects.get(
                                library_id=lib_new_name[lib_id])
                            current_counts[lib_new_name[lib_id]
                                           ] = libraryinfo.seqinfo_set.all().count()
                        except:
                            current_counts[lib_new_name[lib_id]] = 0

                    if current_counts[lib_new_name[lib_id]] == 0:
                        thisseqid = lib_new_name[lib_id]
                        current_counts[lib_new_name[lib_id]] += 1
                    else:
                        thisseqid = lib_new_name[lib_id]+'_' + \
                            str(current_counts[lib_new_name[lib_id]]+1)
                        current_counts[lib_new_name[lib_id]] += 1
                    data_seq[thisseqid] = {}
                    data_seq[thisseqid] = {
                        'libraryinfo': lib_new_name[lib_id],
                        'default_label': data['sequencings'][seq]['default_label'],
                        'team_member_initails': request.user.username,
                        'notes': data['sequencings'][seq]['notes']
                    }
            #data_seq = {i:data_seq[i] for i in sorted(data_seq.keys())}
            data_seq = {y: data_seq[y] for y in [x[1] for x in sorted(
                [(value['libraryinfo'], key) for (key, value) in data_seq.items()])]}

            if 'Preview' in request.POST:
                displayorder_sam = ['sample_index', 'group', 'description',
                                    'date', 'species', 'sample_type', 'notes', 'team_member']
                displayorder_lib = ['sampleinfo', 'lib_description', 'team_member_initails', 'experiment_index',
                                    'experiment_type', 'notes']
                displayorder_seq = [
                    'libraryinfo', 'default_label', 'team_member_initails', 'notes']

                context = {
                    'encode_data_form': encode_data_form,
                    'modalshow': 1,
                    'displayorder_sam': displayorder_sam,
                    'displayorder_lib': displayorder_lib,
                    'displayorder_seq': displayorder_seq,
                    'data_sam': data_sam,
                    'data_lib': data_lib,
                    'data_seq': data_seq,
                }
                return render(request, 'masterseq_app/encode.html', context)

            if 'Save' in request.POST:
                for k, v in data_sam.items():
                    if v['group']:
                        group_tm = Group.objects.get(name=v['group'])
                    else:
                        group_tm = None
                    SampleInfo.objects.create(
                        sample_id=k,
                        species=v['species'],
                        team_member=request.user,
                        description=v['description'],
                        sample_type=v['sample_type'],
                        notes=v['notes'],
                        group=group_tm,
                        date=today,
                        sample_index=v['sample_index']
                    )
                for k, v in data_lib.items():
                    LibraryInfo.objects.create(
                        library_id=k,
                        sampleinfo=SampleInfo.objects.get(
                            sample_id=v['sampleinfo']),
                        library_description=v['lib_description'],
                        experiment_type=v['experiment_type'],
                        notes=v['notes'],
                        team_member_initails=request.user,
                        experiment_index=v['experiment_index']
                    )
                for k, v in data_seq.items():
                    SeqInfo.objects.create(
                        seq_id=k,
                        libraryinfo=LibraryInfo.objects.get(
                            library_id=v['libraryinfo']),
                        team_member_initails=request.user,
                        notes=v['notes'],
                        default_label=v['default_label'],
                    )

                return redirect('masterseq_app:user_metadata')

    else:
        encode_set_form = EncodeDataForm(None)

    context = {
        'encode_data_form': encode_data_form,
    }

    return render(request, 'masterseq_app/encode.html', context)
