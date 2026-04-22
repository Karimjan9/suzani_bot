# Suzani Shop Telegram Bot

Bu loyiha savdo qilmaydigan, foydalanuvchini kerakli rasmiy sahifalarga yo'naltiradigan Telegram bot.

## O'rnatilgan narsalar

- `aiogram`
- `mysql-connector-python`
- `python-dotenv`
- lokal virtual environment: `.venv`

## Ishga tushirish

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python bot.py
```

## Bot imkoniyatlari

- Biz haqimizda
- Bog'lanish Telegram
- Instagram
- Manzil
- Asosiy sayt
- ko'p tilli interfeys: o'zbek, rus, ingliz
- `WELCOME_IMAGE_URL` orqali welcome image qo'shish
- ish vaqti holatini ko'rsatish
- `LOCATION_LATITUDE` va `LOCATION_LONGITUDE` berilsa live location yuborish
- `/stats` orqali admin statistika ko'rishi

## Sozlanadigan env maydonlar

- `BOT_TOKEN`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `ADMIN_CHAT_ID`
- `WELCOME_IMAGE_URL`
- `LOCATION_LATITUDE`
- `LOCATION_LONGITUDE`

Bot endi MySQL ishlatadi. Agar local XAMPP ishlatsangiz, default qiymatlar odatda yetadi:

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_NAME=suzani_bot`
- `DB_USER=root`
- `DB_PASSWORD=`

Bot ishga tushganda baza va kerakli jadvallar avtomatik yaratiladi.

## Admin statistikasi

`/stats` buyrug'i faqat `.env` ichida `ADMIN_CHAT_ID` ko'rsatilgan foydalanuvchiga ishlaydi.
