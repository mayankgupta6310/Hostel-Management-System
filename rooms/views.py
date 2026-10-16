from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.mixins import RoleRequiredMixin
from .forms import RoomCreateForm, RoomUpdateForm
from .models import Room, Bed


class StaffMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN", "WARDEN"]


class AdminOnlyMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN"]


class RoomListView(StaffMixin, ListView):
    model = Room
    template_name = "rooms/room_list.html"
    context_object_name = "rooms"

    def get_queryset(self):
        return Room.objects.select_related("hostel").prefetch_related("beds")


class RoomCreateView(StaffMixin, CreateView):
    model = Room
    form_class = RoomCreateForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("room_list")

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            for i in range(1, self.object.capacity + 1):
                Bed.objects.create(room=self.object, bed_no=f"B{i}")
        messages.success(self.request, f"Room {self.object.room_no} and {self.object.capacity} beds created.")
        return response


class RoomUpdateView(StaffMixin, UpdateView):
    model = Room
    form_class = RoomUpdateForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("room_list")

    def form_valid(self, form):
        messages.success(self.request, "Room updated.")
        return super().form_valid(form)


class RoomDeleteView(AdminOnlyMixin, DeleteView):
    model = Room
    template_name = "rooms/room_confirm_delete.html"
    success_url = reverse_lazy("room_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Room deleted.")
            return response
        except ProtectedError:
            messages.error(self.request, "A tenant is allotted to a bed in this room, so it cannot be deleted.")
            return redirect("room_list")