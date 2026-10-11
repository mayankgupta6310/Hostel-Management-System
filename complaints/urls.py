from django.urls import path
from . import views

urlpatterns = [
    path("my/", views.MyComplaintsView.as_view(), name="my_complaints"),
    path("new/", views.ComplaintCreateView.as_view(), name="complaint_add"),
    path("", views.ComplaintListView.as_view(), name="complaint_list"),
    path("<int:pk>/assign/", views.AssignComplaintView.as_view(), name="complaint_assign"),
    path("tasks/", views.StaffTasksView.as_view(), name="staff_tasks"),
    path("<int:pk>/status/", views.UpdateStatusView.as_view(), name="complaint_status"),
]