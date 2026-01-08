"""
Sha8alny Main URL Configuration

Implements API routing as specified in SRS Appendix B.

SRS Reference: Section 3.2.4 (Communication Interfaces)
- CI-1: REST API with JSON-based request/response
- Standard conventions: GET /api/..., POST /api/...

API Version: v1 (as per SRS Appendix B)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # ============================================================================
    # API v1 Endpoints (SRS Appendix B)
    # ============================================================================

    # User Service endpoints: /auth/login, /users/me, /users/skills
    path("api/v1/users/", include('apps.users.urls')),

    # Assessment Service endpoints: /assessment/, /assessment/latest, /assessment/history
    path("api/v1/assessment/", include('apps.assessments.urls')),

    # Roadmap Service endpoints: /roadmap/, /roadmap/progress
    path("api/v1/roadmap/", include('apps.roadmaps.urls')),

    # Job Service endpoints: /jobs/search, /jobs/<id>
    path("api/v1/jobs/", include('apps.jobs.urls')),

    # Advisory Service endpoints: /advisory/chat, /advisory/history
    path("api/v1/advisory/", include('apps.advisory.urls')),

    # ============================================================================
    # EXTRA MODULES - NOT IN SRS APPENDIX B
    # These modules kept as-is per user request (to be added to SRS later)
    # ============================================================================

    # Progress Service endpoints (not in SRS Appendix B)
    path("api/v1/progress/", include('apps.progress.urls')),

    # Career Tools Service endpoints (not in SRS Appendix B)
    path("api/v1/career-tools/", include('apps.career_tools.urls')),

    # ============================================================================
    # EXTRA MODULES - NOT IN SRS APPENDIX B
    # Uncomment if needed in future
    # ============================================================================

    # Notification Service endpoints
    # path("api/v1/notifications/", include('apps.notifications.urls')),

    # Course Service endpoints
    # path("api/v1/courses/", include('apps.courses.urls')),

    # API Documentation (OpenAPI/Swagger)
    # As per SRS requirement for REST API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
