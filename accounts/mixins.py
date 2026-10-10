from django.contrib.auth.mixins import UserPassesTestMixin


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role in self.allowed_roles