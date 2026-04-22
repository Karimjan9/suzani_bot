import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import (
    ADDRESS,
    ADMIN_CHAT_ID,
    BOT_TOKEN,
    DB_CONFIG,
    INSTAGRAM_URL,
    LOCATION_LATITUDE,
    LOCATION_LONGITUDE,
    LOCATION_TITLE,
    MAP_URL,
    STORE_NAME,
    TELEGRAM_URL,
    TIMEZONE,
    WEBSITE_URL,
    WELCOME_IMAGE_URL,
    WORK_TIME,
)
from content import LANGUAGE_NAMES, get_menu_text, get_text, normalize_language
from storage import get_stats, get_user_language, init_db, log_event, save_user_language


dp = Dispatcher()
LANGUAGE_PICKER_TEXT = (
    "Til / Язык / Language\n\n"
    "O'zingizga qulay tilni tanlang."
)


def build_language_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text=LANGUAGE_NAMES["uz"],
                    callback_data="lang:uz",
                ),
                InlineKeyboardButton(
                    text=LANGUAGE_NAMES["ru"],
                    callback_data="lang:ru",
                ),
                InlineKeyboardButton(
                    text=LANGUAGE_NAMES["en"],
                    callback_data="lang:en",
                ),
            ]
        ]
    )


def build_main_menu(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        keyboard=[
            [InlineKeyboardButton(text=get_menu_text(language, "about"), callback_data="about")],
            [InlineKeyboardButton(text=get_menu_text(language, "telegram"), url=TELEGRAM_URL)],
            [InlineKeyboardButton(text=get_menu_text(language, "instagram"), url=INSTAGRAM_URL)],
            [InlineKeyboardButton(text=get_menu_text(language, "address"), callback_data="address")],
            [InlineKeyboardButton(text=get_menu_text(language, "website"), url=WEBSITE_URL)],
        ]
    )


def get_store_status(language: str) -> str:
    now = datetime.now(ZoneInfo(TIMEZONE))
    is_open = now.weekday() < 6 and 9 <= now.hour < 20
    status_key = "status_open" if is_open else "status_closed"
    return get_text(language, status_key)


def resolve_language(user_id: int | None) -> str:
    if user_id is None:
        return "uz"
    return normalize_language(get_user_language(DB_CONFIG, user_id))


async def send_welcome(message: Message, language: str) -> None:
    text = get_text(
        language,
        "welcome",
        store_name=STORE_NAME,
        status_line=get_store_status(language),
    )
    markup = build_main_menu(language)

    if WELCOME_IMAGE_URL:
        await message.answer_photo(
            photo=WELCOME_IMAGE_URL,
            caption=text,
            reply_markup=markup,
        )
        return

    await message.answer(text, reply_markup=markup)


def build_stats_message(language: str, stats: dict[str, object]) -> str:
    lines = [
        get_text(language, "stats_title"),
        "",
        get_text(language, "stats_users", count=str(stats["users_count"])),
    ]

    languages = stats["languages"]
    events = stats["events"]

    if not languages and not events:
        lines.extend(["", get_text(language, "stats_empty")])
        return "\n".join(lines)

    if languages:
        lines.extend(["", get_text(language, "stats_languages")])
        for code, count in languages:
            lines.append(f"- {LANGUAGE_NAMES.get(code, code)}: {count}")

    if events:
        lines.extend(["", get_text(language, "stats_events")])
        for event_name, count in events:
            lines.append(f"- {get_text(language, f'event_{event_name}')}: {count}")

    return "\n".join(lines)


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    language = resolve_language(user_id)
    if user_id is not None:
        log_event(DB_CONFIG, user_id, "start", language)

    if user_id is None or get_user_language(DB_CONFIG, user_id) is None:
        await message.answer(LANGUAGE_PICKER_TEXT, reply_markup=build_language_menu())
        return

    await send_welcome(message, language)


@dp.message(Command("lang"))
async def language_handler(message: Message) -> None:
    language = resolve_language(message.from_user.id if message.from_user else None)
    await message.answer(get_text(language, "language_prompt"), reply_markup=build_language_menu())


@dp.message(Command("stats"))
async def stats_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    language = resolve_language(user_id)

    if ADMIN_CHAT_ID is None or user_id != ADMIN_CHAT_ID:
        await message.answer(get_text(language, "stats_denied"))
        return

    log_event(DB_CONFIG, user_id, "stats_viewed", language)
    await message.answer(build_stats_message(language, get_stats(DB_CONFIG)))


@dp.callback_query(F.data.startswith("lang:"))
async def language_callback_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    language = normalize_language(callback.data.split(":", maxsplit=1)[1])
    save_user_language(DB_CONFIG, callback.from_user.id, language)
    log_event(DB_CONFIG, callback.from_user.id, "language_selected", language)

    await callback.message.answer(get_text(language, "language_saved"))
    await send_welcome(callback.message, language)
    await callback.answer()


@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    log_event(DB_CONFIG, callback.from_user.id, "about", language)
    await callback.message.answer(
        get_text(
            language,
            "about",
            store_name=STORE_NAME,
            address=ADDRESS,
            work_time=WORK_TIME,
            status_line=get_store_status(language),
        )
    )
    await callback.answer()


@dp.callback_query(F.data == "address")
async def address_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    log_event(DB_CONFIG, callback.from_user.id, "address", language)
    await callback.message.answer(
        get_text(
            language,
            "address",
            address=ADDRESS,
            work_time=WORK_TIME,
            status_line=get_store_status(language),
            map_url=MAP_URL,
        )
    )

    if LOCATION_LATITUDE is not None and LOCATION_LONGITUDE is not None:
        await callback.message.answer_venue(
            latitude=LOCATION_LATITUDE,
            longitude=LOCATION_LONGITUDE,
            title=LOCATION_TITLE,
            address=ADDRESS,
        )
        await callback.answer(get_text(language, "location_sent"))
        return

    await callback.answer()


@dp.message()
async def fallback_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    stored_language = get_user_language(DB_CONFIG, user_id) if user_id is not None else None
    if stored_language is None:
        await message.answer(LANGUAGE_PICKER_TEXT, reply_markup=build_language_menu())
        return

    language = normalize_language(stored_language)
    await message.answer(
        get_text(language, "fallback", store_name=STORE_NAME),
        reply_markup=build_main_menu(language),
    )


async def main() -> None:
    init_db(DB_CONFIG)
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
