from django.db import migrations

TASK_NAME = "IA — Marcar chats sin respuesta como error"
TASK_PATH = "apps.reportes.tasks.tarea_marcar_chats_vencidos"


def registrar_tarea(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = IntervalSchedule.objects.get_or_create(every=10, period="minutes")
    PeriodicTask.objects.get_or_create(
        name=TASK_NAME,
        defaults={"task": TASK_PATH, "interval": schedule, "enabled": True},
    )


def eliminar_tarea(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name=TASK_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("reportes", "0003_conversacion_mensajechat"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(registrar_tarea, eliminar_tarea),
    ]
