from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import CandidateProfile, RecruiterProfile


class CandidateProfileInline(admin.StackedInline):
    model = CandidateProfile
    can_delete = False
    verbose_name_plural = 'Candidate Profile'
    filter_horizontal = ('skills',)


class RecruiterProfileInline(admin.StackedInline):
    model = RecruiterProfile
    can_delete = False
    verbose_name_plural = 'Recruiter Profile'


# Extend default UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (CandidateProfileInline, RecruiterProfileInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')

    def get_role(self, obj):
        if hasattr(obj, 'candidate_profile'):
            return "Candidate"
        elif hasattr(obj, 'recruiter_profile'):
            return "Recruiter"
        elif obj.is_superuser:
            return "Superuser"
        return "Standard User"
    get_role.short_description = 'Portal Role'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'phone', 'location', 'get_completeness', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'headline', 'location')
    filter_horizontal = ('skills',)

    def get_completeness(self, obj):
        return f"{obj.completeness_percentage()}%"
    get_completeness.short_description = 'Profile Completeness'


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'designation', 'phone', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'company')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'designation', 'company__name')
    actions = ['approve_recruiters', 'suspend_recruiters']

    @admin.action(description="Approve selected recruiters (Grant posting rights)")
    def approve_recruiters(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description="Suspend selected recruiters (Revoke posting rights)")
    def suspend_recruiters(self, request, queryset):
        queryset.update(is_verified=False)
