from django.db import migrations

PLANS = [
    {
        "name": "Free",
        "code": "free",
        "price": 0,
        "billing_period": "monthly",
        "features": [
            "quizzes",
            "notes_basic",
            "ai_tutor",
            "study_plan_basic",
            "analytics_basic",
        ],
        "quotas": {"ai_tutor": 5, "paper_view": 3},
        "is_active": True,
    },
    {
        "name": "Plus",
        "code": "plus",
        "price": 2,
        "billing_period": "monthly",
        "features": [
            "quizzes",
            "notes_unlimited",
            "ai_tutor",
            "study_plan_basic",
            "analytics_basic",
            "paper_download",
        ],
        "quotas": {"ai_tutor": 30},
        "is_active": True,
    },
    {
        "name": "Premium",
        "code": "premium",
        "price": 5,
        "billing_period": "monthly",
        "features": [
            "quizzes",
            "notes_unlimited",
            "ai_tutor",
            "study_plan_full",
            "analytics_advanced",
            "paper_download",
        ],
        "quotas": {},
        "is_active": True,
    },
    {
        "name": "School",
        "code": "school",
        "price": 1,
        "billing_period": "term",
        "features": [
            "quizzes",
            "notes_unlimited",
            "ai_tutor",
            "study_plan_full",
            "analytics_advanced",
            "paper_download",
            "teacher_dashboard",
        ],
        "quotas": {},
        "is_active": True,
    },
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    for plan in PLANS:
        Plan.objects.update_or_create(code=plan["code"], defaults=plan)


def unseed_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code__in=[plan["code"] for plan in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]

    operations = [migrations.RunPython(seed_plans, unseed_plans)]
