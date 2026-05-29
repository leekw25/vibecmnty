import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="poll",
            old_name="title",
            new_name="question",
        ),
        migrations.RenameField(
            model_name="poll",
            old_name="author",
            new_name="created_by",
        ),
        migrations.RenameField(
            model_name="poll",
            old_name="starts_at",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="poll",
            old_name="ends_at",
            new_name="expires_at",
        ),
        migrations.RemoveField(model_name="poll", name="description"),
        migrations.RemoveField(model_name="poll", name="is_multiple"),
        migrations.RemoveField(model_name="poll", name="is_anonymous"),
        migrations.RemoveField(model_name="polloption", name="order"),
        migrations.AddField(
            model_name="polloption",
            name="votes_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RenameModel(
            old_name="PollVote",
            new_name="Vote",
        ),
        migrations.RenameField(
            model_name="vote",
            old_name="voter",
            new_name="user",
        ),
        migrations.AlterField(
            model_name="vote",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="vote",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="poll",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
