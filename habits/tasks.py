from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import Habit
from users.models import TelegramUser
import requests


@shared_task
def send_telegram_reminders():
    """Отправка напоминаний о привычках через Telegram"""
    print("=== ЗАПУСК ЗАДАЧИ TELEGRAM REMINDERS ===")

    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не настроен")
        return

    now = timezone.now()
    current_time = now.time()
    print(f"🕐 Текущее время: {current_time}")

    # Получаем привычки, которые нужно выполнить в текущее время
    habits = Habit.objects.filter(time__hour=current_time.hour, time__minute=current_time.minute)
    print(f"📝 Найдено привычек: {habits.count()}")

    for habit in habits:
        print(f"🔍 Обрабатываем привычку: {habit.action} для пользователя {habit.user.username}")

        try:
            # Проверяем, есть ли у пользователя привязка к Telegram
            telegram_user = TelegramUser.objects.filter(user=habit.user).first()
            if not telegram_user:
                print(f"❌ У пользователя {habit.user.username} нет привязки к Telegram")
                continue

            chat_id = telegram_user.chat_id
            print(f"💬 Chat ID: {chat_id}")

            # Формируем сообщение
            message = f"Я буду {habit.action} в {habit.place}"

            if habit.reward:
                message += f"\nВознаграждение: {habit.reward}"
            elif habit.related_habit:
                message += f"\nСвязанная привычка: {habit.related_habit.action}"

            print(f"📤 Отправляем сообщение: {message}")

            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}

            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"✅ Успешно отправлено пользователю {habit.user.username}")
            else:
                print(f"❌ Ошибка отправки: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Неизвестная ошибка для {habit.user.username}: {e}")

    print("=== ЗАВЕРШЕНИЕ ЗАДАЧИ ===")
