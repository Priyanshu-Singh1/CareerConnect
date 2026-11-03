from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('browse/', views.job_list, name='job_list'),
    path('post/', views.job_create, name='job_create'),
    path('saved/', views.saved_jobs_list, name='saved_jobs'),
    path('<int:pk>/<slug:slug>/', views.job_detail, name='job_detail'),
    path('<int:pk>/', views.job_detail, name='job_detail_short'),
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('<int:pk>/toggle-status/', views.job_toggle_status, name='job_toggle_status'),
    path('<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('<int:pk>/save/', views.toggle_save_job, name='toggle_save_job'),
    path('<int:pk>/report/', views.report_job, name='report_job'),
]
