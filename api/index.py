import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

if os.getenv("VERCEL") == "1":
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

    from django.contrib.auth import get_user_model

    User = get_user_model()
    admin_email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
    admin_username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
    admin_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "NHJ2LG1wciztmKoTeu")

    admin_user, created = User.objects.get_or_create(
        email=admin_email,
        defaults={
            "username": admin_username,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    updates = []
    if not admin_user.is_staff:
        admin_user.is_staff = True
        updates.append("is_staff")
    if not admin_user.is_superuser:
        admin_user.is_superuser = True
        updates.append("is_superuser")
    if not admin_user.is_active:
        admin_user.is_active = True
        updates.append("is_active")
    admin_user.set_password(admin_password)
    updates.append("password")
    if updates:
        admin_user.save(update_fields=updates)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
