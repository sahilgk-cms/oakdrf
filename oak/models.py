import uuid

from django.db import models
from django.contrib.auth.models import User
from oakdrf.config import MAIN_DOCUMENT_CHOICES


# Create your models here.
class ChatSession(models.Model):
    """For creating and storing sessions"""
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    user = models.ForeignKey(User, on_delete = models.CASCADE, null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Session: {self.id}"


class ChatMessage(models.Model):
    """For creating and storing chat messages within a session"""
    id = models.BigAutoField(primary_key = True)
    role = models.CharField(max_length = 20, choices = [("user", "User"), ("assistant", "Assistant")])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add = True)
    session = models.ForeignKey(ChatSession, on_delete = models.CASCADE, related_name = "chatmessages")

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.role}: {self.message[:50]}"


class CaseStory(models.Model):
    """For creating and storing case stories in the database"""
    main_document = models.CharField(max_length = 50, choices = MAIN_DOCUMENT_CHOICES)
    journal = models.CharField(max_length = 255, null = True, blank = True)
    partner = models.CharField(max_length = 255, null = True, blank = True)
    social_actor_name = models.CharField(max_length = 255, null = True, blank = True)
    pdf_name = models.CharField(max_length = 255, null = True, blank = True)
    case_story = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        unique_together = (
        ("main_document", "journal", "partner", "social_actor_name"),
        ("main_document", "pdf_name")
        )

    def __str__(self):
        return f"{self.main_document} - {self.journal or self.pdf_name}"

class CaseStoryChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_story = models.ForeignKey(CaseStory, on_delete = models.CASCADE, related_name = "case_story_chatsession")
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Case Story Chat Session: {self.case_story}"

class CaseStoryChatMessage(models.Model):
    session = models.ForeignKey(CaseStoryChatSession, on_delete = models.CASCADE, related_name = "case_story_chatmessages")
    role = models.CharField(max_length = 20, choices = [("user", "User"), ("assistant", "Assistant")])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.role}: {self.message[:50]}"


