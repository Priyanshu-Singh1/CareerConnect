def user_role_context(request):
    """
    Context processor making user role helpers and profile instances available in all templates.
    """
    context = {
        'is_candidate': False,
        'is_recruiter': False,
        'is_verified_recruiter': False,
        'candidate_profile': None,
        'recruiter_profile': None,
        'unread_notifications_count': 0,
        'saved_jobs_count': 0,
        'my_applications_count': 0,
    }

    if request.user.is_authenticated:
        # Check Candidate Profile
        if hasattr(request.user, 'candidate_profile'):
            context['is_candidate'] = True
            context['candidate_profile'] = request.user.candidate_profile
            context['saved_jobs_count'] = request.user.saved_jobs.count()
            context['my_applications_count'] = request.user.applications.count()

        # Check Recruiter Profile
        if hasattr(request.user, 'recruiter_profile'):
            context['is_recruiter'] = True
            context['recruiter_profile'] = request.user.recruiter_profile
            context['is_verified_recruiter'] = request.user.recruiter_profile.is_verified

        # Notifications
        if hasattr(request.user, 'notifications'):
            context['unread_notifications_count'] = request.user.notifications.filter(is_read=False).count()

    return context
