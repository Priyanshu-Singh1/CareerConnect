from django.contrib import admin
from .models import JobCategory, Skill, Job, SavedJob, JobReport


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'job_type', 'work_mode', 'deadline', 'is_active', 'created_at')
    list_filter = ('job_type', 'work_mode', 'experience_level', 'is_active', 'category', 'company')
    search_fields = ('title', 'description', 'location', 'company__name')
    filter_horizontal = ('skills_required',)
    actions = ['activate_jobs', 'deactivate_jobs']

    @admin.action(description="Activate selected job listings")
    def activate_jobs(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate / Close selected job listings")
    def deactivate_jobs(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('candidate__username', 'job__title')


@admin.register(JobReport)
class JobReportAdmin(admin.ModelAdmin):
    list_display = ('job', 'reported_by', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('job__title', 'reported_by__username', 'reason', 'details')
    actions = ['mark_as_reviewed', 'mark_as_dismissed']

    @admin.action(description="Mark selected reports as Reviewed")
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='Reviewed')

    @admin.action(description="Mark selected reports as Dismissed")
    def mark_as_dismissed(self, request, queryset):
        queryset.update(status='Dismissed')
