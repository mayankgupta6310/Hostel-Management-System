from django.db import models


class Hostel(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    room_no = models.CharField(max_length=10)
    floor = models.PositiveIntegerField(default=0)
    capacity = models.PositiveSmallIntegerField(default=2, help_text="Kitne beds hain")
    rent_per_bed = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("hostel", "room_no")
        ordering = ["hostel", "floor", "room_no"]

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_no}"

    @property
    def occupied_count(self):
        return sum(1 for b in self.beds.all() if b.is_occupied)

    @property
    def vacant_count(self):
        return self.beds.count() - self.occupied_count


class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="beds")
    bed_no = models.CharField(max_length=5)
    is_occupied = models.BooleanField(default=False)

    class Meta:
        unique_together = ("room", "bed_no")
        ordering = ["bed_no"]

    def __str__(self):
        return f"{self.room} / {self.bed_no}"