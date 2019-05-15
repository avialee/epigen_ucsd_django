from django.shortcuts import redirect,render,get_object_or_404
from epigen_ucsd_django.models import CollaboratorPersonInfo,Person_Index
from django.db import transaction
from .forms import UserForm,CollaboratorPersonForm,GroupForm,GroupCreateForm,PersonIndexForm,PersonIndexCreateForm
from django.contrib import messages
from django.contrib.auth.models import User,Group
from django.http import JsonResponse
from django.db.models import Q
from epigen_ucsd_django.shared import is_member

# Create your views here.


def CollaboratorListView(request):
    collabs = CollaboratorPersonInfo.objects.all().select_related('person_id').prefetch_related('person_id__groups','person_index_set')
    collabs_list = collabs.values(\
        'person_id__groups__name','person_id__username',\
        'person_id__first_name','person_id__last_name',\
        'person_id__email','cell_phone','email','role'\
        ,'person_index__index_name')

    context = {
        'collab_list':collabs_list,
    }
    return render(request, 'manager_app/collaboratorlist.html', context=context)   

@transaction.atomic
def CollaboratorCreateView(request):
    user_form = UserForm(request.POST or None)
    profile_form = CollaboratorPersonForm(request.POST or None)
    group_form = GroupForm(request.POST or None)
    group_create_form = GroupCreateForm(request.POST or None)
    person_index_form = PersonIndexForm(request.POST or None)

    if request.method=='POST' and 'profile_save' in request.POST:
        if user_form.is_valid() and profile_form.is_valid() and group_form.is_valid() and person_index_form.is_valid():
            this_user = user_form.save()
            this_profile = profile_form.save(commit=False)
            this_profile.person_id = this_user
            this_profile.save()
            this_group = Group.objects.get(name=group_form.clean_name()) 
            this_group.user_set.add(this_user)
            this_person_index = person_index_form.save(commit=False)
            this_person_index.person = this_profile
            this_person_index.save()

            messages.success(request,'Your profile was successfully updated!')
            return redirect('manager_app:collab_list')
        else:
            messages.error(request,'Please correct the error below.')
    # elif request.method=='POST' and 'group_save' in request.POST:
    #     if group_create_form.is_valid():
    #         group_create_form.save()
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'group_form':group_form,
        'group_create_form':group_create_form,
        'person_index_form':person_index_form,
    }
    if is_member(request.user,'manager'):
        return render(request, 'manager_app/profile_add.html', context)
    else:
        return render(request, 'manager_app/profile_add_nogroup.html', context)

@transaction.atomic
def AjaxGroupCreateView(request):
    data = {}
    if request.method == 'POST':
        group_create_form = GroupCreateForm(request.POST)
        if group_create_form.is_valid():
            groupname = request.POST.get('name')
            thisgroup = Group(name=groupname)
            thisgroup.save()
            data['ok'] = 1;
        else:
            data['error'] = str(group_create_form.errors);
            print(data['error'])
    return JsonResponse(data)

def load_groups(request):
    q = request.GET.get('term', '')
    gs = Group.objects.exclude(name__in=['bioinformatics','wetlab','manager']).filter(
        name__icontains=q).values('name')[:20]
    results = []
    for g in gs:
        gsearch = {}
        gsearch['id'] = g['name']
        gsearch['label'] = g['name']
        gsearch['value'] = g['name']
        results.append(gsearch)
    return JsonResponse(results, safe=False)

@transaction.atomic
def IndexCreateView(request):
    person_index_form = PersonIndexCreateForm(request.POST or None)
    if request.method == 'POST':
        post = request.POST.copy()
        obj = get_object_or_404(CollaboratorPersonInfo, id=post['person'].split(':')[0])
        post['person'] = obj.id
        person_index_form = PersonIndexCreateForm(post)
        if person_index_form.is_valid():
            person_index_form.save()
            return redirect('manager_app:collab_list')
    context = {
        'person_index_form':person_index_form,
    }
    return render(request, 'manager_app/index_add.html', context)
def load_collabs(request):
    q = request.GET.get('term', '')
    #collabusers = User.objects.filter(Q(first_name__icontains = q)|Q(last_name__icontains = q)).values('first_name','last_name')[:20]
    collabusers = User.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q))
    for f in Group.objects.filter(name__icontains=q):
        collabusers = collabusers | f.user_set.all()
    results = []
    for u in collabusers:
        uu = {}
        uu['id'] = str(u.collaboratorpersoninfo_set.first().id)+': '+u.first_name+' '+u.last_name + \
            '('+u.groups.all().first().name+')'
        uu['label'] = str(u.collaboratorpersoninfo_set.first().id)+': '+u.first_name+' ' + \
            u.last_name+'('+u.groups.all().first().name+')'
        uu['value'] = str(u.collaboratorpersoninfo_set.first().id)+': '+u.first_name+' ' + \
            u.last_name+'('+u.groups.all().first().name+')'
        results.append(uu)
    return JsonResponse(results, safe=False)