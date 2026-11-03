from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('my/', views.candidate_applications, name='candidate_applications'),
    path('withdraw/<int:application_id>/', views.withdraw_application, name='withdraw_application'),
    path('manage/', views.recruiter_applicants, name='recruiter_applicants'),
    path('manage/<int:job_id>/', views.recruiter_applicants, name='recruiter_job_applicants'),
    path('pipeline/<int:job_id>/', views.recruiter_pipeline, name='recruiter_pipeline'),
    path('status/<int:application_id>/', views.update_application_status, name='update_status'),
    path('schedule/<int:application_id>/', views.schedule_interview, name='schedule_interview'),
    path('interview/<int:interview_id>/', views.interview_detail, name='interview_detail'),
]
