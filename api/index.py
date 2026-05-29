import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

if os.getenv("VERCEL") == "1":
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
