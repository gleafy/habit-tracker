from rest_framework import serializers
from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = ["user"]

    def validate(self, data):
        errors = {}

        # Валидация 1: время выполнения <= 120 секунд
        duration = data.get("duration")
        if duration and duration > 120:
            errors["duration"] = "Время выполнения не должно превышать 120 секунд."

        # Валидация 2: периодичность не реже 1 раза в 7 дней
        frequency = data.get("frequency", 1)
        if frequency > 7:
            errors["frequency"] = "Нельзя выполнять привычку реже, чем 1 раз в 7 дней."

        # Валидация 3: нельзя одновременно связанную привычку и вознаграждение
        related_habit = data.get("related_habit")
        reward = data.get("reward")
        if related_habit and reward:
            errors["reward"] = "Нельзя одновременно указывать связанную привычку и вознаграждение."

        # Валидация 4: связанная привычка должна быть приятной
        if related_habit and not related_habit.is_pleasant:
            errors["related_habit"] = "Связанная привычка должна быть приятной."

        # Валидация 5: у приятной привычки не может быть вознаграждения или связанной привычки
        is_pleasant = data.get("is_pleasant", False)
        if is_pleasant:
            if reward:
                errors["reward"] = "У приятной привычки не может быть вознаграждения."
            if related_habit:
                errors["related_habit"] = "У приятной привычки не может быть связанной привычки."

        if errors:
            raise serializers.ValidationError(errors)

        return data
