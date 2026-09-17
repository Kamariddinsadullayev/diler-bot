import asyncio
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8836647954:AAHcaIoFn9Dey8ccviwJ5AapCxP7gZB5Dow"
ADMIN_ID = 518579722
USERS_FILE = "users_data.json"
STATE_FILE = "bot_state.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

video_status = {
    "waiting": False,
    "last_sent_date": None
}

MONDAY_TEMPLATES = [
    "Assalomu alaykum, aka yaxshimisiz! Yangi hafta muborak bo‘lsin. Bu hafta ishlab chiqarish xom ashyolariga pul chiqarishimiz kerak edi, shuning uchun bugun va 2 yoki 3 kun bizga perechesleniya qilib turing aka, oldindan rahmat!",
    "Assalomu alaykum, hurmatli hamkor! Yangi ish haftangiz barakali kelsin. Bu haftalik ishlab chiqarish va yuk ortish rejalari shakllantirilmoqda. Yuklaringiz navbatdan kechikmasligi uchun hisob raqamimizga to'lovlarni o'tkazib turishingizni iltimos qilamiz.",
    "Assalomu alaykum, aka yaxshimisiz! Haftaning boshida yangi partiya tovarlar va xom ashyolar kirib kelmoqda. Hisob-kitoblar to'xtab qolmasligi uchun hisob raqamga mablag' tashlab berishingizni kutib qolamiz. Savdolaringizga baraka!"
]

FRIDAY_TEMPLATES = [
    "Assalomu alaykum! Juma ayyomingiz muborak bo'lsin. Bu oy perechesleniyangiz kamayib ketdi, bugun pul tashab tursangiz, shu bilan hafta tugaydi aka, kecha majlisda ham ko'rdik bu oy perechesleniyangiz kamayib ketibdi! Savdolaringizni barakasini bersin.",
    "Assalomu alaykum, Juma muborak bo'lsin! Bugun haftaning oxirgi bank ish kuni. Keyingi hafta yuklaringizni to'xtovsiz chiqarib berishimiz uchun bugun bank yopilguncha hisob raqamga to'lov qilib berishingizni so'raymiz.",
    "Assalomu alaykum, aka yaxshimisiz! Juma ayyomi qutlug' bo'lsin. Hafta yakunida filiallar hisobotlarini topshiryapmiz, siz tomoningizdan hisob raqamga to'lov qilinishi zarur edi. Bugun to'lov topshirig'ini (platejka) tashlab bersangiz juda katta yordam bo'lardi."
]

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Ulangan dilerlar ro'yxati")]
    ],
    resize_keyboard=True
)

dealer_links_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Rasmiy saytimiz", url="https://sagflooring.uz/ru")],
        [InlineKeyboardButton(text="📚 Mahsulotlar katalogi", url="https://sites.google.com/view/sag-flooring/%D0%B3%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F-%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0")],
        [InlineKeyboardButton(text="✨ Yangi kolleksiyalar", url="https://online.fliphtml5.com/rtyet/katalog_carpet-tile_UZ/#p=1")]
    ]
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

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"mon_idx": 0, "fri_idx": 0}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"mon_idx": 0, "fri_idx": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_current_text(day_type):
    state = load_state()
    if day_type == "mon":
        idx = state.get("mon_idx", 0) % len(MONDAY_TEMPLATES)
        return MONDAY_TEMPLATES[idx]
    else:
        idx = state.get("fri_idx", 0) % len(FRIDAY_TEMPLATES)
        return FRIDAY_TEMPLATES[idx]

def advance_text_index(day_type):
    state = load_state()
    if day_type == "mon":
        state["mon_idx"] = (state.get("mon_idx", 0) + 1) % len(MONDAY_TEMPLATES)
    else:
        state["fri_idx"] = (state.get("fri_idx", 0) + 1) % len(FRIDAY_TEMPLATES)
    save_state(state)

async def send_scheduled_reminder(day_type):
    today = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d")
    
    if video_status.get("last_sent_date") == today:
        return

    text = get_current_text(day_type)
    users = load_users()
    count = 0
    for uid in users.keys():
        try:
            await bot.send_message(int(uid), text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await bot.send_message(
        ADMIN_ID,
        f"📢 <b>Dilerlarga haftalik eslatma yuborildi!</b>\n\n"
        f"👥 <b>Qabul qildi:</b> {count} ta diler\n"
        f"📝 <b>Yuborilgan matn:</b>\n<i>\"{text}\"</i>",
        parse_mode="HTML"
    )
    advance_text_index(day_type)

async def trigger_admin_video_reminder():
    today_dt = datetime.now(ZoneInfo("Asia/Tashkent"))
    day_type = "mon" if today_dt.weekday() == 0 else "fri"
    
    video_status["waiting"] = True
    video_status["last_sent_date"] = None
    
    scheduled_text = get_current_text(day_type)
    
    await bot.send_message(
        ADMIN_ID,
        f"⚠️ <b>Qamariddin, diqqat!</b>\n\n"
        f"30 daqiqadan so'ng (09:30 da) dilerlarga haftalik xabarnoma boradi.\n"
        f"Iltimos, dilerlar uchun <b>dumaloq video</b> yuboring!\n\n"
        f"<i>Agar video yubormasangiz, soat 09:30 da quyidagi matn avtomatik ketadi:</i>\n"
        f"👉 <i>\"{scheduled_text}\"</i>\n\n"
        f"<i>(Video kelmasa, bot har soatda sizga eslatib turadi)</i>",
        parse_mode="HTML"
    )

async def hourly_check_video():
    today = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d")
    if video_status["waiting"] and video_status["last_sent_date"] != today:
        await bot.send_message(
            ADMIN_ID,
            "🔔 <b>Eslatma!</b>\n\n"
            "Dilerlarga yuboriladigan dumaloq video hali qabul qilinmadi. "
            "Iltimos, dumaloq video yuboring!",
            parse_mode="HTML"
        )

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user = message.from_user
    if user.id == ADMIN_ID:
        await message.answer(
            "Xush kelibsiz, Qamariddin!\n\n"
            "• Dumaloq video yuborsangiz, barcha dilerlarga yetkaziladi va eslatmalar to'xtatiladi.\n"
            "• Dilerlar yuborgan xabarlar va platejkalar shu yerga keladi.\n"
            "• Har dushanba va juma 09:00 da bot video tayyorlashni eslatadi.",
            reply_markup=admin_keyboard
        )
    else:
        save_user(user)
        dealer_welcome = (
            "🌟 <b>Assalomu alaykum, hurmatli hamkor!</b>\n"
            "🏢 <b>SAG FLOORING</b> rasmiy axborot tizimiga xush kelibsiz!\n\n"
            "Ushbu bot orqali siz:\n"
            "🌐 Rasmiy saytimiz\n"
            "📚 Mahsulotlar katalogi\n"
            "✨ Yangi kolleksiyalar va pol qoplamalari yangiliklaridan birinchilardan bo‘lib xabardor bo‘lasiz!\n\n"
            "────────────────\n"
            "💬 Savol yoki takliflaringiz bo‘lsa, to‘g‘ridan-to‘g‘ri yozib qoldiring.\n"
            "<i>Savdolaringizga ulkan baraka tilaymiz!</i> 🤝📈"
        )
        await message.answer(
            dealer_welcome,
            parse_mode="HTML",
            reply_markup=dealer_links_keyboard
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
    today = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d")
    users = load_users()
    count = 0
    for uid in users.keys():
        try:
            await bot.send_video_note(int(uid), message.video_note.file_id)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
            
    video_status["waiting"] = False
    video_status["last_sent_date"] = today
    
    await message.answer(f"✅ Dumaloq video {count} ta dilerga muvaffaqiyatli tarqatildi!\nEslatmalar to'xtatildi.")

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
    await message.answer("Xabaringiz yetkazildi. Tez orada aloqaga chiqamiz!")

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
    
    scheduler.add_job(
        trigger_admin_video_reminder,
        "cron",
        day_of_week="mon,fri",
        hour=9,
        minute=0,
        timezone="Asia/Tashkent",
    )
    
    scheduler.add_job(
        hourly_check_video,
        "cron",
        day_of_week="mon,fri",
        hour="9-18",
        minute=30,
        timezone="Asia/Tashkent",
    )
    
    scheduler.add_job(
        send_scheduled_reminder,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=30,
        timezone="Asia/Tashkent",
        args=["mon"],
    )
    
    scheduler.add_job(
        send_scheduled_reminder,
        "cron",
        day_of_week="fri",
        hour=9,
        minute=30,
        timezone="Asia/Tashkent",
        args=["fri"],
    )
    
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
