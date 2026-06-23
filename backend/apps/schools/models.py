from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class School(BaseModel):
    name = models.CharField(max_length=255)
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="administered_schools"
    )
    seat_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SchoolSeat(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="seats")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="school_seats"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["school", "user"], name="unique_seat_per_school_user")
        ]

    def __str__(self):
        return f"SchoolSeat<{self.school_id}:{self.user_id}>"
