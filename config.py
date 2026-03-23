from pathlib import Path

from dotenv import dotenv_values


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


def get_bot_token() -> str:
    env_values = dotenv_values(ENV_PATH)
    token = env_values.get("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("`.env` faylida BOT_TOKEN topilmadi.")
    return token


BOT_TOKEN = get_bot_token()

STORE_NAME = "Suzani Shop"
STORE_DESCRIPTION = (
    "Milliy suzani mahsulotlari haqida ma'lumot beruvchi va foydalanuvchini kerakli "
    "sahifalarga yo'naltiruvchi rasmiy bot."
)
TELEGRAM_URL = "https://t.me/suzani_shop_admin"
INSTAGRAM_URL = "https://instagram.com/suzani_shop"
WEBSITE_URL = "https://suzanishop.uz"
MAP_URL = "https://maps.google.com/?q=Toshkent+shahri+Chilonzor+tumani"
ADDRESS = "Toshkent shahri, Chilonzor tumani"
WORK_TIME = "Dushanba - Shanba, 09:00 dan 20:00 gacha"

ABOUT_TEXT = (
    f"{STORE_NAME} haqida\n\n"
    f"{STORE_DESCRIPTION}\n\n"
    f"Manzil: {ADDRESS}\n"
    f"Ish vaqti: {WORK_TIME}"
)

WELCOME_TEXT = (
    f"Assalomu alaykum, {STORE_NAME} botiga xush kelibsiz.\n\n"
    "Bu bot savdo qilmaydi. U sizni rasmiy sahifalarimiz va bog'lanish "
    "kanallarimizga yo'naltiradi.\n\n"
    "Quyidagi tugmalardan birini tanlang."
)

ADDRESS_TEXT = (
    f"Manzilimiz: {ADDRESS}\n"
    f"Ish vaqti: {WORK_TIME}\n\n"
    f"Xarita havolasi: {MAP_URL}"
)
