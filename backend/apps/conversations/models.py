from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class ConversationState(BaseModel):
    class Flow(models.TextChoices):
        MAIN_MENU = "main_menu", "Main Menu"
        REGISTRATION = "registration", "Registration"
        PAST_PAPER = "past_paper", "Past Paper"
        REVISION = "revision", "Revision"
        QUIZ = "quiz", "Quiz"
        AI_TUTOR = "ai_tutor", "AI Tutor"
        STUDY_PLAN = "study_plan", "Study Plan"
        PROGRESS = "progress", "Progress"
        BILLING = "billing", "Billing"

    phone_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation_states",
    )
    current_flow = models.CharField(
        max_length=20, choices=Flow.choices, default=Flow.MAIN_MENU
    )
    current_step = models.CharField(max_length=50, blank=True, default="")
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["phone_number"])]

    def __str__(self):
        return f"ConversationState<{self.phone_number}> {self.current_flow}/{self.current_step}"

    def reset_to_main_menu(self):
        self.current_flow = self.Flow.MAIN_MENU
        self.current_step = ""
        self.context = {}
