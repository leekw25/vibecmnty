from django.urls import path

from . import views

app_name = "admin_dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("notices/", views.notice_management, name="notices"),
    path("posts/", views.post_management, name="posts"),
    path("events/", views.event_management, name="events"),
    path("polls/", views.poll_management, name="polls"),
    path("surveys/", views.survey_management, name="surveys"),
    path("users/", views.user_management, name="users"),
    path("users/action/", views.user_action, name="user_action"),
    path("system/", views.system_management, name="system"),
]
