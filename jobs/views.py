from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponseForbidden

from .models import Job, JobCategory, Skill, SavedJob, JobReport
from .forms import JobForm, JobReportForm
from accounts.decorators import recruiter_required, candidate_required, verified_recruiter_required
from applications.models import Application
from companies.models import Company


def home_view(request):
    """Platform landing page with hero search, key stats, top categories, and latest jobs."""
    # Key platform metrics
    total_jobs = Job.objects.filter(is_active=True).count()
    total_companies = Company.objects.count()
    total_categories = JobCategory.objects.count()
    
    # Top categories with job count
    categories = JobCategory.objects.annotate(
        jobs_count=Count('jobs', filter=Q(jobs__is_active=True))
    ).order_by('-jobs_count')[:8]

    # Latest job listings
    featured_jobs = Job.objects.filter(
        is_active=True,
        deadline__gte=timezone.now().date()
    ).select_related('company', 'category').prefetch_related('skills_required').order_by('-created_at')[:6]

    return render(request, 'jobs/home.html', {
        'total_jobs': total_jobs,
        'total_companies': total_companies,
        'total_categories': total_categories,
        'categories': categories,
        'featured_jobs': featured_jobs,
    })


def job_list(request):
    """
    Job and Internship listings view with multi-factor search, filtering, sorting, and pagination.
    """
    jobs = Job.objects.filter(is_active=True).select_related('company', 'category').prefetch_related('skills_required')

    # GET filter parameters
    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    work_mode = request.GET.get('work_mode', '').strip()
    experience = request.GET.get('experience', '').strip()
    location = request.GET.get('location', '').strip()
    sort_by = request.GET.get('sort', 'newest')

    # Keyword search across title, description, company name, skills
    auto_fetched = False
    if q:
        filtered_jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(company__name__icontains=q) |
            Q(skills_required__name__icontains=q)
        ).distinct()

        # If no local jobs match the search query, check Company Openings API if requested or known company!
        from companies.services import CompanyOpeningsAPIService
        should_fetch = request.GET.get('fetch') == '1' or CompanyOpeningsAPIService.is_known_company(q)

        if not filtered_jobs.exists() and should_fetch:
            api_result = CompanyOpeningsAPIService.fetch_and_sync_company_openings(q)
            if api_result:
                auto_fetched = True
                messages.success(
                    request,
                    f"Found and imported {api_result['count']} active opening(s) for '{api_result['company'].name}' via Company Openings API! You can now explore and apply."
                )
                # Re-query active jobs
                jobs = Job.objects.filter(is_active=True).select_related('company', 'category').prefetch_related('skills_required')
                filtered_jobs = jobs.filter(
                    Q(title__icontains=q) |
                    Q(description__icontains=q) |
                    Q(company__name__icontains=q) |
                    Q(skills_required__name__icontains=q)
                ).distinct()

        jobs = filtered_jobs

    if category_slug:
        jobs = jobs.filter(category__slug=category_slug)

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    if work_mode:
        jobs = jobs.filter(work_mode=work_mode)

    if experience:
        jobs = jobs.filter(experience_level=experience)

    if location:
        jobs = jobs.filter(location__icontains=location)

    # Sorting options
    if sort_by == 'deadline':
        jobs = jobs.order_by('deadline')
    elif sort_by == 'salary_high':
        jobs = jobs.order_by('-salary_max', '-salary_min')
    else:  # Default 'newest'
        jobs = jobs.order_by('-created_at')

    # Total matching count
    results_count = jobs.count()

    # Pagination: 10 per page
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter dropdown options
    categories = JobCategory.objects.all()
    job_types = [c[0] for c in Job.JOB_TYPE_CHOICES]
    work_modes = [c[0] for c in Job.WORK_MODE_CHOICES]
    experiences = [c[0] for c in Job.EXPERIENCE_CHOICES]

    # Preserve GET parameters in pagination
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_query = query_params.urlencode()

    return render(request, 'jobs/job_list.html', {
        'page_obj': page_obj,
        'results_count': results_count,
        'categories': categories,
        'job_types': job_types,
        'work_modes': work_modes,
        'experiences': experiences,
        'current_q': q,
        'current_category': category_slug,
        'current_job_type': job_type,
        'current_work_mode': work_mode,
        'current_experience': experience,
        'current_location': location,
        'current_sort': sort_by,
        'pagination_query': pagination_query,
        'auto_fetched': auto_fetched,
        'popular_companies': ['Google', 'Microsoft', 'Amazon', 'Meta', 'Netflix', 'TCS', 'Infosys', 'Zomato', 'Swiggy', 'Spotify', 'Apple', 'Adobe'],
    })


def job_detail(request, pk, slug=None):
    """
    Detailed job view with:
    - Smart Skill Matching calculation
    - Application status check
    - Wishlist check
    - Session tracking for recently viewed jobs
    """
    job = get_object_or_404(Job.objects.select_related('company', 'category', 'recruiter').prefetch_related('skills_required'), pk=pk)

    # Increment view count
    Job.objects.filter(pk=job.pk).update(views_count=job.views_count + 1)

    # Track in Session for Candidates
    if 'recently_viewed_jobs' not in request.session:
        request.session['recently_viewed_jobs'] = []
    viewed = request.session['recently_viewed_jobs']
    if job.id not in viewed:
        viewed.insert(0, job.id)
        request.session['recently_viewed_jobs'] = viewed[:8]
        request.session.modified = True

    # Check if user already applied
    user_application = None
    is_saved = False
    match_score = None
    matched_skills = []
    missing_skills = []

    if request.user.is_authenticated:
        if hasattr(request.user, 'candidate_profile'):
            user_application = Application.objects.filter(job=job, candidate=request.user).first()
            is_saved = SavedJob.objects.filter(candidate=request.user, job=job).exists()

            # Smart Skill Matching Algorithm
            required_skills = set(job.skills_required.all())
            candidate_skills = set(request.user.candidate_profile.skills.all())

            if required_skills:
                matched_set = required_skills.intersection(candidate_skills)
                matched_skills = list(matched_set)
                missing_skills = list(required_skills - matched_set)
                match_score = int(round((len(matched_skills) / len(required_skills)) * 100))
            else:
                match_score = 100

    report_form = JobReportForm()

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'user_application': user_application,
        'is_saved': is_saved,
        'match_score': match_score,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'report_form': report_form,
    })


@recruiter_required
@verified_recruiter_required
def job_create(request):
    """Recruiter posts a new job opening."""
    recruiter_profile = request.user.recruiter_profile
    if not recruiter_profile.company:
        messages.warning(request, "Please set up your company profile before posting a job.")
        return redirect('companies:company_edit')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.company = recruiter_profile.company
            job.save()
            form.save_m2m()  # Save skills ManyToMany
            messages.success(request, f"Job '{job.title}' published successfully!")
            return redirect('jobs:job_detail', pk=job.pk, slug=job.slug)
        else:
            messages.error(request, "Please fix the errors in the job listing form.")
    else:
        form = JobForm(initial={'is_active': True})

    return render(request, 'jobs/job_form.html', {
        'form': form,
        'action_title': 'Post a New Job Opening',
        'button_text': 'Publish Job Listing',
    })


@recruiter_required
def job_edit(request, pk):
    """Recruiter edits their existing job post."""
    job = get_object_or_404(Job, pk=pk)
    if job.recruiter != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to edit this job posting.")

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job '{job.title}' updated successfully.")
            return redirect('jobs:job_detail', pk=job.pk, slug=job.slug)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/job_form.html', {
        'form': form,
        'job': job,
        'action_title': f"Edit: {job.title}",
        'button_text': 'Save Changes',
    })


@recruiter_required
def job_toggle_status(request, pk):
    """Toggle job active/closed state."""
    job = get_object_or_404(Job, pk=pk)
    if job.recruiter != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Permission denied.")

    job.is_active = not job.is_active
    job.save()
    status_str = "reopened and published" if job.is_active else "closed to new applications"
    messages.info(request, f"Job '{job.title}' is now {status_str}.")
    return redirect('dashboards:recruiter_dashboard' if 'dashboard' in request.META.get('HTTP_REFERER', '') else 'jobs:job_detail', pk=job.pk, slug=job.slug)


@recruiter_required
def job_delete(request, pk):
    """Delete a job listing."""
    job = get_object_or_404(Job, pk=pk)
    if job.recruiter != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Permission denied.")

    if request.method == 'POST':
        title = job.title
        job.delete()
        messages.success(request, f"Job '{title}' was permanently deleted.")
        return redirect('accounts:recruiter_dashboard')

    return render(request, 'jobs/job_confirm_delete.html', {'job': job})


@candidate_required
def toggle_save_job(request, pk):
    """Bookmark / Wishlist toggle for candidates."""
    job = get_object_or_404(Job, pk=pk)
    saved_obj = SavedJob.objects.filter(candidate=request.user, job=job).first()

    if saved_obj:
        saved_obj.delete()
        messages.info(request, f"Removed '{job.title}' from your saved wishlist.")
    else:
        SavedJob.objects.create(candidate=request.user, job=job)
        messages.success(request, f"Added '{job.title}' to your saved wishlist.")

    return redirect(request.META.get('HTTP_REFERER', 'jobs:job_detail'), pk=job.pk, slug=job.slug)


@candidate_required
def saved_jobs_list(request):
    """List of all jobs saved by the logged-in candidate."""
    saved_items = SavedJob.objects.filter(candidate=request.user).select_related('job', 'job__company').order_by('-created_at')
    return render(request, 'jobs/saved_jobs.html', {'saved_items': saved_items})


@login_required
def report_job(request, pk):
    """Report an inappropriate or fraudulent job post."""
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        form = JobReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.job = job
            report.reported_by = request.user
            report.save()
            messages.success(request, "Thank you. Your report has been submitted to portal administrators for review.")
        else:
            messages.error(request, "Unable to submit report. Please check the fields.")
    return redirect('jobs:job_detail', pk=job.pk, slug=job.slug)
