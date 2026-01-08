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
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

app_name = 'advisory'

urlpatterns = [
    # Chat endpoint
    path('chat/', views.ChatView.as_view(), name='chat'),

    # Conversation management
    path('', include(router.urls)),
]
