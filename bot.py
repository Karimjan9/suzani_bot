import asyncio
import random
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    User,
)

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
    WELCOME_BANNER_DIR,
    WELCOME_BANNER_MODE,
    WEBSITE_URL,
    WELCOME_IMAGE_URL,
    WORK_TIME,
)
from content import LANGUAGE_NAMES, get_menu_text, get_text, get_welcome_variants, normalize_language
from storage import (
    get_stats,
    get_user_language,
    has_user_activity,
    init_db,
    log_event,
    save_lead,
    save_user_language,
)


FAQ_TOPICS = ("prices", "delivery", "payment", "timeline", "custom")
LEAD_TYPE_LABEL_KEYS = {
    "question": "ask_question",
    "contact": "leave_contact",
}
CANCEL_TEXTS = {
    "❌ Bekor qilish",
    "❌ Отмена",
    "❌ Cancel",
}
PHONE_ALLOWED_PATTERN = re.compile(r"^\+?[0-9 ()-]{7,20}$")
WELCOME_BANNER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_interest = State()


dp = Dispatcher()
LANGUAGE_PICKER_TEXT = (
    "🌐 Til / Язык / Language\n\n"
    "✨ O'zingizga qulay tilni tanlang."
)
WELCOME_ROTATION_INDEX = 0
WELCOME_BANNER_FILES = tuple(
    path
    for path in sorted(WELCOME_BANNER_DIR.iterdir())
    if path.is_file() and path.suffix.lower() in WELCOME_BANNER_EXTENSIONS
) if WELCOME_BANNER_DIR.exists() else ()


def build_language_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LANGUAGE_NAMES["uz"], callback_data="lang:uz"),
                InlineKeyboardButton(text=LANGUAGE_NAMES["ru"], callback_data="lang:ru"),
                InlineKeyboardButton(text=LANGUAGE_NAMES["en"], callback_data="lang:en"),
            ]
        ]
    )


def build_main_menu(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_menu_text(language, "about"), callback_data="about")],
            [InlineKeyboardButton(text=get_menu_text(language, "telegram"), callback_data="telegram")],
            [InlineKeyboardButton(text=get_menu_text(language, "instagram"), url=INSTAGRAM_URL)],
            [InlineKeyboardButton(text=get_menu_text(language, "address"), callback_data="address")],
            [InlineKeyboardButton(text=get_menu_text(language, "website"), url=WEBSITE_URL)],
            [InlineKeyboardButton(text=get_menu_text(language, "faq"), callback_data="faq")],
            [InlineKeyboardButton(text=get_menu_text(language, "lead"), callback_data="lead")],
        ]
    )


def build_faq_menu(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_menu_text(language, "prices"), callback_data="faq:prices"),
                InlineKeyboardButton(text=get_menu_text(language, "delivery"), callback_data="faq:delivery"),
            ],
            [
                InlineKeyboardButton(text=get_menu_text(language, "payment"), callback_data="faq:payment"),
                InlineKeyboardButton(text=get_menu_text(language, "timeline"), callback_data="faq:timeline"),
            ],
            [
                InlineKeyboardButton(text=get_menu_text(language, "custom"), callback_data="faq:custom"),
            ],
            [
                InlineKeyboardButton(text=get_menu_text(language, "back"), callback_data="back_main"),
            ],
        ]
    )


def build_lead_menu(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_menu_text(language, "ask_question"),
                    callback_data="lead:question",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_menu_text(language, "leave_contact"),
                    callback_data="lead:contact",
                )
            ],
            [
                InlineKeyboardButton(text=get_menu_text(language, "back"), callback_data="back_main"),
            ],
        ]
    )


def build_telegram_menu(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_menu_text(language, "open_telegram"),
                    url=TELEGRAM_URL,
                )
            ],
            [
                InlineKeyboardButton(text=get_menu_text(language, "back"), callback_data="back_main"),
            ],
        ]
    )


def build_phone_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_menu_text(language, "share_phone"), request_contact=True)],
            [KeyboardButton(text=get_menu_text(language, "cancel"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_cancel_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_menu_text(language, "cancel"))]],
        resize_keyboard=True,
        one_time_keyboard=True,
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


def get_user_display_name(user: User) -> str:
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
    return full_name or "Unknown"


def get_user_username(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    return "-"


def is_cancel_text(text: str | None) -> bool:
    if not text:
        return False
    return text.strip() in CANCEL_TEXTS


def is_valid_phone_number(phone_number: str) -> bool:
    digits_only = re.sub(r"\D", "", phone_number)
    return len(digits_only) >= 7 and len(digits_only) <= 15 and bool(
        PHONE_ALLOWED_PATTERN.fullmatch(phone_number.strip())
    )


def get_welcome_rotation_index() -> int | None:
    global WELCOME_ROTATION_INDEX

    if WELCOME_BANNER_MODE == "random":
        return None

    rotation_index = WELCOME_ROTATION_INDEX
    WELCOME_ROTATION_INDEX += 1
    return rotation_index


def get_welcome_photo(rotation_index: int | None) -> FSInputFile | str | None:

    if WELCOME_BANNER_FILES:
        if rotation_index is None:
            banner_path = random.choice(WELCOME_BANNER_FILES)
        else:
            banner_path = WELCOME_BANNER_FILES[rotation_index % len(WELCOME_BANNER_FILES)]

        return FSInputFile(Path(banner_path))

    if WELCOME_IMAGE_URL:
        return WELCOME_IMAGE_URL

    return None


def get_welcome_text(language: str, rotation_index: int | None) -> str:
    variants = get_welcome_variants(
        language,
        store_name=STORE_NAME,
        status_line=get_store_status(language),
    )
    if rotation_index is None:
        return random.choice(variants)
    return variants[rotation_index % len(variants)]


async def notify_admin_activity(
    bot: Bot,
    user: User,
    language: str,
    title: str,
    details: list[str] | None = None,
) -> None:
    if ADMIN_CHAT_ID is None or user.id == ADMIN_CHAT_ID:
        return

    lines = [
        f"🔔 {title}",
        "",
        f"Foydalanuvchi: {get_user_display_name(user)}",
        f"Username: {get_user_username(user)}",
        f"ID: {user.id}",
        f"Til: {LANGUAGE_NAMES.get(language, language)}",
    ]
    if details:
        lines.extend(["", *details])

    try:
        await bot.send_message(ADMIN_CHAT_ID, "\n".join(lines))
    except Exception:
        return


async def notify_admin_lead(
    bot: Bot,
    user: User,
    language: str,
    lead_type: str,
    full_name: str,
    phone: str,
    interest: str,
) -> None:
    lead_label = get_menu_text(language, LEAD_TYPE_LABEL_KEYS.get(lead_type, "ask_question"))
    await notify_admin_activity(
        bot,
        user,
        language,
        "Yangi murojaat yuborildi",
        [
            f"Turi: {lead_label}",
            f"Ism: {full_name}",
            f"Telefon: {phone}",
            f"Qiziqish: {interest}",
        ],
    )


async def clear_active_flow(message: Message, state: FSMContext, language: str) -> None:
    if await state.get_state() is None:
        return

    await state.clear()
    await message.answer(
        get_text(language, "lead_cancelled"),
        reply_markup=ReplyKeyboardRemove(),
    )


async def send_welcome(message: Message, language: str) -> None:
    rotation_index = get_welcome_rotation_index()
    text = get_welcome_text(language, rotation_index)
    markup = build_main_menu(language)

    photo = get_welcome_photo(rotation_index)
    if photo is not None:
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=markup,
        )
        return

    await message.answer(text, reply_markup=markup)


async def send_main_menu(message: Message, language: str) -> None:
    await message.answer(
        get_text(language, "fallback", store_name=STORE_NAME),
        reply_markup=build_main_menu(language),
    )


def build_stats_message(language: str, stats: dict[str, object]) -> str:
    lines = [
        get_text(language, "stats_title"),
        "",
        get_text(language, "stats_users", count=str(stats["users_count"])),
        get_text(language, "stats_leads", count=str(stats["leads_count"])),
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
            event_label_key = f"event_{event_name}"
            try:
                event_label = get_text(language, event_label_key)
            except KeyError:
                event_label = event_name
            lines.append(f"- {event_label}: {count}")

    return "\n".join(lines)


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    user_id = user.id if user else None
    language = resolve_language(user_id)

    await clear_active_flow(message, state, language)

    is_new_user = user_id is not None and not has_user_activity(DB_CONFIG, user_id)

    if user_id is not None:
        log_event(DB_CONFIG, user_id, "start", language)

    stored_language = get_user_language(DB_CONFIG, user_id) if user_id is not None else None

    if is_new_user and user is not None:
        await notify_admin_activity(
            message.bot,
            user,
            language,
            "Yangi foydalanuvchi /start bosdi",
        )

    if stored_language is None:
        await message.answer(LANGUAGE_PICKER_TEXT, reply_markup=build_language_menu())
        return

    await send_welcome(message, language)


@dp.message(Command("lang"))
async def language_handler(message: Message, state: FSMContext) -> None:
    language = resolve_language(message.from_user.id if message.from_user else None)
    await clear_active_flow(message, state, language)
    await message.answer(get_text(language, "language_prompt"), reply_markup=build_language_menu())


@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else None
    language = resolve_language(user_id)
    stored_language = get_user_language(DB_CONFIG, user_id) if user_id is not None else None

    if await state.get_state() is None:
        if stored_language is None:
            await message.answer(LANGUAGE_PICKER_TEXT, reply_markup=build_language_menu())
            return
        await send_main_menu(message, language)
        return

    await clear_active_flow(message, state, language)
    await send_main_menu(message, language)


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
async def language_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    language = normalize_language(callback.data.split(":", maxsplit=1)[1])
    await clear_active_flow(callback.message, state, language)

    save_user_language(DB_CONFIG, callback.from_user.id, language)
    log_event(DB_CONFIG, callback.from_user.id, "language_selected", language)

    await callback.message.answer(
        get_text(language, "language_saved"),
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_welcome(callback.message, language)
    await callback.answer()


@dp.callback_query(F.data == "back_main")
async def back_main_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    await send_main_menu(callback.message, language)
    await callback.answer()


@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
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


@dp.callback_query(F.data == "faq")
async def faq_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    log_event(DB_CONFIG, callback.from_user.id, "faq_opened", language)
    await callback.message.answer(
        get_text(language, "faq_intro"),
        reply_markup=build_faq_menu(language),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("faq:"))
async def faq_topic_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    topic = callback.data.split(":", maxsplit=1)[1]
    if topic not in FAQ_TOPICS:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    await callback.message.answer(
        get_text(language, f"faq_{topic}"),
        reply_markup=build_faq_menu(language),
    )
    await callback.answer()


@dp.callback_query(F.data == "telegram")
async def telegram_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    log_event(DB_CONFIG, callback.from_user.id, "telegram_clicked", language)
    await notify_admin_activity(
        callback.bot,
        callback.from_user,
        language,
        "Telegram aloqa tugmasi bosildi",
    )
    await callback.message.answer(
        get_text(language, "telegram_prompt"),
        reply_markup=build_telegram_menu(language),
    )
    await callback.answer()


@dp.callback_query(F.data == "address")
async def address_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    log_event(DB_CONFIG, callback.from_user.id, "address", language)
    await notify_admin_activity(
        callback.bot,
        callback.from_user,
        language,
        "Manzil bo'limi ochildi",
    )
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


@dp.callback_query(F.data == "lead")
async def lead_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    await clear_active_flow(callback.message, state, language)
    await callback.message.answer(
        get_text(language, "lead_intro"),
        reply_markup=build_lead_menu(language),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("lead:"))
async def lead_type_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    lead_type = callback.data.split(":", maxsplit=1)[1]
    if lead_type not in LEAD_TYPE_LABEL_KEYS:
        await callback.answer()
        return

    language = resolve_language(callback.from_user.id)
    log_event(DB_CONFIG, callback.from_user.id, "lead_started", language)
    await state.set_state(LeadForm.waiting_name)
    await state.update_data(lead_type=lead_type)
    await callback.message.answer(
        get_text(language, "lead_name_prompt"),
        reply_markup=build_cancel_keyboard(language),
    )
    await callback.answer()


@dp.message(LeadForm.waiting_name)
async def lead_name_handler(message: Message, state: FSMContext) -> None:
    language = resolve_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await clear_active_flow(message, state, language)
        await send_main_menu(message, language)
        return

    full_name = (message.text or "").strip()
    if not full_name:
        await message.answer(
            get_text(language, "lead_name_invalid"),
            reply_markup=build_cancel_keyboard(language),
        )
        return

    await state.update_data(full_name=full_name)
    await state.set_state(LeadForm.waiting_phone)
    await message.answer(
        get_text(language, "lead_phone_prompt"),
        reply_markup=build_phone_keyboard(language),
    )


@dp.message(LeadForm.waiting_phone)
async def lead_phone_handler(message: Message, state: FSMContext) -> None:
    language = resolve_language(message.from_user.id if message.from_user else None)

    if is_cancel_text(message.text):
        await clear_active_flow(message, state, language)
        await send_main_menu(message, language)
        return

    phone_number = ""
    if message.contact and message.contact.phone_number:
        phone_number = message.contact.phone_number.strip()
    elif message.text:
        phone_number = message.text.strip()

    if not phone_number or not is_valid_phone_number(phone_number):
        await message.answer(
            get_text(language, "lead_phone_invalid"),
            reply_markup=build_phone_keyboard(language),
        )
        return

    await state.update_data(phone=phone_number)
    await state.set_state(LeadForm.waiting_interest)
    await message.answer(
        get_text(language, "lead_interest_prompt"),
        reply_markup=build_cancel_keyboard(language),
    )


@dp.message(LeadForm.waiting_interest)
async def lead_interest_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    language = resolve_language(user.id if user else None)

    if is_cancel_text(message.text):
        await clear_active_flow(message, state, language)
        await send_main_menu(message, language)
        return

    interest = (message.text or "").strip()
    if not interest:
        await message.answer(
            get_text(language, "lead_interest_invalid"),
            reply_markup=build_cancel_keyboard(language),
        )
        return

    data = await state.get_data()
    lead_type = str(data.get("lead_type", "question"))
    full_name = str(data.get("full_name", "")).strip()
    phone_number = str(data.get("phone", "")).strip()

    await state.clear()

    if user is not None:
        save_lead(
            DB_CONFIG,
            user.id,
            lead_type,
            full_name,
            phone_number,
            interest,
            user.username or "",
            language,
        )
        log_event(DB_CONFIG, user.id, "lead_submitted", language)
        await notify_admin_lead(
            message.bot,
            user,
            language,
            lead_type,
            full_name,
            phone_number,
            interest,
        )

    await message.answer(
        get_text(
            language,
            "lead_saved",
            lead_type=get_menu_text(language, LEAD_TYPE_LABEL_KEYS.get(lead_type, "ask_question")),
        ),
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_main_menu(message, language)


@dp.message()
async def fallback_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    stored_language = get_user_language(DB_CONFIG, user_id) if user_id is not None else None
    if stored_language is None:
        await message.answer(LANGUAGE_PICKER_TEXT, reply_markup=build_language_menu())
        return

    language = normalize_language(stored_language)
    await send_main_menu(message, language)


async def main() -> None:
    init_db(DB_CONFIG)
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
