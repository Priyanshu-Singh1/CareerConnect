from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def candidate_required(view_func):
    """
    Decorator for views that checks if the logged-in user is a Candidate.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to continue.")
            return redirect('accounts:login')
        if not hasattr(request.user, 'candidate_profile'):
            messages.error(request, "This page is accessible only to candidates.")
            return redirect('jobs:job_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def recruiter_required(view_func):
    """
    Decorator for views that checks if the logged-in user is a Recruiter.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in as a recruiter to continue.")
            return redirect('accounts:login')
        if not hasattr(request.user, 'recruiter_profile'):
            messages.error(request, "Access denied. This page is reserved for recruiters.")
            return redirect('jobs:job_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def verified_recruiter_required(view_func):
    """
    Decorator requiring the recruiter account to be verified before posting jobs.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'recruiter_profile'):
            raise PermissionDenied("Only recruiters can access this area.")
        if not request.user.recruiter_profile.is_verified:
            messages.warning(request, "Your recruiter account is pending verification by an administrator.")
            return redirect('dashboards:recruiter_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
