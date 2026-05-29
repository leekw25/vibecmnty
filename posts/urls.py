from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.post_list, name="list"),
    path("new/", views.post_create, name="create"),
    path("<int:pk>/", views.post_detail, name="detail"),
    path("<int:pk>/edit/", views.post_update, name="update"),
    path("<int:pk>/delete/", views.post_delete, name="delete"),
    path("<int:post_id>/like/", views.post_toggle_like, name="like"),
    path("<int:post_id>/comments/", views.post_comment_create, name="comment_create"),
    path(
        "<int:post_id>/comments/<int:comment_id>/delete/",
        views.post_comment_delete,
        name="comment_delete",
    ),
    path(
        "<int:post_id>/comments/<int:comment_id>/edit/",
        views.post_comment_update,
        name="comment_update",
    ),
]
