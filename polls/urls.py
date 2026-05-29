from django.urls import path

from . import views

app_name = "polls"

urlpatterns = [
    path("", views.poll_list, name="list"),
    path("new/", views.poll_create, name="new"),
    path("create/", views.poll_create, name="create"),
    path("<int:pk>/", views.poll_detail, name="detail"),
    path("<int:pk>/results/", views.poll_results, name="results"),
    path("<int:pk>/delete/", views.poll_delete, name="delete"),
]
