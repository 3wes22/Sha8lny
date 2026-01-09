"""
Roadmaps Service URL Configuration

SRS Appendix B:
| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | /roadmap/             | Generate roadmap               |
| GET    | /roadmap/             | Get user's roadmap             |
| PUT    | /roadmap/progress     | Update progress                |
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.roadmaps import views

router = DefaultRouter()
# EXTRA ENDPOINT - NOT IN SRS APPENDIX B
# Uncomment if needed in future
# router.register(r'templates', views.RoadmapTemplateViewSet, basename='template')
router.register(r'', views.RoadmapViewSet, basename='roadmap')

app_name = 'roadmaps'

urlpatterns = [
    # Roadmap CRUD and actions
    path('', include(router.urls)),
]
