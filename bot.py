import asyncio
import json
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8836647954:AAHcaIoFn9Dey8ccviwJ5AapCxP7gZB5Dow"
ADMIN_ID = 518579722
USERS_FILE = "users_data.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Ulangan dilerlar ro'yxati")]
    ],
    resize_keyboard=True
)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_user(user: types.User):
    users = load_users()
    str_id = str(user.id)
    users[str_id] = {
        "name": user.full_name,
        "username": f"@{user.username}" if user.username else "mavjud emas"
    }
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

async def send_scheduled_reminder(text):
    users = load_users()
    for uid in users.keys():
        try:
            await bot.send_message(int(uid), text)
            await asyncio.sleep(0.05)
        except Exception:
            pass

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user = message.from_user
    if user.id == ADMIN_ID:
        await message.answer(
            "Xush kelibsiz, Qamariddin!\n\n"
            "• Dumaloq video yoki matn yuborsangiz, barcha dilerlarga tarqatiladi.\n"
            "• Dilerlar yuborgan to'lov topshiriqlari (platejkalar) va xabarlar shu yerga keladi.\n"
            "• Quyidagi tugma orqali ulangan dilerlarni ko'rishingiz mumkin.",
            reply_markup=admin_keyboard
        )
    else:
        save_user(user)
        await message.answer(
            "Assalomu alaykum, hurmatli hamkor!\n\n"
            "Bu bizning rasmiy axborot va to'lov bildirishnomalari botimiz.\n"
            "Kompaniya hisob raqamiga to'lov qilingandan so'ng, to'lov topshirig'ini (platejka) shu yerga rasm yoki fayl shaklida yuborishingiz mumkin.\n"
            "Shuningdek, savollaringiz bo'lsa to'g'ridan-to'g'ri xabar yozishingiz mumkin."
        )

@dp.message(F.from_user.id == ADMIN_ID, F.text == "👥 Ulangan dilerlar ro'yxati")
async def show_dealers_list(message: types.Message):
    users = load_users()
    if not users:
        await message.answer("Hozircha botga birorta ham diler ulanmagan.")
        return

    text = f"📋 <b>Ulangan dilerlar soni: {len(users)} ta</b>\n\n"
    for i, (uid, data) in enumerate(users.items(), start=1):
        text += f"{i}. {data['name']} ({data['username']}) | ID: <code>{uid}</code>\n"

    await message.answer(text, parse_mode="HTML")

@dp.message(F.from_user.id == ADMIN_ID, F.video_note)
async def admin_video_note(message: types.Message):
    users = load_users()
    count = 0
    for uid in users.keys():
        try:
            await bot.send_video_note(int(uid), message.video_note.file_id)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"Dumaloq video {count} ta dilerga yuborildi!")

@dp.message(F.from_user.id == ADMIN_ID, F.text & ~F.text.startswith("/"))
async def admin_broadcast_text(message: types.Message):
    users = load_users()
    count = 0
    for uid in users.keys():
        try:
            await bot.send_message(int(uid), message.text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"Xabar {count} ta dilerga yuborildi!")

# Dilerlardan kelgan rasmlar yoki hujjatlarni (platejka) qabul qilish
@dp.message(F.from_user.id != ADMIN_ID, F.photo | F.document)
async def diler_payment_slip(message: types.Message):
    user = message.from_user
    full_name = user.full_name
    username = f"@{user.username}" if user.username else "mavjud emas"
    caption = f"📄 <b>Yangi to'lov topshirig'i (platejka)!</b>\n\nKimdan: {full_name} ({username})\nID: <code>{user.id}</code>"
    
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, parse_mode="HTML")
    await message.answer("To'lov topshirig'i qabul qilindi. Rahmat!")

# Dilerlardan kelgan matnli xabarlarni adminga yetkazish
@dp.message(F.from_user.id != ADMIN_ID, F.text & ~F.text.startswith("/"))
async def diler_text_message(message: types.Message):
    user = message.from_user
    full_name = user.full_name
    username = f"@{user.username}" if user.username else "mavjud emas"
    
    admin_notify = (
        f"💬 <b>Dilerdan yangi xabar!</b>\n\n"
        f"<b>Kimdan:</b> {full_name} ({username})\n"
        f"<b>ID:</b> <code>{user.id}</code>\n\n"
        f"<b>Xabar matni:</b>\n{message.text}"
    )
    
    await bot.send_message(ADMIN_ID, admin_notify, parse_mode="HTML")
    await message.answer("Xabaringiz mas'ul xodimga yetkazildi. Tez orada javob beramiz!")

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    
    # Dushanba 09:30 (Toshkent vaqti)
    scheduler.add_job(
        send_scheduled_reminder,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=30,
        timezone="Asia/Tashkent",
        args=["Assalomu alaykum, hurmatli hamkorlar! Yangi hafta boshlandi. Navbatni ushlab qolish va rejalashtirilgan yuklarni o'z vaqtida chiqarish uchun firma hisob raqamimizga to'lovlarni o'tkazishingizni so'raymiz."],
    )
    
    # Juma 09:30 (Toshkent vaqti)
    scheduler.add_job(
        send_scheduled_reminder,
        "cron",
        day_of_week="fri",
        hour=9,
        minute=30,
        timezone="Asia/Tashkent",
        args=["Assalomu alaykum, hurmatli hamkorlar! Bugun hafta yakuni va bank amaliyotlari kuni. Yuk kutib qolmasligi va navbat kechikmasligi uchun hisob raqamdan to'lovni bugun amalga oshirishingizni so'raymiz."],
    )
    
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
