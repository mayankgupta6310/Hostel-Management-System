import os

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from notices.models import Notice
from rooms.models import Bed, Hostel, Room
from tenants.models import Allotment, Tenant

User = get_user_model()

# 1x1 transparent PNG (demo ID proof ke liye)
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe"
    b"\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82"
)


class Command(BaseCommand):
    help = "Demo data banata hai (users, rooms, tenants). Password SEED_PASSWORD env se aata hai."

    def handle(self, *args, **options):
        password = os.getenv("SEED_PASSWORD")
        if not password:
            raise CommandError("SEED_PASSWORD environment variable set karo (strong password).")

        with transaction.atomic():
            self.make_staff_users(password)
            self.make_hostel_and_rooms()
            self.make_tenants(password)
            Notice.objects.get_or_create(
                title="Welcome",
                defaults={"body": "Welcome to the Hostel Management demo.", "is_important": True},
            )
        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    def make_user(self, username, role, password, **extra):
        user, created = User.objects.get_or_create(
            username=username, defaults={"role": role, **extra}
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"  user bana: {username} ({role})")
        return user

    def make_staff_users(self, password):
        admin = self.make_user("admin_demo", "ADMIN", password, is_staff=True, is_superuser=True)
        self.make_user("warden1", "WARDEN", password)
        self.make_user("guard1", "GUARD", password)
        self.make_user("staff1", "STAFF", password)
        self.make_user("mess1", "MESS", password)
        return admin

    def make_hostel_and_rooms(self):
        hostel, _ = Hostel.objects.get_or_create(
            name="Gupta Boys Hostel", defaults={"address": "Lucknow"}
        )
        for room_no, floor, capacity, rent in [
            ("101", 1, 3, 4000), ("102", 1, 2, 5000), ("201", 2, 4, 3500),
        ]:
            room, created = Room.objects.get_or_create(
                hostel=hostel, room_no=room_no,
                defaults={"floor": floor, "capacity": capacity, "rent_per_bed": rent},
            )
            if created:
                for i in range(1, capacity + 1):
                    Bed.objects.create(room=room, bed_no=f"B{i}")

    def make_tenants(self, password):
        beds = list(Bed.objects.filter(is_occupied=False).order_by("room__room_no", "bed_no")[:2])
        for username, first, bed in zip(["rahul1", "amit1"], ["Rahul", "Amit"], beds):
            user = self.make_user(username, "TENANT", password, first_name=first, last_name="Demo")
            tenant, created = Tenant.objects.get_or_create(
                user=user,
                defaults={"guardian_name": f"{first}'s Father", "guardian_phone": "9999999999"},
            )
            if created:
                tenant.id_proof.save("demo_id.png", ContentFile(TINY_PNG), save=True)
            if not tenant.allotments.filter(is_active=True).exists():
                Allotment.objects.create(tenant=tenant, bed=bed, start_date=timezone.localdate())
                bed.is_occupied = True
                bed.save(update_fields=["is_occupied"])