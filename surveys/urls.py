from django.urls import path

from . import views

app_name = "surveys"

urlpatterns = [
    path("", views.survey_list, name="list"),
    path("new/", views.survey_create, name="new"),
    path("<int:pk>/respond/", views.survey_respond, name="respond"),
    path("<int:pk>/results/", views.survey_results, name="results"),
]
