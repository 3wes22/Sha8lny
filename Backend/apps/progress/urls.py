"""
Progress Service URL Configuration

Endpoints for progress tracking, course completions, achievements, and time logs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.progress import views

router = DefaultRouter()
router.register(r'progress', views.UserProgressViewSet, basename='progress')
router.register(r'completions', views.CourseCompletionViewSet, basename='completion')
router.register(r'achievements', views.MilestoneAchievementViewSet, basename='achievement')
router.register(r'timelogs', views.TimeLogViewSet, basename='timelog')

app_name = 'progress'

urlpatterns = [
    # Statistics
    path('stats/', views.ProgressStatsView.as_view(), name='stats'),

    # Progress tracking routes
    path('', include(router.urls)),
]
