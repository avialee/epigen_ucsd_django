from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'setqc_app'
urlpatterns = [

    path('', views.UserSetQCView, name='index'),
    path('mysets/', views.UserSetQCView, name='usersetqcs'),
    path('allsets/', views.AllSetQCView, name='allsetqcs'),
    path('adds/', views.SetQCCreateView, name='setqc_add'),
    path('<int:setqc_pk>/delete/', views.SetQCDeleteView, name='setqc_delete'),
    path('<int:setqc_pk>/update/',views.SetQCUpdateView, name='setqc_update'),
    path('<int:setqc_pk>/getmynotes/',views.GetNotesView, name='setqc_getnotes'),
    path('<int:setqc_pk>/runsetqc/',views.RunSetQC, name='runsetqc'),
    path('<int:setqc_pk>/',views.SetQCDetailView, name='setqc_detail'),
    path('myreports/', views.CollaboratorSetQCView, name='collaboratorsetqcs'),
    path('<int:setqc_pk>/details/',views.CollaboratorSetQCDetailView, name='setqc_collaboratordetail'),
    path('<int:setqc_pk>/getnotes/',views.CollaboratorGetNotesView, name='setqc_collaboratorgetnotes'),

]
