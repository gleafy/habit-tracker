from django.db import models
from users.models import User


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.CharField(max_length=255)
    time = models.TimeField()
    action = models.CharField(max_length=255)
    is_pleasant = models.BooleanField(default=False)
    related_habit = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    frequency = models.PositiveSmallIntegerField(default=1)
    reward = models.CharField(max_length=255, blank=True, null=True)
    duration = models.PositiveSmallIntegerField()
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.action} в {self.place}"
