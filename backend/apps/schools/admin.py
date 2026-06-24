from django.contrib import admin

from .models import School, SchoolSeat


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "admin_user", "seat_count")


@admin.register(SchoolSeat)
class SchoolSeatAdmin(admin.ModelAdmin):
    list_display = ("school", "user", "is_active")
    list_filter = ("school", "is_active")
