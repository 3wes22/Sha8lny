"""
Notifications Service URL Configuration

Implements REST API endpoints for notifications and preferences.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.notifications import views

# Router for ViewSets
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')

app_name = 'notifications'

urlpatterns = [
    # Notification preferences
    path('preferences/', views.NotificationPreferencesView.as_view(), name='preferences'),
    path('preferences/type/', views.UpdateTypePreferenceView.as_view(), name='type-preference'),
    path('preferences/quiet-hours/', views.SetQuietHoursView.as_view(), name='quiet-hours'),

    # Notification statistics
    path('stats/', views.NotificationStatsView.as_view(), name='stats'),

    # Router URLs (notifications CRUD)
    path('', include(router.urls)),
]
