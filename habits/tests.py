from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User, TelegramUser
from habits.tasks import send_telegram_reminders
from unittest.mock import patch, Mock
from habits.models import Habit
from datetime import time


class HabitModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_habit_creation(self):
        habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time="08:00:00",
            action="Читать книгу",
            duration=60,
            frequency=1,
        )
        self.assertEqual(habit.action, "Читать книгу")
        self.assertEqual(habit.duration, 60)


class HabitAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_create_habit(self):
        data = {
            "place": "Парк",
            "time": "07:00:00",
            "action": "Бегать",
            "duration": 120,
            "frequency": 1,
        }
        response = self.client.post("/api/habits/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class HabitTasksTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # Создаем привязку к Telegram
        self.telegram_user = TelegramUser.objects.create(user=self.user, chat_id="123456789")

        # Создаем привычку на текущее время
        current_time = timezone.now().time()
        self.habit = Habit.objects.create(
            user=self.user, place="Дом", time=current_time, action="Тестовая привычка", duration=60
        )

    @patch("habits.tasks.settings.TELEGRAM_BOT_TOKEN", "test_token")
    @patch("habits.tasks.requests.post")
    def test_send_telegram_reminders_success(self, mock_post):
        """Тест успешной отправки напоминания"""
        # Мокаем успешный ответ от Telegram API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Вызываем задачу
        send_telegram_reminders()

        # Проверяем, что запрос был отправлен
        mock_post.assert_called_once()

        # Проверяем параметры запроса
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["chat_id"], "123456789")
        self.assertIn("Тестовая привычка", kwargs["json"]["text"])

    @patch("habits.tasks.settings.TELEGRAM_BOT_TOKEN", "test_token")
    @patch("habits.tasks.requests.post")
    def test_send_telegram_reminders_no_telegram_user(self, mock_post):
        """Тест когда у пользователя нет привязки к Telegram"""
        # Удаляем привязку к Telegram
        self.telegram_user.delete()

        send_telegram_reminders()

        # Проверяем, что запрос не отправлялся
        mock_post.assert_not_called()

    @patch("habits.tasks.settings.TELEGRAM_BOT_TOKEN", "")
    @patch("habits.tasks.requests.post")
    def test_send_telegram_reminders_no_token(self, mock_post):
        """Тест когда не настроен TELEGRAM_BOT_TOKEN"""
        send_telegram_reminders()
        mock_post.assert_not_called()

    @patch("habits.tasks.settings.TELEGRAM_BOT_TOKEN", "test_token")
    @patch("habits.tasks.requests.post")
    def test_send_telegram_reminders_telegram_error(self, mock_post):
        """Тест когда Telegram возвращает ошибку"""
        # Мокаем ошибку от Telegram API
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        send_telegram_reminders()

        # Проверяем, что запрос все равно был отправлен
        mock_post.assert_called_once()

    def test_send_telegram_reminders_no_habits(self):
        """Тест когда нет привычек на текущее время"""
        # Удаляем все привычки
        Habit.objects.all().delete()

        # Создаем привычку на другое время
        other_time = time(23, 59, 59)
        Habit.objects.create(user=self.user, place="Дом", time=other_time, action="Ночная привычка", duration=60)

        with patch("habits.tasks.requests.post") as mock_post:
            send_telegram_reminders()
            mock_post.assert_not_called()
