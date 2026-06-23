from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.quizzes.models import QuizAttempt

from .tasks import recompute_user_analytics_task


@receiver(post_save, sender=QuizAttempt)
def trigger_analytics_recompute(sender, instance, **kwargs):
    if instance.completed_at is not None:
        recompute_user_analytics_task.delay(str(instance.user_id))
