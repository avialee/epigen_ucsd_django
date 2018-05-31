from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'nextseq_app'
urlpatterns = [
    #path('', views.IndexView.as_view(),name='index'),
    #path('', views.IndexView,name='index'),
    path('', views.IndexView,name='index'),
    path('samples/', views.UserSamplesView,name='usersamples'),
    path('home/', views.HomeView.as_view(),name='home'),
    path('home/samples/', views.AllSamplesView,name='allsamples'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    #path('<int:pk>/', views.RunDetailView.as_view(), name='rundetail'),
    #path('<int:pk>/', views.RunDetailView.as_view(), name='rundetail'),
    path('<int:pk>/', views.RunDetailView2.as_view(), name='rundetail'),
    #path('add/', views.RunCreateView2.as_view(), name='run_add'),
    path('adds/', views.RunCreateView4, name='runandsample_add'),
    path('addsinbulky/', views.RunCreateView6, name='runandsample_add_inbulky'),
    #path('<int:pk>/update/', views.RunUpdateView.as_view(), name='run_update'),
    path('<slug:username>/<int:run_pk>/update/', views.RunUpdateView2, name='run_update'),
    #path('<int:pk>/delete/', views.RunDeleteView.as_view(), name='run_delete'),
    path('<int:run_pk>/delete2/', views.RunDeleteView2, name='run_delete2'),
    path('<int:run_pk>/sample/add/', views.SampleCreateView, name='sample_add'),
    path('<int:run_pk>/samples/add/', views.SamplesBulkCreateView, name='samples_bulkadd'),
    path('<int:run_pk>/samples/delete/', views.SamplesDeleteView, name='samples_delete'),
    path('<int:run_pk>/samplesheetcreate/', views.SampleSheetCreateView, name='samplesheet_create'),
    
]
