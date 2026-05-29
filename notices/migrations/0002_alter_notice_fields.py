from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notices", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notice",
            old_name="is_pinned",
            new_name="is_important",
        ),
        migrations.RemoveIndex(
            model_name="notice",
            name="notices_not_is_pinn_017be3_idx",
        ),
        migrations.RemoveField(
            model_name="notice",
            name="is_published",
        ),
        migrations.AlterModelOptions(
            name="notice",
            options={"ordering": ["-is_important", "-created_at"]},
        ),
        migrations.AddIndex(
            model_name="notice",
            index=models.Index(fields=["is_important", "created_at"], name="notices_is_import_creat_idx"),
        ),
    ]
