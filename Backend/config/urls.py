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

    # API v1 Endpoints (SRS Appendix B)
    # User Service endpoints: /auth/login, /users/me, /users/skills
    path("api/v1/users/", include('apps.users.urls')),

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
