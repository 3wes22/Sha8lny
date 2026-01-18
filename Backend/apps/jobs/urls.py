"""
Jobs Service URL Configuration

SRS Appendix B:
| Method | Endpoint            | Description                    |
|--------|---------------------|--------------------------------|
| GET    | /jobs/search        | Search jobs                    |
| GET    | /jobs/<id>          | Get job details                |
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.jobs import views

# Separate routers to avoid conflicts
job_router = DefaultRouter()
job_router.register(r'', views.JobViewSet, basename='job')

saved_job_router = DefaultRouter()
saved_job_router.register(r'', views.SavedJobViewSet, basename='saved-job')

# EXTRA ENDPOINTS - NOT IN SRS APPENDIX B
# Uncomment if needed in future
# router.register(r'platforms', views.JobPlatformViewSet, basename='platform')
# router.register(r'demand', views.SkillDemandViewSet, basename='demand')

app_name = 'jobs'

urlpatterns = [
    path('saved-jobs/', include(saved_job_router.urls)),
    path('', include(job_router.urls)),
]
