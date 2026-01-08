"""
Courses Service URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.courses import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'enrollments', views.UserCourseEnrollmentViewSet, basename='enrollment')
router.register(r'platforms', views.CoursePlatformViewSet, basename='platform')

app_name = 'courses'

urlpatterns = [
    path('', include(router.urls)),
]
