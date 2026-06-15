from django.db import migrations

TASK_NAME = "CU11 — Cerrar convocatorias vencidas"
TASK_PATH = "apps.convocatorias.tasks.tarea_cerrar_convocatorias_vencidas"


def registrar_tarea(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="*",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )
    PeriodicTask.objects.get_or_create(
        name=TASK_NAME,
        defaults={"task": TASK_PATH, "crontab": schedule, "enabled": True},
    )


def eliminar_tarea(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name=TASK_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("convocatorias", "0001_initial"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(registrar_tarea, eliminar_tarea),
    ]
