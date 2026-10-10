from django.urls import path
from . import views

urlpatterns = [
    path("", views.RoomListView.as_view(), name="room_list"),
    path("add/", views.RoomCreateView.as_view(), name="room_add"),
    path("<int:pk>/edit/", views.RoomUpdateView.as_view(), name="room_edit"),
    path("<int:pk>/delete/", views.RoomDeleteView.as_view(), name="room_delete"),
]