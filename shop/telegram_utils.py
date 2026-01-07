# shop/telegram_utils.py
import requests
from django.conf import settings
from asgiref.sync import sync_to_async
import aiohttp
import asyncio


def send_application_to_admin(application):
    """
    Yangi do'kon arizasini Telegram bot orqali adminga yuborish
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID

    if not bot_token or not admin_chat_id:
        print("Telegram bot sozlanmagan!")
        return False

    # Xabar matni
    message = f"""
🆕 <b>YANGI DO'KON ARIZASI</b>

👤 <b>Foydalanuvchi:</b> @{application.user.username}
📛 <b>Ism-familiya:</b> {application.owner_full_name}
🏪 <b>Do'kon nomi:</b> {application.shop_name}
📁 <b>Kategoriya:</b> {application.category.name}
📞 <b>Telefon:</b> {application.phone_number}

💬 <b>Qo'shimcha ma'lumot:</b>
{application.description}

📅 <b>Ariza sanasi:</b> {application.created_at.strftime("%d.%m.%Y %H:%M")}
🆔 <b>Ariza ID:</b> {application.id}
"""

    # Inline tugmalar
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ Qabul qilish",
                    "callback_data": f"approve_{application.id}",
                },
                {"text": "❌ Rad etish", "callback_data": f"reject_{application.id}"},
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": admin_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": keyboard,
            },
            timeout=10,
        )

        if response.status_code == 200:
            print(f"Ariza #{application.id} adminga yuborildi")
            return True
        else:
            print(f"Xatolik: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"Telegram xatolik: {e}")
        return False


async def send_application_to_admin_async(application):
    """Async versiyasi"""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID

    if not bot_token or not admin_chat_id:
        return False

    message = f"""
🆕 <b>YANGI DO'KON ARIZASI</b>

👤 <b>Foydalanuvchi:</b> @{application.user.username}
📛 <b>Ism-familiya:</b> {application.owner_full_name}
🏪 <b>Do'kon nomi:</b> {application.shop_name}
📁 <b>Kategoriya:</b> {application.category.name}
📞 <b>Telefon:</b> {application.phone_number}

💬 <b>Qo'shimcha ma'lumot:</b>
{application.description}

📅 <b>Ariza sanasi:</b> {application.created_at.strftime("%d.%m.%Y %H:%M")}
🆔 <b>Ariza ID:</b> {application.id}
"""

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✅ Qabul qilish",
                    "callback_data": f"approve_{application.id}",
                },
                {"text": "❌ Rad etish", "callback_data": f"reject_{application.id}"},
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={
                    "chat_id": admin_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    print(f"Ariza #{application.id} adminga yuborildi (async)")
                    return True
                else:
                    text = await response.text()
                    print(f"Xatolik: {response.status} - {text}")
                    return False

    except Exception as e:
        print(f"Telegram async xatolik: {e}")
        return False


def send_application_status(application, status):
    """
    Ariza holati haqida foydalanuvchiga xabar yuborish
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token:
        return False

    # Hozircha foydalanuvchining Telegram ID sini olish uchun modelga qo'shish kerak
    # Agar User modelida telegram_id field bo'lsa:
    # telegram_id = application.user.telegram_id

    if status == "approved":
        message = f"""
✅ <b>ARIZANGIZ QABUL QILINDI!</b>

Tabriklaymiz! Sizning "{application.shop_name}" do'koningiz tasdiqlandi.

Endi siz tizimga kirib do'koningizni to'liq boshqarishingiz mumkin.

🌐 Saytga kirish: http://127.0.0.1:8000
"""
    else:
        message = f"""
❌ <b>ARIZANGIZ RAD ETILDI</b>

Afsuski, "{application.shop_name}" do'koni uchun arizangiz rad etildi.

Iltimos, yangi ariza qoldirib ko'ring yoki qo'llab-quvvatlash bilan bog'laning.
"""

    print(f"Foydalanuvchiga yuborilishi kerak: {message}")

    # Agar telegram_id bo'lsa:
    # if telegram_id:
    #     url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    #     requests.post(url, json={
    #         "chat_id": telegram_id,
    #         "text": message,
    #         "parse_mode": "HTML"
    #     })

    return True
