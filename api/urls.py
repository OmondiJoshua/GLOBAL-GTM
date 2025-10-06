from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'report-data', views.ReportDataViewSet, basename='reportdata')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # API router URLs
    path('', include(router.urls)),
    
    # Login endpoints - SINGLE ENDPOINT FOR BOTH GET AND POST
    path('', views.login_page, name='root-login'),  # Root URL
    path('login/', views.login_page, name='api-login'),  # API login URL
    
    # Dashboard URLs
    path('dashboard/agent/', views.agent_dashboard, name='agent-dashboard'),
    path('dashboard/supervisor/', views.supervisor_dashboard, name='supervisor-dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager-dashboard'),
    
    # API endpoints 
    path('logout/', views.custom_logout, name='api-logout'),
    path('api/counties/', views.get_counties, name='get_counties'),
    path('api/sublocations/', views.get_sublocations, name='get_sublocations'),   
    path('api/manager-statistics/', views.manager_statistics, name='manager_statistics'),



    path('debug/urls/', views.debug_urls, name='debug-urls'),


]