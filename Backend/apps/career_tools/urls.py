"""
Career Tools Service URL Configuration

Endpoints for resume/CV builder and portfolio management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.career_tools import views

router = DefaultRouter()
router.register(r'resumes', views.ResumeViewSet, basename='resume')
router.register(r'portfolios', views.PortfolioViewSet, basename='portfolio')

app_name = 'career_tools'

urlpatterns = [
    path('', include(router.urls)),
]
