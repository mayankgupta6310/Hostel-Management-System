from django.db import models


class MealType(models.TextChoices):
    BREAKFAST = "BREAKFAST", "Breakfast"
    LUNCH = "LUNCH", "Lunch"
    DINNER = "DINNER", "Dinner"


class MenuItem(models.Model):
    DAYS = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
        (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    day = models.PositiveSmallIntegerField(choices=DAYS)
    meal_type = models.CharField(max_length=10, choices=MealType.choices)
    items = models.CharField(max_length=250, help_text="Jaise: Roti, Dal, Aloo Gobhi, Chawal")

    class Meta:
        unique_together = ("day", "meal_type")
        ordering = ["day", "meal_type"]

    def __str__(self):
        return f"{self.get_day_display()} - {self.get_meal_type_display()}"


class MealOptOut(models.Model):
    """Is tenant ne is din ka yeh meal NAHI khana. Record nahi hai = meal ON."""
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="meal_optouts")
    date = models.DateField()
    meal_type = models.CharField(max_length=10, choices=MealType.choices)

    class Meta:
        unique_together = ("tenant", "date", "meal_type")

    def __str__(self):
        return f"{self.tenant} - {self.date} - {self.meal_type}"


class MessFeedback(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="mess_feedback")
    date = models.DateField(auto_now_add=True)
    meal_type = models.CharField(max_length=10, choices=MealType.choices)
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} star") for i in range(1, 6)])
    comment = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.tenant} - {self.meal_type} - {self.rating}"