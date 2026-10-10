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
        messages.success(self.request, f"Room {self.object.room_no} aur {self.object.capacity} beds ban gaye.")
        return response


class RoomUpdateView(StaffMixin, UpdateView):
    model = Room
    form_class = RoomUpdateForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("room_list")

    def form_valid(self, form):
        messages.success(self.request, "Room update ho gaya.")
        return super().form_valid(form)


class RoomDeleteView(AdminOnlyMixin, DeleteView):
    model = Room
    template_name = "rooms/room_confirm_delete.html"
    success_url = reverse_lazy("room_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Room delete ho gaya.")
            return response
        except ProtectedError:
            messages.error(self.request, "Is room ke beds par tenant allotted hai, delete nahi ho sakta.")
            return redirect("room_list")