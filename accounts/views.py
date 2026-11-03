import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, HttpResponseForbidden, FileResponse
from django.conf import settings
from django.db.models import Count, Q

from .models import CandidateProfile, RecruiterProfile
from .forms import (
    CandidateRegistrationForm,
    RecruiterRegistrationForm,
    UserUpdateForm,
    CandidateProfileForm,
    RecruiterProfileForm
)
from .decorators import candidate_required, recruiter_required
from jobs.models import Job, SavedJob, JobCategory
from applications.models import Application, Notification


def register_choice(request):
    """View to select role for registration (Candidate vs Recruiter)."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'accounts/register_choice.html')


def register_candidate(request):
    """Register a new student/job-seeker candidate."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = CandidateRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to CareerConnect, {user.first_name}! Your candidate account is created.")
            return redirect('accounts:candidate_profile_edit')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CandidateRegistrationForm()

    return render(request, 'accounts/register_candidate.html', {'form': form})


def register_recruiter(request):
    """Register a new company recruiter."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RecruiterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome {user.first_name}! Your recruiter account has been registered.")
            return redirect('accounts:recruiter_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RecruiterRegistrationForm()

    return render(request, 'accounts/register_recruiter.html', {'form': form})


def login_view(request):
    """User authentication view with role-based redirection."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            
            # Next URL redirection
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm(request)

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Log out the current user and clear session."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('jobs:job_list')


@login_required
def dashboard_redirect(request):
    """Direct user to their appropriate role-based dashboard."""
    if hasattr(request.user, 'candidate_profile'):
        return redirect('accounts:candidate_dashboard')
    elif hasattr(request.user, 'recruiter_profile'):
        return redirect('accounts:recruiter_dashboard')
    elif request.user.is_staff or request.user.is_superuser:
        return redirect('admin:index')
    return redirect('jobs:job_list')


@candidate_required
def candidate_dashboard(request):
    """Candidate portal: recent applications, pipeline stats, saved jobs, recommended jobs."""
    candidate = request.user
    profile = candidate.candidate_profile
    completeness = profile.completeness_percentage()

    # Applications and status metrics
    applications = Application.objects.filter(candidate=candidate).select_related('job', 'job__company', 'interview').order_by('-applied_at')
    
    status_counts = {
        'total': applications.count(),
        'applied': applications.filter(status='Applied').count(),
        'under_review': applications.filter(status='Under Review').count(),
        'shortlisted': applications.filter(status='Shortlisted').count(),
        'interview': applications.filter(status='Interview Scheduled').count(),
        'selected': applications.filter(status='Selected').count(),
        'rejected': applications.filter(status='Rejected').count(),
    }

    # Saved jobs
    saved_jobs = SavedJob.objects.filter(candidate=candidate).select_related('job', 'job__company')[:6]

    # Smart Job Recommendations based on candidate's skills
    candidate_skills = profile.skills.all()
    if candidate_skills.exists():
        recommended_jobs = Job.objects.filter(
            is_active=True,
            skills_required__in=candidate_skills
        ).exclude(
            applications__candidate=candidate
        ).distinct()[:5]
    else:
        recommended_jobs = Job.objects.filter(is_active=True).exclude(
            applications__candidate=candidate
        )[:5]

    # Recently viewed jobs from Session (Demonstrating Session Management)
    viewed_job_ids = request.session.get('recently_viewed_jobs', [])
    recently_viewed = Job.objects.filter(id__in=viewed_job_ids, is_active=True)[:4]

    context = {
        'profile': profile,
        'completeness': completeness,
        'applications': applications[:5],
        'status_counts': status_counts,
        'saved_jobs': saved_jobs,
        'recommended_jobs': recommended_jobs,
        'recently_viewed': recently_viewed,
    }
    return render(request, 'dashboards/candidate_dashboard.html', context)


@recruiter_required
def recruiter_dashboard(request):
    """
    Recruiter portal: job listings, pipeline summary, recruitment analytics, conversion rates.
    """
    recruiter = request.user
    company = recruiter.recruiter_profile.company

    # All jobs posted by this recruiter
    jobs = Job.objects.filter(recruiter=recruiter).order_by('-created_at')
    active_jobs_count = jobs.filter(is_active=True).count()
    
    # Applications across all recruiter's jobs
    all_apps = Application.objects.filter(job__recruiter=recruiter)
    total_apps_count = all_apps.count()

    # Pipeline breakdown
    status_counts = {
        'applied': all_apps.filter(status='Applied').count(),
        'under_review': all_apps.filter(status='Under Review').count(),
        'shortlisted': all_apps.filter(status='Shortlisted').count(),
        'interview': all_apps.filter(status='Interview Scheduled').count(),
        'selected': all_apps.filter(status='Selected').count(),
        'rejected': all_apps.filter(status='Rejected').count(),
    }

    # Analytics: Conversion rate (Selected / Total Apps)
    conversion_rate = 0
    if total_apps_count > 0:
        conversion_rate = round((status_counts['selected'] / total_apps_count) * 100, 1)

    # Recent applicants
    recent_applications = all_apps.select_related('candidate', 'candidate__candidate_profile', 'job').order_by('-applied_at')[:8]

    context = {
        'company': company,
        'jobs_count': jobs.count(),
        'active_jobs_count': active_jobs_count,
        'total_apps_count': total_apps_count,
        'status_counts': status_counts,
        'conversion_rate': conversion_rate,
        'recent_applications': recent_applications,
        'recent_jobs': jobs[:5],
    }
    return render(request, 'dashboards/recruiter_dashboard.html', context)


@candidate_required
def candidate_profile_view(request):
    """View candidate profile in presentation format."""
    profile = request.user.candidate_profile
    return render(request, 'accounts/profile_candidate.html', {'profile': profile})


@candidate_required
def candidate_profile_edit(request):
    """Edit candidate profile: education, skills, resume upload, links."""
    profile = request.user.candidate_profile

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = CandidateProfileForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:candidate_profile_view')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = CandidateProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {
        'u_form': u_form,
        'p_form': p_form,
        'completeness': profile.completeness_percentage(),
    })


@recruiter_required
def recruiter_profile_edit(request):
    """Edit recruiter profile."""
    profile = request.user.recruiter_profile

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        r_form = RecruiterProfileForm(request.POST, instance=profile)

        if u_form.is_valid() and r_form.is_valid():
            u_form.save()
            r_form.save()
            messages.success(request, "Recruiter profile updated successfully!")
            return redirect('accounts:recruiter_dashboard')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        r_form = RecruiterProfileForm(instance=profile)

    return render(request, 'accounts/recruiter_profile_edit.html', {
        'u_form': u_form,
        'r_form': r_form,
    })


@login_required
def download_resume(request, user_id):
    """
    Secure Resume Access View.
    Ensures that only:
    1. The candidate who owns the resume,
    2. A recruiter who has received an application from this candidate, or
    3. An administrator / staff member
    can download/view the resume. Otherwise returns HTTP 403 Forbidden!
    """
    candidate_profile = get_object_or_404(CandidateProfile, user_id=user_id)
    
    if not candidate_profile.resume:
        raise Http404("No resume uploaded for this candidate.")

    # Authorization Check
    is_owner = (request.user.id == candidate_profile.user.id)
    is_staff = request.user.is_staff or request.user.is_superuser
    is_authorized_recruiter = False

    if hasattr(request.user, 'recruiter_profile'):
        # Check if candidate has applied to any job posted by this recruiter
        is_authorized_recruiter = Application.objects.filter(
            candidate=candidate_profile.user,
            job__recruiter=request.user
        ).exists()

    if not (is_owner or is_staff or is_authorized_recruiter):
        return HttpResponseForbidden("Access Denied: You are not authorized to view this candidate's resume.")

    file_path = candidate_profile.resume.path
    if not os.path.exists(file_path):
        raise Http404("Resume file not found on server.")

    return FileResponse(open(file_path, 'rb'), as_attachment=False, filename=os.path.basename(file_path))


@login_required
def notifications_view(request):
    """View all notifications for the current user."""
    notifications = request.user.notifications.all()
    # Mark all as read when viewed
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'accounts/notifications.html', {'notifications': notifications})
