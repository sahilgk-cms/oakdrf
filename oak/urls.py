from django.urls import path
from .views import ChatbotAPIView, CaseStoryView, CaseStoryChatView

urlpatterns = [
    path("chat/", ChatbotAPIView.as_view(), name = "chatbot"),
    path("casestory/", CaseStoryView.as_view(), name = "casestory"),
    path("casestorychat/", CaseStoryChatView.as_view(), name = "casestorychat")
]