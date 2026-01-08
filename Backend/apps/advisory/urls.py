"""
Advisory Service URL Configuration

SRS Appendix B:
| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | /advisory/chat        | Send message to chatbot        |
| GET    | /advisory/history     | Get conversation history       |
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.advisory import views

router = DefaultRouter()
router.register(r'history', views.ConversationViewSet, basename='conversation')

app_name = 'advisory'

urlpatterns = [
    # SRS APPENDIX B ENDPOINTS
    # POST /advisory/chat - Send message to chatbot
    path('chat/', views.ChatView.as_view(), name='chat'),

    # GET /advisory/history - Get conversation history
    path('', include(router.urls)),
]
