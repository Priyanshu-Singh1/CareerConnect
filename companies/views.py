from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from .models import Company
from .forms import CompanyForm
from .services import CompanyOpeningsAPIService, KNOWN_COMPANIES_CATALOG
from accounts.decorators import recruiter_required


def company_list(request):
    """
    Browse all registered companies with search, active jobs count,
    and automatic API fetch integration when searching for any company.
    """
    query = request.GET.get('q', '').strip()
    industry = request.GET.get('industry', '').strip()
    auto_fetched = False

    companies = Company.objects.annotate(
        active_jobs_total=Count('jobs', filter=Q(jobs__is_active=True))
    )

    if query:
        filtered = companies.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
        # If no local company matches, automatically invoke the Company Openings API!
        if not filtered.exists():
            api_result = CompanyOpeningsAPIService.fetch_and_sync_company_openings(query)
            if api_result:
                auto_fetched = True
                messages.success(
                    request,
                    f"Found and imported {api_result['count']} active opening(s) for '{api_result['company'].name}' via Company Openings API! You can now view and apply for them."
                )
                # Re-query
                companies = Company.objects.annotate(
                    active_jobs_total=Count('jobs', filter=Q(jobs__is_active=True))
                )
                filtered = companies.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(location__icontains=query)
                )

        companies = filtered

    if industry:
        companies = companies.filter(industry__iexact=industry)

    # Industries for filter dropdown
    industries = Company.objects.values_list('industry', flat=True).distinct()

    paginator = Paginator(companies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Popular company suggestions for quick-fetching
    popular_companies = [
        'Google', 'Microsoft', 'Amazon', 'Meta', 'Netflix',
        'Apple', 'TCS', 'Infosys', 'Zomato', 'Swiggy', 'Spotify', 'Adobe'
    ]

    return render(request, 'companies/company_list.html', {
        'page_obj': page_obj,
        'query': query,
        'industry': industry,
        'industries': industries,
        'popular_companies': popular_companies,
        'auto_fetched': auto_fetched,
    })


def company_detail(request, slug):
    """Company profile detail page with active job openings."""
    company = get_object_or_404(Company, slug=slug)
    active_jobs = company.jobs.filter(is_active=True).order_by('-created_at')

    return render(request, 'companies/company_detail.html', {
        'company': company,
        'active_jobs': active_jobs,
    })


def fetch_company_api_view(request):
    """
    Dedicated view allowing users to enter ANY company name,
    fetch its live openings & details via Company Openings API, and apply immediately.
    """
    company_name = request.GET.get('company', '').strip()
    result = None

    if company_name:
        result = CompanyOpeningsAPIService.fetch_and_sync_company_openings(company_name)
        if result:
            messages.success(
                request,
                f"Successfully synced {result['count']} opening(s) for {result['company'].name}. Available to apply now!"
            )
        else:
            messages.error(request, f"Could not fetch openings for '{company_name}'. Please verify the name.")

    popular_companies = [
        'Google', 'Microsoft', 'Amazon', 'Meta', 'Netflix',
        'Spotify', 'TCS', 'Infosys', 'Zomato', 'Swiggy', 'Adobe', 'Apple'
    ]

    return render(request, 'companies/fetch_api.html', {
        'searched_company': company_name,
        'result': result,
        'popular_companies': popular_companies,
    })


def api_fetch_company_openings(request):
    """
    REST API endpoint: returns JSON list of company details and job openings.
    GET /companies/api/fetch/?company=<name>
    """
    company_query = request.GET.get('company', '').strip()
    if not company_query:
        return JsonResponse({'error': 'Please provide a company query parameter.'}, status=400)

    result = CompanyOpeningsAPIService.fetch_and_sync_company_openings(company_query)
    if not result:
        return JsonResponse({'error': f'Unable to fetch openings for {company_query}'}, status=404)

    jobs_data = []
    for job in result['jobs']:
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'job_type': job.job_type,
            'work_mode': job.work_mode,
            'experience_level': job.experience_level,
            'location': job.location,
            'salary': job.salary_display,
            'deadline': str(job.deadline),
            'url': f"/jobs/{job.id}/{job.slug}/",
            'apply_url': f"/applications/apply/{job.id}/",
            'skills': [s.name for s in job.skills_required.all()],
        })

    return JsonResponse({
        'status': 'success',
        'company': {
            'name': result['company'].name,
            'slug': result['company'].slug,
            'industry': result['company'].industry,
            'location': result['company'].location,
            'website': result['company'].website,
            'company_size': result['company'].company_size,
            'description': result['company'].description,
            'url': f"/companies/{result['company'].slug}/",
        },
        'openings_count': result['count'],
        'openings': jobs_data,
    })


@recruiter_required
def company_edit(request):
    """Recruiter edit view for their associated company profile."""
    recruiter_profile = request.user.recruiter_profile
    company = recruiter_profile.company

    if not company:
        messages.warning(request, "Please create your company profile first.")
        company = Company()

    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save()
            if not recruiter_profile.company:
                recruiter_profile.company = company
                recruiter_profile.save()
            messages.success(request, "Company details updated successfully!")
            return redirect('companies:company_detail', slug=company.slug)
        else:
            messages.error(request, "Please fix the errors in the company form.")
    else:
        form = CompanyForm(instance=company)

    return render(request, 'companies/company_form.html', {'form': form, 'company': company})
