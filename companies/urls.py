from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('edit/', views.company_edit, name='company_edit'),
    path('fetch-api/', views.fetch_company_api_view, name='fetch_api'),
    path('api/fetch/', views.api_fetch_company_openings, name='api_fetch_openings'),
    path('<slug:slug>/', views.company_detail, name='company_detail'),
]
