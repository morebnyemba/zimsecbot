from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.common.models import BaseModel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        CONTENT_ADMIN = "content_admin", "Content Admin"
        SUPERADMIN = "superadmin", "Superadmin"
        SUPPORT = "support", "Support"
        SCHOOL_ADMIN = "school_admin", "School Admin"

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class StudentProfile(BaseModel):
    class Level(models.TextChoices):
        O_LEVEL = "o_level", "O-Level"
        A_LEVEL = "a_level", "A-Level"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    level = models.CharField(max_length=20, choices=Level.choices, blank=True)
    exam_year = models.PositiveIntegerField(blank=True, null=True)
    school_name = models.CharField(max_length=255, blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return f"Profile<{self.user.email}>"
