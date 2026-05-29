from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import TemplateView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("notices/", include("notices.urls")),
    path("posts/", include("posts.urls")),
    path("events/", include("events.urls")),
    path("polls/", include("polls.urls")),
    path("surveys/", include("surveys.urls")),
    path("admin-dashboard/", include("admin_dashboard.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler403 = "config.views.custom_permission_denied"
