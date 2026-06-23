from celery import shared_task
from django.contrib.auth import get_user_model

from . import services

User = get_user_model()


@shared_task
def recompute_user_analytics_task(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    services.recompute_user_analytics(user)


@shared_task
def recompute_all_users_analytics():
    user_ids = User.objects.filter(role=User.Role.STUDENT).values_list("id", flat=True)
    for user_id in user_ids:
        recompute_user_analytics_task.delay(str(user_id))
