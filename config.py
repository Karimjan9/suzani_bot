from pathlib import Path

from dotenv import dotenv_values


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

env_values = dotenv_values(ENV_PATH)


def get_required_env(name: str) -> str:
    value = env_values.get(name, "").strip()
    if not value:
        raise RuntimeError(f"`.env` faylida {name} topilmadi.")
    return value


def get_optional_int(name: str) -> int | None:
    value = env_values.get(name, "").strip()
    if not value:
        return None
    return int(value)


def get_optional_float(name: str) -> float | None:
    value = env_values.get(name, "").strip()
    if not value:
        return None
    return float(value)


def get_optional_str(name: str, default: str = "") -> str:
    return env_values.get(name, default).strip()


BOT_TOKEN = get_required_env("BOT_TOKEN")
ADMIN_CHAT_ID = get_optional_int("ADMIN_CHAT_ID")
WELCOME_IMAGE_URL = get_optional_str("WELCOME_IMAGE_URL")

DB_CONFIG = {
    "host": get_optional_str("DB_HOST", "127.0.0.1"),
    "port": get_optional_int("DB_PORT") or 3306,
    "database": get_optional_str("DB_NAME", "suzani_bot"),
    "user": get_optional_str("DB_USER", "root"),
    "password": get_optional_str("DB_PASSWORD"),
    "charset": "utf8mb4",
}

TIMEZONE = "Asia/Tashkent"
STORE_NAME = "Suzani Shop"
STORE_DESCRIPTION = (
    "Milliy suzani mahsulotlari haqida ma'lumot beruvchi va foydalanuvchini kerakli "
    "sahifalarga yo'naltiruvchi rasmiy bot."
)

TELEGRAM_URL = "https://t.me/suzani_shop_admin"
INSTAGRAM_URL = "https://instagram.com/suzani_shop"
WEBSITE_URL = "https://suzanishop.uz"
MAP_URL = "https://maps.google.com/?q=Buxoro+shahri+hunarmandlar+shaharchasi"

ADDRESS = "Buxoro shahri, hunarmandlar shaharchasi"
WORK_TIME = "Dushanba - Shanba, 09:00 dan 20:00 gacha"

LOCATION_TITLE = "Suzani Shop"
LOCATION_LATITUDE = get_optional_float("LOCATION_LATITUDE")
LOCATION_LONGITUDE = get_optional_float("LOCATION_LONGITUDE")
