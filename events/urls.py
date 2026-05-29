from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_calendar, name="calendar"),
    path("new/", views.event_create, name="new"),
    path("create/", views.event_create, name="create"),
    path("<int:pk>/", views.event_detail, name="detail"),
    path("<int:pk>/edit/", views.event_update, name="update"),
    path("<int:pk>/delete/", views.event_delete, name="delete"),
]
