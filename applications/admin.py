from django.contrib import admin
from .models import Application, Interview, Notification


class InterviewInline(admin.StackedInline):
    model = Interview
    can_delete = True
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'applied_at', 'updated_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('candidate__username', 'candidate__first_name', 'candidate__last_name', 'job__title', 'job__company__name')
    inlines = [InterviewInline]
    actions = ['mark_under_review', 'mark_shortlisted', 'mark_rejected']

    @admin.action(description="Mark selected applications as Under Review")
    def mark_under_review(self, request, queryset):
        queryset.update(status='Under Review')

    @admin.action(description="Mark selected applications as Shortlisted")
    def mark_shortlisted(self, request, queryset):
        queryset.update(status='Shortlisted')

    @admin.action(description="Mark selected applications as Rejected")
    def mark_rejected(self, request, queryset):
        queryset.update(status='Rejected')


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'scheduled_date', 'scheduled_time', 'mode', 'location_or_link')
    list_filter = ('mode', 'scheduled_date')
    search_fields = ('application__candidate__username', 'application__job__title', 'location_or_link')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
