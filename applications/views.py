from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseForbidden, Http404
from django.db.models import Count, Q

from .models import Application, Interview, Notification
from .forms import ApplicationForm, ApplicationStatusUpdateForm, InterviewScheduleForm
from jobs.models import Job
from accounts.decorators import candidate_required, recruiter_required


@candidate_required
def apply_job(request, job_id):
    """
    Apply for a job with online form, resume validation, duplicate checks, and deadline enforcement.
    Demonstrates Unit IV (Forms, CSRF, POST-Redirect-GET) & Unit V (ORM, UniqueConstraint).
    """
    job = get_object_or_404(Job, pk=job_id)

    # 1. Eligibility Check: Active and not expired
    if not job.can_apply:
        messages.error(request, "This opportunity is closed or past its application deadline.")
        return redirect('jobs:job_detail', pk=job.pk, slug=job.slug)

    # 2. Duplicate Application Prevention
    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, "You have already submitted an application for this position.")
        return redirect('applications:candidate_applications')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES, candidate=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.status = 'Applied'
            application.save()

            # Create notification for recruiter
            Notification.objects.create(
                recipient=job.recruiter,
                title="New Applicant Received",
                message=f"{request.user.get_full_name() or request.user.username} applied for '{job.title}'.",
                link=f"/applications/manage/{job.id}/"
            )

            # Send Email Confirmation (Console Backend for syllabus)
            try:
                send_mail(
                    subject=f"Application Received: {job.title} at {job.company.name}",
                    message=(
                        f"Dear {request.user.first_name},\n\n"
                        f"Thank you for applying for '{job.title}' at {job.company.name}.\n"
                        f"Your application has been received and is now in 'Applied' status.\n\n"
                        f"You can track real-time progress on your CareerConnect dashboard.\n\n"
                        f"Best regards,\nCareerConnect Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=True
                )
            except Exception:
                pass

            messages.success(request, f"Your application for '{job.title}' was submitted successfully!")
            return redirect('applications:candidate_applications')
        else:
            messages.error(request, "Please check the form for any required fields.")
    else:
        form = ApplicationForm(candidate=request.user)

    return render(request, 'applications/apply_form.html', {
        'form': form,
        'job': job,
        'has_profile_resume': bool(request.user.candidate_profile.resume),
    })


@candidate_required
def candidate_applications(request):
    """
    Application Tracking View for Candidates.
    Shows real-time status: Applied, Under Review, Shortlisted, Interview Scheduled, Selected, Rejected, Withdrawn.
    """
    status_filter = request.GET.get('status', 'all')
    applications = Application.objects.filter(candidate=request.user).select_related(
        'job', 'job__company', 'interview'
    ).order_by('-applied_at')

    if status_filter != 'all':
        applications = applications.filter(status=status_filter)

    # Status counts for tab navigation
    all_apps = Application.objects.filter(candidate=request.user)
    counts = {
        'all': all_apps.count(),
        'Applied': all_apps.filter(status='Applied').count(),
        'Under Review': all_apps.filter(status='Under Review').count(),
        'Shortlisted': all_apps.filter(status='Shortlisted').count(),
        'Interview Scheduled': all_apps.filter(status='Interview Scheduled').count(),
        'Selected': all_apps.filter(status='Selected').count(),
        'Rejected': all_apps.filter(status='Rejected').count(),
        'Withdrawn': all_apps.filter(status='Withdrawn').count(),
    }

    return render(request, 'applications/candidate_applications.html', {
        'applications': applications,
        'current_status': status_filter,
        'counts': counts,
    })


@candidate_required
def withdraw_application(request, application_id):
    """Candidate withdraws application when permitted."""
    application = get_object_or_404(Application, pk=application_id, candidate=request.user)

    if not application.can_withdraw:
        messages.error(request, "This application cannot be withdrawn at its current stage.")
        return redirect('applications:candidate_applications')

    if request.method == 'POST':
        application.status = 'Withdrawn'
        application.save()

        # Notify recruiter
        Notification.objects.create(
            recipient=application.job.recruiter,
            title="Application Withdrawn",
            message=f"{request.user.get_full_name()} has withdrawn their application for '{application.job.title}'.",
            link=f"/applications/manage/{application.job.id}/"
        )

        messages.info(request, f"You have withdrawn your application for '{application.job.title}'.")
        return redirect('applications:candidate_applications')

    return render(request, 'applications/withdraw_confirm.html', {'application': application})


@recruiter_required
def recruiter_applicants(request, job_id=None):
    """
    Recruiter applicant management list with filtering, skill match score, and status updater.
    """
    recruiter = request.user
    selected_job = None

    if job_id:
        selected_job = get_object_or_404(Job, pk=job_id, recruiter=recruiter)
        applications = Application.objects.filter(job=selected_job)
    else:
        applications = Application.objects.filter(job__recruiter=recruiter)

    # Status filter
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        applications = applications.filter(status=status_filter)

    applications = applications.select_related(
        'job', 'candidate', 'candidate__candidate_profile', 'interview'
    ).prefetch_related('candidate__candidate_profile__skills', 'job__skills_required').order_by('-applied_at')

    # Recruiter's jobs for the job switcher dropdown
    recruiter_jobs = Job.objects.filter(recruiter=recruiter).order_by('-created_at')

    # Calculate match score for each applicant
    applicant_data = []
    for app in applications:
        score, matched = app.job.skill_match_score(app.candidate)
        applicant_data.append({
            'application': app,
            'match_score': score,
            'matched_skills': matched,
        })

    return render(request, 'applications/recruiter_applicants.html', {
        'applicant_data': applicant_data,
        'selected_job': selected_job,
        'recruiter_jobs': recruiter_jobs,
        'current_status': status_filter,
        'status_choices': Application.STATUS_CHOICES,
    })


@recruiter_required
def recruiter_pipeline(request, job_id):
    """
    Structured Application Pipeline (Kanban / Stage View) for a job opening.
    Organizes applicants across columns: Applied, Under Review, Shortlisted, Interview Scheduled, Selected, Rejected.
    """
    recruiter = request.user
    job = get_object_or_404(Job, pk=job_id, recruiter=recruiter)
    
    all_apps = Application.objects.filter(job=job).select_related(
        'candidate', 'candidate__candidate_profile', 'interview'
    ).prefetch_related('candidate__candidate_profile__skills', 'job__skills_required')

    pipeline_stages = {
        'Applied': [],
        'Under Review': [],
        'Shortlisted': [],
        'Interview Scheduled': [],
        'Selected': [],
        'Rejected': [],
    }

    for app in all_apps:
        score, _ = job.skill_match_score(app.candidate)
        app.calculated_match_score = score
        if app.status in pipeline_stages:
            pipeline_stages[app.status].append(app)

    return render(request, 'applications/recruiter_pipeline.html', {
        'job': job,
        'pipeline_stages': pipeline_stages,
        'total_applicants': all_apps.count(),
    })


@recruiter_required
def update_application_status(request, application_id):
    """
    Recruiter updates applicant status and internal notes.
    Sends notification and email update to the candidate.
    """
    application = get_object_or_404(Application, pk=application_id)
    if application.job.recruiter != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Not authorized.")

    if request.method == 'POST':
        new_status = request.POST.get('status')
        recruiter_notes = request.POST.get('recruiter_notes', '')

        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.recruiter_notes = recruiter_notes
            application.save()

            # Create candidate notification
            Notification.objects.create(
                recipient=application.candidate,
                title=f"Application Status Updated: {new_status}",
                message=f"Your application status for '{application.job.title}' is now '{new_status}'.",
                link="/applications/my/"
            )

            # Send Email Notification
            try:
                send_mail(
                    subject=f"Update on your application for {application.job.title}",
                    message=(
                        f"Hello {application.candidate.first_name},\n\n"
                        f"The status of your application for '{application.job.title}' at {application.job.company.name} "
                        f"has been updated to: {new_status}.\n\n"
                        f"Log in to CareerConnect to review more details.\n\n"
                        f"Best regards,\nCareerConnect Portal"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.candidate.email],
                    fail_silently=True
                )
            except Exception:
                pass

            messages.success(request, f"Updated application status for {application.candidate.get_full_name()} to '{new_status}'.")

            # If changed to 'Interview Scheduled', redirect to scheduling form
            if new_status == 'Interview Scheduled':
                return redirect('applications:schedule_interview', application_id=application.id)

    return redirect(request.META.get('HTTP_REFERER', 'applications:recruiter_applicants'))


@recruiter_required
def schedule_interview(request, application_id):
    """Schedule an interview for shortlisted candidate."""
    application = get_object_or_404(Application, pk=application_id)
    if application.job.recruiter != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Not authorized.")

    interview, created = Interview.objects.get_or_create(
        application=application,
        defaults={
            'scheduled_date': timezone.now().date(),
            'scheduled_time': '10:00:00',
            'mode': 'Online Video Call',
            'location_or_link': 'https://meet.google.com/sample-interview',
        }
    )

    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST, instance=interview)
        if form.is_valid():
            interview = form.save()
            application.status = 'Interview Scheduled'
            application.save()

            # Notify Candidate
            Notification.objects.create(
                recipient=application.candidate,
                title="Interview Scheduled!",
                message=f"An interview for '{application.job.title}' is scheduled on {interview.scheduled_date} at {interview.scheduled_time}.",
                link=f"/applications/interview/{interview.id}/"
            )

            # Send Email
            try:
                send_mail(
                    subject=f"Interview Scheduled: {application.job.title}",
                    message=(
                        f"Dear {application.candidate.first_name},\n\n"
                        f"Congratulations! An interview has been scheduled for '{application.job.title}'.\n\n"
                        f"Date: {interview.scheduled_date}\n"
                        f"Time: {interview.scheduled_time}\n"
                        f"Mode: {interview.mode}\n"
                        f"Location/Link: {interview.location_or_link}\n"
                        f"Instructions: {interview.instructions}\n\n"
                        f"Good luck!\nCareerConnect Portal"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.candidate.email],
                    fail_silently=True
                )
            except Exception:
                pass

            messages.success(request, f"Interview successfully scheduled for {application.candidate.get_full_name()}!")
            return redirect('applications:recruiter_pipeline', job_id=application.job.id)
    else:
        form = InterviewScheduleForm(instance=interview)

    return render(request, 'applications/schedule_interview.html', {
        'form': form,
        'application': application,
    })


@login_required
def interview_detail(request, interview_id):
    """View interview schedule details (Candidate or Recruiter)."""
    interview = get_object_or_404(Interview, pk=interview_id)
    application = interview.application

    # Security check: must be the candidate or job recruiter or admin
    is_candidate = (request.user == application.candidate)
    is_recruiter = (request.user == application.job.recruiter)
    is_staff = request.user.is_staff or request.user.is_superuser

    if not (is_candidate or is_recruiter or is_staff):
        return HttpResponseForbidden("You do not have permission to view this interview.")

    return render(request, 'applications/interview_detail.html', {
        'interview': interview,
        'application': application,
        'is_recruiter': is_recruiter,
    })
