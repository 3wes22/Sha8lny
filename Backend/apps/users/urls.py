"""
User Service URL Configuration

Implements REST API endpoints as specified in SRS Appendix B.

SRS References:
- Appendix B: API Endpoint Summary (MVP)

User Service Endpoints (from SRS):
| Method | Endpoint        | Description           |
|--------|----------------|-----------------------|
| POST   | /auth/login    | User login via Auth0  |
| GET    | /users/me      | Get current user      |
| PUT    | /users/me      | Update profile        |
| GET    | /users/skills  | List user skills      |
| POST   | /users/skills  | Add skill             |
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users import views

# Router for ViewSets
router = DefaultRouter()
router.register(r'skills', views.SkillViewSet, basename='skill')
router.register(r'user-skills', views.UserSkillViewSet, basename='user-skill')

app_name = 'users'

urlpatterns = [
    # Authentication endpoints (SRS Appendix B)
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.UserLoginView.as_view(), name='login'),
    path('auth/logout/', views.UserLogoutView.as_view(), name='logout'),
    path('auth/refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),

    # User profile endpoints (SRS Appendix B: /users/me)
    path('me/', views.UserProfileView.as_view(), name='profile'),
    path('me/preferences/', views.UserPreferencesView.as_view(), name='preferences'),

    # Skill endpoints (SRS Appendix B: /users/skills)
    path('', include(router.urls)),
]
