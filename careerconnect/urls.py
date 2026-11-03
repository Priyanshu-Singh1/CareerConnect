from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('companies/', include('companies.urls')),
    path('applications/', include('applications.urls')),
    path('', include('jobs.urls')),
]

# Serve media files in development (avatars, logos)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'careerconnect.views.error_403'
handler404 = 'careerconnect.views.error_404'
handler500 = 'careerconnect.views.error_500'
