from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from accounts.mixins import RoleRequiredMixin
from .forms import NoticeForm
from .models import Notice


class NoticeListView(LoginRequiredMixin, ListView):
    model = Notice
    template_name = "notices/notice_list.html"
    context_object_name = "notices"
    paginate_by = 20


class NoticeCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["ADMIN", "WARDEN"]
    form_class = NoticeForm
    template_name = "notices/notice_form.html"
    success_url = reverse_lazy("notice_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Notice post ho gaya.")
        return super().form_valid(form)


class NoticeDeleteView(RoleRequiredMixin, View):
    allowed_roles = ["ADMIN", "WARDEN"]

    def post(self, request, pk):
        get_object_or_404(Notice, pk=pk).delete()
        messages.success(request, "Notice delete ho gaya.")
        return redirect("notice_list")