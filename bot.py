import asyncio
import json
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8836647954:AAHcaIoFn9Dey8ccviwJ5AapCxP7gZB5Dow"
ADMIN_ID = 518579722

USERS_FILE = "users.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

async def send_scheduled_reminder(text):
    users = load_users()
    for uid in users:
        try:
            await bot.send_message(uid, text)
            await asyncio.sleep(0.05)
        except Exception:
            pass

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer(
            "Xush kelibsiz, Admin!\n\n"
            "• Dumaloq video yoki matn yuborsangiz, tasdiqlash orqali barcha dilerlarga tarqatishingiz mumkin.\n"
            "• Dilerlar yuborgan to'lov cheklari (platejkalar) shu yerga keladi."
        )
    else:
        save_user(user_id)
        await message.answer(
            "Assalomu alaykum, hurmatli hamkor!\n\n"
            "Bu bizning rasmiy to'lov va axborot bildirishnomalari botimiz.\n"
            "Kompaniya hisob raqamiga to'lov qilingandan so'ng, to'lov topshirig'ini (platejka) shu yerga rasm yoki PDF shaklida yuborishingiz mumkin."
        )

@dp.message(F.from_user.id == ADMIN_ID, F.video_note)
async def admin_video_note(message: types.Message):
    users = load_users()
    count = 0
    for uid in users:
        try:
            await bot.send_video_note(uid, message.video_note.file_id)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"Dumaloq video {count} ta dilerga muvaffaqiyatli yuborildi!")

@dp.message(F.from_user.id == ADMIN_ID, F.text & ~F.text.startswith("/"))
async def admin_broadcast_text(message: types.Message):
    users = load_users()
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, message.text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"Xabar {count} ta dilerga muvaffaqiyatli yuborildi!")

@dp.message(F.from_user.id != ADMIN_ID, F.photo | F.document)
async def diler_payment_slip(message: types.Message):
    user = message.from_user
    full_name = user.full_name
    username = f"@{user.username}" if user.username else "mavjud emas"
    
    caption = f"Yangi to'lov topshirig'i (platejka)!\n\nKimdan: {full_name} ({username})\nID: {user.id}"
    
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
        
    await message.answer("To'lov topshirig'i qabul qilindi. Tez orada hisobingizga kiritiladi. Rahmat!")

async def main():
    scheduler.add_job(
        send_scheduled_reminder,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=30,
        args=["Assalomu alaykum, hurmatli hamkorlar! Yangi hafta boshlandi. Ushbu haftada rejalashtirilgan yuklaringizni o'z vaqtida chiqarish uchun firma hisob raqamimizga to'lovlarni o'tkazishingizni so'raymiz."],
    )
    scheduler.add_job(
        send_scheduled_reminder,
        "cron",
        day_of_week="wed",
        hour=11,
        minute=0,
        args=["Hurmatli hamkor, firma hisob raqamimizga to'lov amalga oshirilgan bo'lsa, to'lov topshirig'ini (platejka) botga yuklashingizni so'raymiz."],
    )
    scheduler.add_job(
        send_scheduled_reminder,
        "cron",
        day_of_week="fri",
        hour=10,
        minute=0,
        args=["Diqqat! Bank operatsiyalari yakunlanishiga oz vaqt qoldi. Dushanbagacha yuk kutib qolmasligi uchun hisob raqamdan to'lovni bugun soat 16:00 gacha amalga oshirishingizni so'raymiz."],
    )
    
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
