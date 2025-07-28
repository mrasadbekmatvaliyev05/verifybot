import asyncio
import logging
import aiohttp
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.enums import ContentType
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

# Load .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL_ADD = os.getenv("API_URL_ADD")
API_URL_LOGIN = os.getenv("API_URL_LOGIN")
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Telefon raqam so‘rash uchun tugma
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
        f"🇺🇿\n"
        f"Salom {full_name} 👋\n"
        f"@trustfund_uz'ning rasmiy botiga xush kelibsiz\n\n"
        f"⬇️ Kontaktingizni yuboring (tugmani bosib)\n\n"
        f"🇺🇸\n"
        f"Hi {full_name} 👋\n"
        f"Welcome to @trustfund_uz's official bot\n\n"
        f"⬇️ Send your contact (by clicking the button)",
        reply_markup=request_phone_kb
    )

@dp.message(lambda message: message.content_type == ContentType.CONTACT)
async def contact_handler(message: types.Message):
    contact = message.contact
    name = message.from_user.full_name
    phone = contact.phone_number
    telegram_id = contact.user_id

    data = {
        "name": name,
        "telegramId": str(telegram_id),
        "phoneNumber": phone
    }

    headers = {
        "X-Telegram-Token": TELEGRAM_SECRET_TOKEN
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL_ADD, json=data, headers=headers) as resp:
                if resp.status == 200:
                    response_data = await resp.json()
                    code = response_data.get("code", "kod topilmadi")
                    await message.answer(f"🔒 Code: `{code}`", parse_mode="Markdown")
                else:
                    await message.answer("❌ API bilan muammo. Keyinroq urinib ko‘ring.")
    except Exception as e:
        logging.error(f"API xatosi: {e}")
        await message.answer("⚠️ Server ishlamayapti yoki ulanib bo‘lmadi.")

@dp.message(Command("login"))
async def login_handler(message: types.Message):
    telegram_id = message.from_user.id
    data = {
        "telegramId": str(telegram_id)
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL_LOGIN, json=data) as resp:
                response_data = await resp.json()
                if resp.status == 200:
                    code = response_data.get("code", "kod topilmadi")
                    await message.answer(f"🔐 Sizning OTP kodingiz: `{code}`", parse_mode="Markdown")
                elif resp.status == 429:
                    await message.answer("🔐 Eski kodingiz hali ham kuchda ☝️")
                else:
                    msg = response_data.get("message", "Xatolik yuz berdi.")
                    await message.answer(f"❌ Muammo: {msg}")
    except Exception as e:
        logging.error(f"Login API xatosi: {e}")
        await message.answer("⚠️ Serverga ulanib bo‘lmadi.")

# Botni ishga tushirish
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
