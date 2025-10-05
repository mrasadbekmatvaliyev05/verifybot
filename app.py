import asyncio
import logging
import aiohttp
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.enums import ContentType
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL_ADD = os.getenv("API_URL_ADD")
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Telefon raqam so‘rash tugmasi
request_phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    full_name = message.from_user.full_name
    await message.answer(
        f"🇺🇿 Salom {full_name} 👋\n"
        f"@trustfund_uz botiga xush kelibsiz!\n\n"
        f"⬇️ Kontaktingizni yuboring:",
        reply_markup=request_phone_kb
    )


@dp.message(lambda message: message.content_type == ContentType.CONTACT)
async def contact_handler(message: types.Message):
    contact = message.contact
    name = message.from_user.first_name
    phone = contact.phone_number
    telegram_id = contact.user_id

    if contact.user_id != message.from_user.id:
        await message.answer("❌ Faqat o'zingizning raqamingizni yuborishingiz mumkin.")
        return

    data = {
        "telegram_id": telegram_id,
        "first_name": name,
        "phone": phone
    }

    headers = {
        "Content-Type": "application/json",
        "X-Telegram-Token": TELEGRAM_SECRET_TOKEN or ""
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL_ADD, json=data, headers=headers) as resp:
                response_data = await resp.json()

                if resp.status == 200:
                    otp = response_data.get("otp")
                    expires_at = response_data.get("expires_at")
                    status = response_data.get("status")

                    # vaqtni formatlash
                    formatted_time = "noma’lum"
                    if expires_at:
                        try:
                            dt = datetime.fromisoformat(expires_at.replace("Z", ""))
                            formatted_time = dt.strftime("%d.%m.%Y %H:%M")
                        except Exception:
                            pass

                    if otp and status == "ok":
                        await message.answer(
                            f"🔢 *Kod:* `{otp}`\n"
                            f"⏰ Amal qilish muddati: *{formatted_time}*",
                            parse_mode="Markdown"
                        )
                    else:
                        await message.answer("⚠️ Noma’lum javob olindi.")
                else:
                    await message.answer(f"❌ API xato: {resp.status}")
    except Exception as e:
        logging.error(f"API xatosi: {e}")
        await message.answer("⚠️ Server bilan aloqa o‘rnatilmadi.")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
