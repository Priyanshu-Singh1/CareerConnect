from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'location', 'company_size', 'is_verified', 'created_at')
    list_filter = ('industry', 'is_verified', 'company_size')
    search_fields = ('name', 'description', 'location', 'industry')
    prepopulated_fields = {'slug': ('name',)}
    actions = ['verify_companies', 'unverify_companies']

    @admin.action(description="Mark selected companies as verified")
    def verify_companies(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description="Mark selected companies as unverified")
    def unverify_companies(self, request, queryset):
        queryset.update(is_verified=False)
