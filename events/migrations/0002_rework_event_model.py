from __future__ import annotations

from datetime import date
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_event_columns(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    user_model = settings.AUTH_USER_MODEL
    user_app_label, user_model_name = user_model.split(".")
    User = apps.get_model(user_app_label, user_model_name)

    default_user = (
        User.objects.filter(is_superuser=True).order_by("id").first()
        or User.objects.filter(is_staff=True).order_by("id").first()
        or User.objects.order_by("id").first()
    )

    for event in Event.objects.all():
        start_value = getattr(event, "start_at", None)
        end_value = getattr(event, "end_at", None)

        if start_value:
            event.start_date = start_value.date()
        else:
            event.start_date = date.today()

        if end_value:
            event.end_date = end_value.date()
        else:
            event.end_date = event.start_date

        if default_user is not None:
            event.created_by_id = default_user.id

        fields = ["start_date", "end_date"]
        if default_user is not None:
            fields.append("created_by_id")
        event.save(update_fields=fields)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_role"),
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to=settings.AUTH_USER_MODEL,
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="start_date",
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="location",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.RunPython(migrate_event_columns, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="event",
            name="events_even_start_a_8d8d94_idx",
        ),
        migrations.RemoveField(
            model_name="event",
            name="is_all_day",
        ),
        migrations.RemoveField(
            model_name="event",
            name="is_published",
        ),
        migrations.RemoveField(
            model_name="event",
            name="start_at",
        ),
        migrations.RemoveField(
            model_name="event",
            name="end_at",
        ),
        migrations.RemoveField(
            model_name="event",
            name="category",
        ),
        migrations.AlterField(
            model_name="event",
            name="start_date",
            field=models.DateField(),
        ),
        migrations.AlterModelOptions(
            name="event",
            options={"ordering": ["start_date", "title"]},
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["start_date"], name="events_event_start_date_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["end_date"], name="events_event_end_date_idx"),
        ),
        migrations.RemoveField(
            model_name="event",
            name="updated_at",
        ),
        migrations.AlterField(
            model_name="event",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
