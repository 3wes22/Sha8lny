"""
Assessment Service URL Configuration

SRS Appendix B:
| Method | Endpoint               | Description            |
|--------|------------------------|------------------------|
| POST   | /assessment/           | Generate assessment    |
| GET    | /assessment/latest     | Latest assessment      |
| GET    | /assessment/history    | All assessments        |
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.assessments import views

router = DefaultRouter()
router.register(r'', views.AssessmentViewSet, basename='assessment')

app_name = 'assessments'

urlpatterns = [
    # EXTRA ENDPOINTS - NOT IN SRS APPENDIX B
    # Uncomment if needed in future
    # path('results/', views.AssessmentResultView.as_view(), name='results-list'),
    # path('results/<uuid:result_id>/', views.AssessmentResultView.as_view(), name='results-detail'),
    # path('stats/', views.AssessmentStatsView.as_view(), name='stats'),

    # Assessment CRUD and actions (from router)
    path('', include(router.urls)),
]
