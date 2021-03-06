from django import forms
from .models import SampleInfo, LibraryInfo, SeqMachineInfo, SeqInfo,\
    choice_for_read_type, choice_for_species, choice_for_sample_type,\
    choice_for_preparation, choice_for_experiment_type, choice_for_unit,\
    choice_for_fixation
from django.contrib.auth.models import User,Group
import datetime
from nextseq_app.models import Barcode
from epigen_ucsd_django.shared import datetransform, SelfUniqueValidation
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from epigen_ucsd_django.models import CollaboratorPersonInfo
from django.db.models import Prefetch
from django.urls import reverse
import re
import requests
import time


class SampleCreationForm(forms.ModelForm):
    group = forms.CharField(
        label='Group Name',
        required=False,
        widget = forms.TextInput({'class': 'ajax_groupinput_form', 'size': 30}),
        )

    class Meta:
        model = SampleInfo
        fields = ['sample_id','description','date','group','research_name',\
        'research_email','research_phone','fiscal_name','fiscal_email','fiscal_index',\
        'financial_unit','project_number','task_number','funding_source_number',\
        'species','sample_type','preparation',\
        'fixation','sample_amount','unit','service_requested',\
        'seq_depth_to_target','seq_length_requested','seq_type_requested','notes','date_received','storage','internal_notes','status']
        widgets ={
            'date': forms.DateInput(),
            'description':forms.Textarea(attrs={'cols': 60, 'rows': 3}),
            'notes':forms.Textarea(attrs={'cols': 60, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.group:
            self.initial['group'] = str(self.instance.group.name)
            gname = str(self.instance.group.name)

    def clean_group(self):
        gname = self.cleaned_data['group']
        if gname:
	        if not Group.objects.filter(name=gname).exists():
	            raise forms.ValidationError('Invalid Group Name!')
	        return Group.objects.get(name=gname)


class LibraryCreationForm(forms.ModelForm):
    sampleinfo = forms.ModelChoiceField(queryset=SampleInfo.objects.all(
    ), widget=forms.TextInput({'class': 'ajax_sampleinput_form', 'size': 50}))

    class Meta:
        model = LibraryInfo
        fields = ['library_id', 'sampleinfo', 'library_description','date_started', 'date_completed', 'experiment_type', 'protocal_used',
                  'reference_to_notebook_and_page_number', 'notes']
        widgets = {
            'date_started': forms.DateInput(),
            'date_completed': forms.DateInput(),
            'library_description': forms.Textarea(attrs={'cols': 60, 'rows': 2}),
            'notes': forms.Textarea(attrs={'cols': 60, 'rows': 3}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['sampleinfo'] = self.instance.sampleinfo.__str__

class SeqCreationForm(forms.ModelForm):
    libraryinfo = forms.ModelChoiceField(queryset=LibraryInfo.objects.all(
    ), widget=forms.TextInput({'class': 'ajax_libinput_form', 'size': 50}))

    class Meta:
        model = SeqInfo
        fields = ['seq_id', 'libraryinfo', 'date_submitted_for_sequencing', 'machine', 'read_length', 'read_type',
                  'portion_of_lane', 'i7index', 'i5index', 'default_label', 'notes']
        widgets = {
            'date_submitted_for_sequencing': forms.DateInput(),
            'notes': forms.Textarea(attrs={'cols': 60, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['libraryinfo'] = self.instance.libraryinfo.__str__
        
class BulkUpdateForm(forms.Form):
	updateinfo = forms.CharField(
			label='To update metadata for multiple entries at the same time, please paste the following information below:\nColumn 1: The Sample ID, Library ID or Sequencing ID of each entry that you want to update (one row per entry). Note that these IDs must already be entered in the metadata app, and should be listed here exactly as they already are.\nColumn 2: The metadata field (i.e. column from the template) that you would like to update for each entry. You do not have to enter all columns from the template here. It is only necessary to enter the columns that you want to update.\nColumns 3+ (optional): You can update as many additional columns as you would like.\n\nNotes:\n(1) The first row that you paste must be the column titles so that the LIMS knows which columns to update. Make sure that each column has a title that exactly matches the corresponding titles in Template\n(2) This function currently does not support updating group, research contact, or fiscal contact.\n(3) Please click on the "show examples" tab to the right to see an example.\n\nThe first column should be Sample ID, Library ID or Sequencing ID',
			widget=forms.Textarea(attrs={'style':'width:100%','rows': 11}),
			required=True,
					)
	def clean_updateinfo(self):
		data = self.cleaned_data['updateinfo']
		cleaneddata = []
		i = 0
		colinfo = {}
		titleinfo = {}
		seqcore = []
		seqmachine = []
		flagkeytitle = 0
		flagseqtitle = 0
		flaglibtitle = 0
		flagsamtitle = 0
		flagdate = 0
		flagspecies = 0
		flagtype = 0
		flagfixation = 0
		flagunit = 0
		flaguser = 0
		flaggroup = 0
		flagexp = 0
		flagbarcode = 0
		flagpolane = 0
		flagtype = 0
		flagcore = 0
		flagmachine = 0
		flagmachine = 0
		flagsamid = 0
		flaglibid = 0
		flagseqid = 0
		invalidseqtitle = []
		invalidlibtitle = []
		invalidsamtitle = []
		invaliddate = []
		invalidspecies = []
		invalidtype = []
		invalidfixation = []
		invalidunit = []
		invaliduserlist = []
		invalidgroup = []
		invalidexp = []
		invalidbarcodelist = []
		invalidpolane = []
		invalidtype = []
		invalidmachine = []
		invalidsamid = []
		invalidlibid = []
		invalidseqid = []


		for lineitem in data.strip().split('\n'):
			if lineitem != '\r':
				fields = lineitem.split('\t')
				if i == 0:
					if fields[0].strip().lower() not in ['sample id','library id (if library generated)','sequencing id','library id']:
						flagkeytitle = 1
					if fields[0].strip().lower() == 'sequencing id':
						for k in range(len(fields)-1):
							if fields[k+1].strip().lower() not in ['label (for qc report)',\
							'team member intials','date submitted for sequencing','library id','sequening core',\
							'machine','sequening length','read type','portion of lane','i7 index (if applicable)','i5 index (or single index)','notes',\
							'i7 index','i5 index','label','sequencing core','sequencing length','team member initials','date']:
								flagseqtitle = 1
								invalidseqtitle.append(fields[k+1].strip())
							elif fields[k+1].strip().lower() in ['sequening core','sequencing core']:
								flagcore = 1
							elif fields[k+1].strip().lower() == 'machine':
								flagmachine = 1

					elif fields[0].strip().lower() in ['library id (if library generated)','library id']:
						for k in range(len(fields)-1):
							if fields[k+1].strip().lower() not in ['sample id (must match column i in sample sheet)','library description',\
							'team member intials','date experiment started','date experiment completed','experiment type','protocol used',\
							'reference to notebook and page number','notes','sample id','team member initials']:
								flaglibtitle = 1
								invalidlibtitle.append(fields[k+1].strip())
					elif fields[0].strip().lower() == 'sample id':
						for k in range(len(fields)-1):
							if fields[k+1].strip().lower() not in ['date','sample description','species','sample type','preperation','fixation?',\
							'sample amount','units','unit','service requested','sequencing depth to target','sequencing length requested',\
							'sequencing type requested','notes','date sample received','initials of reciever','storage location','internal notes']:
								flagsamtitle = 1
								invalidsamtitle.append(fields[k+1].strip())
					for k in range(len(fields)):
						titleinfo[k] = fields[k].strip().lower()
						colinfo[k] = []

				else:
					for k in range(len(fields)):
						colinfo[k].append(fields[k])
				i = i+1
				cleaneddata.append(lineitem)

		if flagkeytitle == 1:
			raise forms.ValidationError('The first column should be \'Sample ID\', \'Library ID\' or \'Sequencing ID\'.')
		if flagseqtitle == 1:
			raise forms.ValidationError('Invalid titles for sequencings:'+','.join(invalidseqtitle))
		if flaglibtitle == 1:
			raise forms.ValidationError('Invalid titles for libraries:'+','.join(invalidlibtitle))		
		if flagsamtitle == 1:
			raise forms.ValidationError('Invalid titles for samples:'+','.join(invalidsamtitle))
		if flagcore != flagmachine:
			raise forms.ValidationError('Sequencing core and Machine should show up together.')



		for k in titleinfo.keys():
			if titleinfo[k] in ['date','date sample received','date experiment started','date experiment completed','date submitted for sequencing']:
				for item in colinfo[k]:
					try:
						anydate = datetransform(item)
					except:
						invaliddate.append(item)
						flagdate = 1
			elif titleinfo[k] == 'species':
				for item in colinfo[k]:
					if item.split('(')[0].lower().strip() not in [x[0].split('(')[0].strip() for x in choice_for_species]:
						invalidspecies.append(item)
						flagspecies = 1
			elif titleinfo[k] == 'sample type':
				for item in colinfo[k]:
					if item.split('(')[0].lower().strip() not in [x[0].split('(')[0].strip() for x in choice_for_sample_type]:
						invalidtype.append(item)
						flagtype = 1
			elif titleinfo[k] == 'fixation?':
				for item in colinfo[k]:
					if item.strip().lower() not in [x[0].lower() for x in choice_for_fixation]:
						invalidfixation.append(item)
						flagfixation = 1

			elif titleinfo[k] in ['units','unit']:
				for item in colinfo[k]:
					if item.split('(')[0].lower().strip() not in [x[0].split('(')[0].strip() for x in choice_for_unit]:
						invalidunit.append(item)
						flagunit = 1
			elif titleinfo[k] in ['team member intials','team member initials','initials of reciever']:
				for item in colinfo[k]:
					if item and not User.objects.filter(username=item).exists():
						invaliduserlist.append(item)
						flaguser = 1
			elif titleinfo[k] == 'pi':
				for item in colinfo[k]:
					gname = item.strip() if item.strip() not in ['NA','N/A'] else ''
					if gname:
						if not Group.objects.filter(name=gname).exists():
							invalidgroup.append(item)
							flaggroup = 1
			elif titleinfo[k] == 'experiment type':
				for item in colinfo[k]:
					if item.strip() not in [x[0].split('(')[0].strip() for x in choice_for_experiment_type]:
						invalidexp.append(item)
						flagexp = 1
			elif titleinfo[k] in ['i7 index (if applicable)','i5 index (or single index)','i7 index','i5 index']:
				for item in colinfo[k]:
					if item.strip() and item.strip() not in ['NA', 'Other (please explain in notes)', 'N/A']:
						if not Barcode.objects.filter(indexid=item.strip()).exists():
							invalidbarcodelist.append(item)
							flagbarcode = 1
			elif titleinfo[k] == 'portion of lane':
				for item in colinfo[k]:
					if item.strip() and item.strip() not in ['NA', 'Other (please explain in notes)', 'N/A']:
						try:
							float(polane)
						except:
							invalidpolane.append(polane)
							flagpolane = 1
			elif titleinfo[k] == 'read type':
				for item in colinfo[k]:
					if item.strip() and item.strip() not in [x[0].split('(')[0].strip() for x in choice_for_read_type]:
						invalidtype.append(seqtype)
						flagtype = 1
			elif titleinfo[k] == 'sequening core':
				seqcore = colinfo[k]
			elif titleinfo[k] == 'machine':
				seqmachine = colinfo[k]
			elif titleinfo[k] == 'sequencing id':
				for item in colinfo[k]:
					if not SeqInfo.objects.filter(seq_id=item).exists():
						invalidseqid.append(item)
						flagseqid = 1
			elif titleinfo[k] in ['library id (if library generated)','library id']:
				for item in colinfo[k]:
					if not LibraryInfo.objects.filter(library_id=item).exists():
						invalidlibid.append(item)
						flaglibid = 1
			elif titleinfo[k] == 'sample id':
				for item in colinfo[k]:
					if not SampleInfo.objects.filter(sample_id=item).exists():
						invalidsamid.append(item)
						flagsamid = 1

		for item in zip(seqcore,seqmachine):
			if not SeqMachineInfo.objects.filter(sequencing_core=item[0], machine_name=item[1]).exists():
				invalidmachine.append(seqcore+'_'+seqmachine)
				flagmachine = 1

		if flagdate == 1:
			raise forms.ValidationError('Invalid date:'+','.join(invaliddate)+'. Please enter like this: 10/30/2018 or 10/30/18')

		if flagspecies == 1:
			raise forms.ValidationError('Invalid species:'+','.join(invalidspecies))

		if flagtype == 1:
			raise forms.ValidationError('Invalid sample type:'+','.join(invalidtype))

		if flagfixation == 1:
			raise forms.ValidationError('Invalid fixation:'+','.join(invalidfixation)+\
				'.  Should be one of ('+','.join([x[0] for x in\
				 choice_for_fixation])+')')

		if flagunit == 1:
			raise forms.ValidationError('Invalid unit:'+','.join(invalidunit)+\
				'.  Should be one of ('+','.join([x[0] for x in\
				 choice_for_unit])+')')
		if flaguser == 1:
			raise forms.ValidationError(
				'Invalid Member Name:'+','.join(invaliduserlist))

		if flaggroup == 1:
			raise forms.ValidationError(
				'Invalid groups:'+','.join(set(invalidgroup))+'.<p style="color:green;">\
				Please check for accurary of the group name in <a href='+reverse('manager_app:collab_list')+'>Collaborators Table</a>. \
				<br>If this is a new group please contact the manager to add in.</p>')
		if flagexp == 1:
			raise forms.ValidationError(
				'Invalid experiment type:'+','.join(invalidexp))

		if flagbarcode == 1:
			raise forms.ValidationError(
				'Invalid i7 or i5 Barcode:'+','.join(invalidbarcodelist))
		if flagtype == 1:
			raise forms.ValidationError(
				'Invalid read type:'+','.join(invalidtype))
		if flagmachine == 1:
			raise forms.ValidationError(
				'Invalid seqmachine:'+','.join(invalidmachine))
		if flagseqid == 1:
			raise forms.ValidationError('These sequencings are not in database:'+','.join(invalidseqid))
		if flaglibid == 1:
			raise forms.ValidationError('These libraries are not in database:'+','.join(invalidlibid))

		if flagsamid == 1:
			raise forms.ValidationError('These samples are not in database:'+','.join(invalidsamid))



		return '\n'.join(cleaneddata)

class SamplesCreationForm(forms.Form):
	samplesinfo = forms.CharField(
			label='SampleInfo(Please copy and paste all of the columns in sheet \'samples\' from Template)',
			widget=forms.Textarea(attrs={'cols': 120, 'rows': 10}),
			required=True,
					)
	def clean_samplesinfo(self):
		data = self.cleaned_data['samplesinfo']
		cleaneddata = []
		flagdate = 0
		flagdate_received = 0
		flagspecies = 0
		flagtype = 0
		flagunit = 0
		flagfixation = 0
		flaguser = 0
		flagsampid = 0
		flaggroup = 0
		flagresearch = 0
		flagresearch1 = 0
		flagresearch2 = 0
		flagresearchphone = 0
		flagfiscal = 0
		flagfiscal1 = 0
		flagfiscal2 = 0
		flagfisindex = 0
		invaliddate = []
		invaliddate_received = []
		invalidspecies = []
		invalidtype = []
		invalidunit = []
		invalidfixation = []
		invaliduserlist = []
		invalidsampid = []
		selfsamps = []
		invalidgroup = []
		invalidresearch = []
		invalidresearch1 = []
		invalidresearch2 = []
		invalidresearchphone = []
		invalidfiscal = []
		invalidfiscal1 = []
		invalidfiscal2 = []
		invalidfisindex = []
		#invalidprep = []
		for lineitem in data.strip().split('\n'):
			if lineitem != '\r':
				#fields = lineitem.split('\t')
				fields = (lineitem+'\t'*20).split('\t')

				del fields[8:12]
				try:
					samdate = datetransform(fields[0].strip())
				except:
					invaliddate.append(fields[0].strip())
					flagdate = 1
				try:
					samdate_received = datetransform(fields[21].strip())
				except IndexError:
					pass
				except:
					invaliddate_received.append(fields[21].strip())
					flagdate_received = 1
				samid = fields[8].strip()
				samdescript = fields[9].strip()
				samspecies = fields[10].split('(')[0].lower().strip()
				if samspecies not in [x[0].split('(')[0].strip() for x in choice_for_species]:
					invalidspecies.append(samspecies)
					flagspecies = 1
				samtype = fields[11].split('(')[0].strip().lower()
				if samtype not in [x[0].split('(')[0].strip() for x in choice_for_sample_type]:
					invalidtype.append(samtype)
					flagtype = 1
				unit = fields[15].split('(')[0].strip().lower()
				if unit not in [x[0].split('(')[0].strip() for x in choice_for_unit]:
					invalidunit.append(fields[15])
					flagunit = 1
				fixation = fields[13].strip().lower()
				if fixation not in [x[0].lower() for x in choice_for_fixation]:
					invalidfixation.append(fields[13])
					flagfixation = 1
				try:
					membername = fields[22].strip()
				except:
					membername = ''
				if membername and not User.objects.filter(username=membername).exists():
					invaliduserlist.append(membername)
					flaguser = 1
				if SampleInfo.objects.filter(sample_id=samid).exists():
					invalidsampid.append(samid)
					flagsampid = 1
				selfsamps.append(samid)
				gname = fields[1].strip() if fields[1].strip() not in ['NA','N/A'] else ''
				if gname:
					if not Group.objects.filter(name=gname).exists():
						invalidgroup.append(fields[1].strip())
						flaggroup = 1

				resname = fields[2].strip() if fields[2].strip() not in ['NA','N/A'] else ''
				resemail = fields[3].strip().lower() if fields[3].strip() not in ['NA','N/A'] else ''
				resphone = re.sub('-| |\.|\(|\)|ext', '', fields[4].strip()) if fields[4].strip() not in ['NA','N/A'] else ''
				if resemail:
					if not gname or not Group.objects.filter(name=gname).exists():
						invalidgroup.append(fields[1].strip())
						flaggroup = 1
					else:
						thisgroup = Group.objects.get(name=gname)
						if thisgroup.collaboratorpersoninfo_set.all().filter(email__contains=[resemail]).exists():
							thisresearch = thisgroup.collaboratorpersoninfo_set.all().get(email__contains=[resemail])
							if resname:
								if not thisresearch.person_id.first_name in resname.split(' '):
									invalidresearch1.append(resname+':'+resemail)
									flagresearch1 = 1
						else:
							if not resname or len(resname.split(' '))<2:
								invalidresearch2.append(resname+':'+resemail)
								flagresearch2 = 1
				elif resname:
					if len(resname.split(' '))<2:
						invalidresearch2.append(resname)
						flagresearch2 = 1


				fiscalname = fields[5].strip() if fields[5].strip() not in ['NA','N/A'] else ''
				fiscalemail = fields[6].strip().lower() if fields[6].strip() not in ['NA','N/A'] else ''
				indname = fields[7].strip() if fields[7].strip() not in ['NA','N/A'] else ''
				if fiscalemail:
					if not gname or not Group.objects.filter(name=gname).exists():
						invalidgroup.append(fields[1].strip())
						flaggroup = 1
					else:
						thisgroup = Group.objects.get(name=gname)
						if thisgroup.collaboratorpersoninfo_set.all().filter(email__contains=[fiscalemail]).exists():
							thisfiscal = thisgroup.collaboratorpersoninfo_set.all().get(email__contains=[fiscalemail])
							if fiscalname:
								if not thisfiscal.person_id.first_name in fiscalname.split(' '):
									invalidfiscal1.append(fiscalname+':'+fiscalemail)
									flagfiscal1 = 1			
						else:
							if not fiscalname or len(fiscalname.split(' '))<2:
								invalidfiscal2.append(fiscalname+':'+fiscalemail)
								flagfiscal2 = 1
				elif fiscalname:
					if len(fiscalname.split(' '))<2:
						invalidresearch2.append(fiscalname)
						flagresearch2 = 1

				samnotes = fields[20].strip()
					
				cleaneddata.append(lineitem)
		if flagdate == 1:
			raise forms.ValidationError('Invalid date:'+','.join(invaliddate)+'. Please enter like this: 10/30/2018 or 10/30/18')
		if flagdate_received == 1:
			raise forms.ValidationError('Invalid date_received:'+','.join(invaliddate_received)+'. Please enter like this: 10/30/2018 or 10/30/18')

		if flagspecies == 1:
			raise forms.ValidationError('Invalid species:'+','.join(invalidspecies))
		if flagtype == 1:
			raise forms.ValidationError('Invalid sample type:'+','.join(invalidtype))

		if flagunit == 1:
			raise forms.ValidationError('Invalid unit:'+','.join(invalidunit)+\
				'.  Should be one of ('+','.join([x[0] for x in\
				 choice_for_unit])+')')
		if flagfixation == 1:
			raise forms.ValidationError('Invalid fixation:'+','.join(invalidfixation)+\
				'.  Should be one of ('+','.join([x[0] for x in\
				 choice_for_fixation])+')')
		if flaguser == 1:
			raise forms.ValidationError(
				'Invalid Member Name:'+','.join(invaliduserlist))
		if flagsampid == 1:
			raise forms.ValidationError(
				','.join(invalidsampid)+' is already existed in database')
		if flaggroup == 1:
			raise forms.ValidationError(
				'Invalid groups:'+','.join(set(invalidgroup))+'.<p style="color:green;">\
				Please check for accurary of the group name in <a href='+reverse('manager_app:collab_list')+'>Collaborators Table</a>. \
				<br>If this is a new group please contact the manager to add in.</p>')
		if flagresearch == 1:
			raise forms.ValidationError(
				'Invalid research contacts:'+','.join(invalidresearch)+'.<p style="color:green;">\
				Please check the reasons below \
				in <a href='+reverse('manager_app:collab_list')+'>Collaborators Table</a>:\
				(1).First name, last name and email match with profile in the database.\
				(2).The user is in the right group you provided.<br>\
				(3).The user name is not full name.<br>')
		if flagresearch1 == 1:
			raise forms.ValidationError(
				'Invalid research contacts:'+','.join(invalidresearch1)+'.<p style="color:green;">\
				The research contact\'s name in the database searched by email does not \
				match with your supplied name,please check \
				the accurary in <a href='+reverse('manager_app:collab_list')+'>Collaborators Table</a>')
		if flagresearch2 == 1:
			raise forms.ValidationError(
				'Invalid research contacts:'+','.join(invalidresearch2)+'.<p style="color:green;">\
				Since you are supplying a new email, please \
				fill in the research contact\'s full name')

		if flagfiscal == 1:
			raise forms.ValidationError(
				'Invalid fiscal contacts:'+','.join(invalidfiscal)+'.<p style="color:green;">\
				Please check the reasons below \
				in <a href='+reverse('manager_app:collab_list')+'>Collaborators Table</a>:\
				(1).First name, last name and email match with profile in the database.\
				(2).The user is in the right group you provided.<br>\
				(3).The user name is not full name.<br>')

		if flagfiscal1 == 1:
			raise forms.ValidationError(
				'Invalid fiscal contacts:'+','.join(invalidfiscal1)+'.<p style="color:green;">\
				The fiscal contact\'s name in the database searched by email does not \
				match with your supplied name,please check \
				the accurary in <a href='+reverse('manager_app:collab_list')+'>Collaborators Table</a>')
		if flagfiscal2 == 1:
			raise forms.ValidationError(
				'Invalid fiscal contacts:'+','.join(invalidfiscal2)+'.<p style="color:green;">\
				Since you are supplying a new email, please \
				fill in the fiscal contact\'s full name')

		sampselfduplicate = SelfUniqueValidation(selfsamps)
		if len(sampselfduplicate) > 0:
			raise forms.ValidationError(
				'Duplicate Sample Name within this bulk entry:'+','.join(sampselfduplicate))

		# if flagprep == 1:
		# 	raise forms.ValidationError('Invalid sample preparation:'+','.join(invalidprep))
		return '\n'.join(cleaneddata)




class LibsCreationForm(forms.Form):
    libsinfo = forms.CharField(
        label='LibsInfo(Please copy and paste all of the columns in sheet \'libraries\' from Template):',
        widget=forms.Textarea(attrs={'cols': 120, 'rows': 10}),
        required=True,
    )

    def clean_libsinfo(self):
        data = self.cleaned_data['libsinfo']
        cleaneddata = []
        flagdate = 0
        flagexp = 0
        flaglibid = 0
        flaguser = 0
        flagref = 0
        invaliddate = []
        invalidexp = []
        selflibs = []
        invalidlibid = []
        invaliduserlist = []
        selfsamps = []
        for lineitem in data.strip().split('\n'):
            if lineitem != '\r':
                cleaneddata.append(lineitem)
                # print(lineitem)
                #fields = lineitem.split('\t')
                fields = (lineitem+'\t'*10).split('\t')
                samid = fields[0].strip()
                if not SampleInfo.objects.filter(sample_id=samid).exists():
                    selfsamps.append(samid)
                try:
                    datestart = datetransform(fields[3].strip())
                except:
                    invaliddate.append(fields[3].strip())
                    flagdate = 1
                try:
                    dateend = datetransform(fields[4].strip())
                except:
                    invaliddate.append(fields[4].strip())
                    flagdate = 1
                libexp = fields[5].strip()
                if libexp not in [x[0].split('(')[0].strip() for x in choice_for_experiment_type]:
                    invalidexp.append(libexp)
                    flagexp = 1
                libid = fields[8].strip()
                if LibraryInfo.objects.filter(library_id=libid).exists():
                    invalidlibid.append(libid)
                    flaglibid = 1
                membername = fields[2].strip()
                if not User.objects.filter(username=membername).exists():
                    invaliduserlist.append(membername)
                    flaguser = 1
                if fields[7].strip().lower() in ['','na','other','n/a']:
                    flagref = 1

                selflibs.append(libid)

        if flagdate == 1:
            raise forms.ValidationError('Invalid date:'+','.join(invaliddate))
        if flagexp == 1:
            raise forms.ValidationError(
                'Invalid experiment type:'+','.join(invalidexp))
        if flaglibid == 1:
            raise forms.ValidationError(
                ','.join(invalidlibid)+' is already existed in database')
        libraryselfduplicate = SelfUniqueValidation(selflibs)
        if len(libraryselfduplicate) > 0:
            raise forms.ValidationError(
                'Duplicate Library within this bulk entry:'+','.join(libraryselfduplicate))
        if flaguser == 1:
            raise forms.ValidationError(
                'Invalid Member Name:'+','.join(invaliduserlist))
        if flagref == 1:
            raise forms.ValidationError('Please do not leave Reference_to_notebook_and_page_number as blank')        	
        
        sampselfduplicate = SelfUniqueValidation(selfsamps)
        if len(sampselfduplicate) > 0:
            raise forms.ValidationError(
                'Duplicate Sample Name within this bulk entry:'+','.join(sampselfduplicate))
        return '\n'.join(cleaneddata)

class LibsCreationForm_wetlab(forms.Form):
    libsinfo = forms.CharField(
        label='LibsInfo(Please copy and paste all of the columns in sheet \'libraries\' from Template):',
        widget=forms.Textarea(attrs={'cols': 120, 'rows': 10}),
        required=True,
    )

    def clean_libsinfo(self):
        data = self.cleaned_data['libsinfo']
        cleaneddata = []
        flagdate = 0
        flagexp = 0
        flaglibid = 0
        flaguser = 0
        flagref = 0
        flagsamp = 0
        invaliddate = []
        invalidexp = []
        selflibs = []
        invalidlibid = []
        invaliduserlist = []
        invalidsamps = []
        for lineitem in data.strip().split('\n'):
            if lineitem != '\r':
                cleaneddata.append(lineitem)
                # print(lineitem)
                #fields = lineitem.split('\t')
                fields = (lineitem+'\t'*10).split('\t')
                samid = fields[0].strip()
                if not SampleInfo.objects.filter(sample_id=samid).exists():
                    invalidsamps.append(samid)
                    flagsamp = 1
                try:
                    datestart = datetransform(fields[3].strip())
                except:
                    invaliddate.append(fields[3].strip())
                    flagdate = 1
                try:
                    dateend = datetransform(fields[4].strip())
                except:
                    invaliddate.append(fields[4].strip())
                    flagdate = 1
                libexp = fields[5].strip()
                if libexp not in [x[0].split('(')[0].strip() for x in choice_for_experiment_type]:
                    invalidexp.append(libexp)
                    flagexp = 1
                libid = fields[8].strip()
                if LibraryInfo.objects.filter(library_id=libid).exists():
                    invalidlibid.append(libid)
                    flaglibid = 1
                membername = fields[2].strip()
                if not User.objects.filter(username=membername).exists():
                    invaliduserlist.append(membername)
                    flaguser = 1
                if fields[7].strip().lower() in ['','na','other','n/a']:
                    flagref = 1

                selflibs.append(libid)

        if flagdate == 1:
            raise forms.ValidationError('Invalid date:'+','.join(invaliddate))
        if flagexp == 1:
            raise forms.ValidationError(
                'Invalid experiment type:'+','.join(invalidexp))
        if flaglibid == 1:
            raise forms.ValidationError(
                ','.join(invalidlibid)+' is already existed in database')
        libraryselfduplicate = SelfUniqueValidation(selflibs)
        if len(libraryselfduplicate) > 0:
            raise forms.ValidationError(
                'Duplicate Library within this bulk entry:'+','.join(libraryselfduplicate))
        if flaguser == 1:
            raise forms.ValidationError(
                'Invalid Member Name:'+','.join(invaliduserlist))
        if flagref == 1:
            raise forms.ValidationError('Please do not leave Reference_to_notebook_and_page_number as blank')        	
        
        if flagsamp == 1:
            raise forms.ValidationError(
                'Invalid Sample ID:'+','.join(invalidsamps)+'. Please make sure the samples have already in LIMS.')
        return '\n'.join(cleaneddata)


class SeqsCreationForm(forms.Form):
    seqsinfo = forms.CharField(
        label='SeqsInfo(Please copy and paste all of the columns in sheet \'sequencings\' from Template):',
        widget=forms.Textarea(attrs={'cols': 120, 'rows': 10}),
        required=True,
    )

    def clean_seqsinfo(self):
        data = self.cleaned_data['seqsinfo']
        cleaneddata = []
        flaglib = 0
        flagdate = 0
        flaguser = 0
        flagbarcode = 0
        flagbarcode2 = 0
        flagseqid = 0
        flagmachine = 0
        flagtype = 0
        flagpolane = 0
        flagexp = 0
        invalidlib = []
        invaliddate = []
        invaliduserlist = []
        invalidbarcodelist = []
        invalidbarcodelist2 = []
        invalidseqid = []
        selfseqs = []
        invalidmachine = []
        invalidtype = []
        invalidpolane = []
        invalidexp = []
        selfsamps = []
        selflibs = []

        for lineitem in data.strip().split('\n'):
            if lineitem != '\r':
                cleaneddata.append(lineitem)
                fields = (lineitem+'\t'*20).split('\t')
                libraryid = fields[5].strip()
                exptype = fields[7].strip()
                samid = fields[0].strip()
 

                if not LibraryInfo.objects.filter(library_id=libraryid).exists():
                    if exptype not in [x[0].split('(')[0].strip() for x in choice_for_experiment_type]:
                        invalidexp.append(exptype)
                        flagexp = 1                
                        selfsamps.append(samid)
                        selflibs.append(libraryid)


                if '-' in fields[4].strip():
                    datesub = fields[4].strip()
                else:
                    try:
                        datesub = datetransform(fields[4].strip())
                    except:
                        invaliddate.append(fields[4].strip())
                        flagdate = 1
                membername = fields[3].strip()
                if not User.objects.filter(username=membername).exists():
                    invaliduserlist.append(membername)
                    flaguser = 1

                indexname = fields[13].strip()
                if indexname and indexname not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    if not Barcode.objects.filter(indexid=indexname).exists():
                        invalidbarcodelist.append(indexname)
                        flagbarcode = 1
                indexname2 = fields[14].strip()
                if indexname2 and indexname2 not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    if not Barcode.objects.filter(indexid=indexname2).exists():
                        invalidbarcodelist2.append(indexname2)
                        flagbarcode2 = 1
                polane = fields[12].strip()
                if polane and polane not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    try:
                        float(polane)
                    except:
                        invalidpolane.append(polane)
                        flagpolane = 1
                seqid = fields[6].strip()
                if SeqInfo.objects.filter(seq_id=seqid).exists():
                    invalidseqid.append(seqid)
                    flagseqid = 1
                selfseqs.append(seqid)
                seqcore = fields[8].split('(')[0].strip()
                seqmachine = fields[9].split('(')[0].strip()
                if not SeqMachineInfo.objects.filter(sequencing_core=seqcore, machine_name=seqmachine).exists():
                    invalidmachine.append(seqcore+'_'+seqmachine)
                    flagmachine = 1
                seqtype = fields[11].strip()
                if seqtype not in [x[0].split('(')[0].strip() for x in choice_for_read_type]:
                    invalidtype.append(seqtype)
                    flagtype = 1

        if flaglib == 1:
            raise forms.ValidationError(
                'Invalid library info:'+','.join(invalidlib)+'. If the library is not stored in TS2\
                 please set the fifth column as na,n/a or other.')
        if flagdate == 1:
            raise forms.ValidationError('Invalid date:'+','.join(invaliddate))
        if flaguser == 1:
            raise forms.ValidationError(
                'Invalid Member Name:'+','.join(invaliduserlist))
        if flagbarcode == 1:
            raise forms.ValidationError(
                'Invalid i7 Barcode:'+','.join(invalidbarcodelist))
        if flagbarcode2 == 1:
            raise forms.ValidationError(
                'Invalid i5 Barcode:'+','.join(invalidbarcodelist2))
        if flagpolane == 1:
            raise forms.ValidationError(
                'Invalid portion of lane:'+','.join(invalidpolane))
        if flagseqid == 1:
            raise forms.ValidationError(
                ','.join(invalidseqid)+' is already existed in database')
        seqselfduplicate = SelfUniqueValidation(selfseqs)
        if len(seqselfduplicate) > 0:
            raise forms.ValidationError(
                'Duplicate Seq within this bulk entry:'+','.join(seqselfduplicate))
        if flagmachine == 1:
            raise forms.ValidationError(
                'Invalid seqmachine:'+','.join(invalidmachine))
        if flagtype == 1:
            raise forms.ValidationError(
                'Invalid read type:'+','.join(invalidtype))
        if flagexp == 1:
            raise forms.ValidationError(
                'Invalid experiment type:'+','.join(invalidexp))
        libraryselfduplicate = SelfUniqueValidation(selflibs)
        if len(libraryselfduplicate) > 0:
            raise forms.ValidationError(mark_safe(
                'Duplicate Library ID within this bulk entry:'+','.join(libraryselfduplicate)\
                +'<br> We are creating pseudo libraries for those not\
                 stored in database and assuming that they come from different samples so they should\
                not have the same name. If you are sure they are the same library, please go to\
                the library input interface to store the library first'))
        sampselfduplicate = SelfUniqueValidation(selfsamps)
        if len(sampselfduplicate) > 0:
            raise forms.ValidationError(
                'Duplicate Sample Name within this bulk entry:'+','.join(sampselfduplicate))

        return '\n'.join(cleaneddata)

    def clean_group(self):
        gname = self.cleaned_data['group']
        if not Group.objects.filter(name=gname).exists():
            raise forms.ValidationError('Invalid Group Name!')
        return gname

class SeqsCreationForm_wetlab(forms.Form):
    seqsinfo = forms.CharField(
        label='SeqsInfo(Please copy and paste all of the columns in sheet \'sequencings\' from Template):',
        widget=forms.Textarea(attrs={'cols': 120, 'rows': 10}),
        required=True,
    )

    def clean_seqsinfo(self):
        data = self.cleaned_data['seqsinfo']
        cleaneddata = []
        flaglib = 0
        flagdate = 0
        flaguser = 0
        flagbarcode = 0
        flagbarcode2 = 0
        flagseqid = 0
        flagmachine = 0
        flagtype = 0
        flagpolane = 0
        flagexp = 0

        invalidlib = []
        invaliddate = []
        invaliduserlist = []
        invalidbarcodelist = []
        invalidbarcodelist2 = []
        invalidseqid = []
        selfseqs = []
        invalidmachine = []
        invalidtype = []
        invalidpolane = []
        invalidexp = []

        for lineitem in data.strip().split('\n'):
            if lineitem != '\r':
                cleaneddata.append(lineitem)
                fields = (lineitem+'\t'*20).split('\t')
                libraryid = fields[5].strip()
                exptype = fields[7].strip()
                samid = fields[0].strip()
 

                if not LibraryInfo.objects.filter(library_id=libraryid).exists():
                	invalidlib.append(libraryid)
                	flaglib = 1


                if '-' in fields[4].strip():
                    datesub = fields[4].strip()
                else:
                    try:
                        datesub = datetransform(fields[4].strip())
                    except:
                        invaliddate.append(fields[4].strip())
                        flagdate = 1
                membername = fields[3].strip()
                if not User.objects.filter(username=membername).exists():
                    invaliduserlist.append(membername)
                    flaguser = 1

                indexname = fields[13].strip()
                if indexname and indexname not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    if not Barcode.objects.filter(indexid=indexname).exists():
                        invalidbarcodelist.append(indexname)
                        flagbarcode = 1
                indexname2 = fields[14].strip()
                if indexname2 and indexname2 not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    if not Barcode.objects.filter(indexid=indexname2).exists():
                        invalidbarcodelist2.append(indexname2)
                        flagbarcode2 = 1
                polane = fields[12].strip()
                if polane and polane not in ['NA', 'Other (please explain in notes)', 'N/A']:
                    try:
                        float(polane)
                    except:
                        invalidpolane.append(polane)
                        flagpolane = 1
                seqid = fields[6].strip()
                if SeqInfo.objects.filter(seq_id=seqid).exists():
                    invalidseqid.append(seqid)
                    flagseqid = 1
                selfseqs.append(seqid)
                seqcore = fields[8].split('(')[0].strip()
                seqmachine = fields[9].split('(')[0].strip()
                if not SeqMachineInfo.objects.filter(sequencing_core=seqcore, machine_name=seqmachine).exists():
                    invalidmachine.append(seqcore+'_'+seqmachine)
                    flagmachine = 1
                seqtype = fields[11].strip()
                if seqtype not in [x[0].split('(')[0].strip() for x in choice_for_read_type]:
                    invalidtype.append(seqtype)
                    flagtype = 1

        if flaglib == 1:
            raise forms.ValidationError(
                'Invalid library info:'+','.join(invalidlib)+'. Please make sure these libraries are already in LIMS')
        if flagdate == 1:
            raise forms.ValidationError('Invalid date:'+','.join(invaliddate))
        if flaguser == 1:
            raise forms.ValidationError(
                'Invalid Member Name:'+','.join(invaliduserlist))
        if flagbarcode == 1:
            raise forms.ValidationError(
                'Invalid i7 Barcode:'+','.join(invalidbarcodelist))
        if flagbarcode2 == 1:
            raise forms.ValidationError(
                'Invalid i5 Barcode:'+','.join(invalidbarcodelist2))
        if flagpolane == 1:
            raise forms.ValidationError(
                'Invalid portion of lane:'+','.join(invalidpolane))
        if flagseqid == 1:
            raise forms.ValidationError(
                ','.join(invalidseqid)+' is already existed in database')
        seqselfduplicate = SelfUniqueValidation(selfseqs)
        if len(seqselfduplicate) > 0:
            raise forms.ValidationError(
                'Duplicate Seq within this bulk entry:'+','.join(seqselfduplicate))
        if flagmachine == 1:
            raise forms.ValidationError(
                'Invalid seqmachine:'+','.join(invalidmachine))
        if flagtype == 1:
            raise forms.ValidationError(
                'Invalid read type:'+','.join(invalidtype))
        if flagexp == 1:
            raise forms.ValidationError(
                'Invalid experiment type:'+','.join(invalidexp))

        return '\n'.join(cleaneddata)


    def clean_group(self):
        gname = self.cleaned_data['group']
        if not Group.objects.filter(name=gname).exists():
            raise forms.ValidationError('Invalid Group Name!')
        return gname


class EncodeDataForm(forms.Form):
    encode_link = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 100, 'rows': 2}),
        required=True,
        )
    def clean_encode_link(self):
        cleaned_data = {}
        cleaned_data['samples'] = {}
        cleaned_data['libraries'] = {}
        cleaned_data['sequencings'] = {}

        url = self.cleaned_data['encode_link']
        print(url)
        headers = {'accept': 'application/json'}
        response = requests.get(url, headers=headers)
        biosample = response.json()
        graph = biosample['@graph']

        # First, biosamples.... ================================ 

        start = time.time()
        biosample_list = []
        sam_new_name = {}

        acceptable_species = ['human', 'mouse', 'rat', 'cattle']  
        cell_labels = ['cell line', 'primary cell', 'in vitro differentiated cells']
        tissue_labels = ['tissue']
        experiment_types = ['ATAC-seq','ChIP-seq','DNase-seq']

        for x in graph:
            for y in x['replicates']:
                biosample_list.append(str(y['library']['biosample']['accession']))
        print(set(biosample_list))
        for sample in set(biosample_list):
            this_url = "https://www.encodeproject.org/"+sample+"/?frame=embedded"
            response = requests.get(this_url, headers=headers)
            this_sample = response.json()
            species = str(this_sample['organism']['name'])
            sam_class = str(this_sample['biosample_ontology']['classification'])
            if species.lower() not in acceptable_species:
                raise forms.ValidationError('Incompatible species(' + species.lower()+') for sample: '+sample)

            if sam_class in cell_labels:
                this_sample_type = 'cultured cells'
            elif sam_class in tissue_labels:
                this_sample_type = 'tissue'
            else:
                raise forms.ValidationError('Incompatible sample type(' + species.lower()+') for sample: '+sample)

            sample_id=str(this_sample['biosample_ontology']['term_name'])+'_'+sample
            sam_new_name[sample] = sample_id
            sample_type=this_sample_type

            cleaned_data['samples'][sample_id] = {}
            cleaned_data['samples'][sample_id]['sample_type'] = this_sample_type
            cleaned_data['samples'][sample_id]['species'] = species.lower()
            cleaned_data['samples'][sample_id]['description'] = str(this_sample['summary'])
            cleaned_data['samples'][sample_id]['notes'] = 'pseudosample, data downloaded from ENCODE'

        end = time.time()
        print(end - start)

        # Next, libraries.... ================================
        
        start = time.time()
        library_list = []
        library_id_list = []
        lib_sam = {}
        for x in graph:
            for y in x['replicates']:
                library_list.append(str(y['@id']))

        #print(set(library_list))
        for library in set(library_list):
            this_url = "https://www.encodeproject.org/"+library+"/?frame=embedded"
            response = requests.get(this_url, headers=headers)
            this_library = response.json()
            #this_id=str(this_library['libraries'][0]['accession'])
            this_id=str(this_library['library']['accession'])
            assay_name = str(this_library['experiment']['assay_term_name'])
            if assay_name not in experiment_types:
                raise forms.ValidationError('Incompatible experiment type(' + assay_name+') for library: '+this_id)

            library_id_list.append(this_id)
            thissample = str(this_library['library']['biosample']['accession'])

            cleaned_data['libraries'][this_id] = {}
            cleaned_data['libraries'][this_id]['sampleinfo'] = sam_new_name[thissample]
            cleaned_data['libraries'][this_id]['notes'] = ';'.join(['pseudolibrary, ENCODE library downloaded from encodeproject.org','ENCODE accession:'+this_id])
            cleaned_data['libraries'][this_id]['experiment_type'] = assay_name
            cleaned_data['libraries'][this_id]['library_description'] = ' '.join(['ENCODE',str(this_library['experiment']['description'])])
        if len(set(library_id_list)) > 25:
            raise forms.ValidationError('Exceed maximum number (25) of libraries allowed in each request!')
        end = time.time()
        print(end - start)
        print(str(len(set(library_list))))
        print(str(len(set(library_id_list))))
        print(library_id_list)

        # Finally, sequencings... ================================

        start = time.time()
        seq_list = []
        for library in set(library_id_list):
            this_url = "https://www.encodeproject.org/"+library+"/?frame=embedded"
            response = requests.get(this_url, headers=headers)
            this_library = response.json()
            for rep in this_library['replicates']:
                this_rep_url = "https://www.encodeproject.org/"+rep+"/?frame=embedded"
                response = requests.get(this_rep_url, headers=headers)
                this_rep_library = response.json()
                try:
                    target = re.split('/|-',str(this_rep_library['experiment']['target']))[2]
                except:
                    target = ''

                this_uuid = str(this_rep_library['uuid'])
                seq_list.append(this_uuid)

                cleaned_data['sequencings'][this_uuid] = {}
                cleaned_data['sequencings'][this_uuid]['libraryinfo'] = library
                #cleaned_data['sequencings'][this_uuid]['notes'] = ';'.join(['ENCODE uuid:'+this_uuid,'ENCODE url for files info:'+this_rep_url])
                cleaned_data['sequencings'][this_uuid]['notes'] = 'ENCODE uuid:'+this_uuid
                cleaned_data['sequencings'][this_uuid]['default_label'] = '_'.join([cleaned_data['libraries'][library]['sampleinfo'],target]).strip('_')
        end = time.time()
        print(end - start)
        print(seq_list)

        print(cleaned_data)
        return(cleaned_data)


