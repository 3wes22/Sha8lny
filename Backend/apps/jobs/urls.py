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

router = DefaultRouter()
router.register(r'', views.JobViewSet, basename='job')
router.register(r'platforms', views.JobPlatformViewSet, basename='platform')
router.register(r'insights', views.SkillDemandInsightViewSet, basename='insight')

app_name = 'jobs'

urlpatterns = [
    path('', include(router.urls)),
]
