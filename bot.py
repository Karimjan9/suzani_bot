import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import (
    ABOUT_TEXT,
    ADDRESS_TEXT,
    BOT_TOKEN,
    INSTAGRAM_URL,
    STORE_NAME,
    TELEGRAM_URL,
    WEBSITE_URL,
    WELCOME_TEXT,
)


def build_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        keyboard=[
            [InlineKeyboardButton(text="Biz haqimizda", callback_data="about")],
            [InlineKeyboardButton(text="Bog'lanish Telegram", url=TELEGRAM_URL)],
            [InlineKeyboardButton(text="Instagram", url=INSTAGRAM_URL)],
            [InlineKeyboardButton(text="Manzil", callback_data="address")],
            [InlineKeyboardButton(text="Asosiy sayt", url=WEBSITE_URL)],
        ]
    )


dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=build_main_menu())


@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(ABOUT_TEXT)
    await callback.answer()


@dp.callback_query(F.data == "address")
async def address_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(ADDRESS_TEXT, reply_markup=build_main_menu())
    await callback.answer()


@dp.message()
async def fallback_handler(message: Message) -> None:
    await message.answer(
        f"{STORE_NAME} boti faqat yo'naltiruvchi ma'lumot beradi. Tugmalardan foydalaning.",
        reply_markup=build_main_menu(),
    )


async def main() -> None:
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
