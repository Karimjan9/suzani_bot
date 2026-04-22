# Server Deployment Guide

This bot uses `aiogram` long polling and MySQL.
That means:

- You do not need Nginx or a webhook to run it.
- The bot process must stay alive in the background.
- The server must be able to connect to Telegram and MySQL.

## 1. Prepare the server

Example below assumes Ubuntu.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git mysql-client
```

If MySQL will run on the same server:

```bash
sudo apt install -y mysql-server
```

## 2. Copy the project to the server

Example path:

```bash
sudo mkdir -p /opt/suzani_bot
sudo chown $USER:$USER /opt/suzani_bot
git clone <YOUR_GIT_REPO_URL> /opt/suzani_bot
cd /opt/suzani_bot
```

If the project is already on the server, just move into the folder.

## 3. Create virtualenv and install dependencies

```bash
cd /opt/suzani_bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Create the `.env` file

Copy from the sample:

```bash
cp .env.example .env
```

Then edit:

```bash
nano .env
```

Minimum required values:

```env
BOT_TOKEN=your_telegram_bot_token
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=suzani_bot
DB_USER=suzani_user
DB_PASSWORD=strong_password
ADMIN_CHAT_ID=your_telegram_numeric_id
WELCOME_IMAGE_URL=
LOCATION_LATITUDE=
LOCATION_LONGITUDE=
```

Notes:

- `BOT_TOKEN` is required, otherwise the bot will not start.
- `ADMIN_CHAT_ID` is needed only if you want `/stats` to work for your admin account.
- If MySQL is on another server, use that host instead of `127.0.0.1`.

## 5. Prepare MySQL

The app tries to create the database automatically on startup.
For that to work, the MySQL user must have permission to create databases.

If your MySQL user does not have that permission, create the database and user manually:

```sql
CREATE DATABASE suzani_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'suzani_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON suzani_bot.* TO 'suzani_user'@'localhost';
FLUSH PRIVILEGES;
```

If you use a remote MySQL server, replace `'localhost'` with the correct host rule.

## 6. Test the bot manually

Run it once before setting up the service:

```bash
cd /opt/suzani_bot
source .venv/bin/activate
python bot.py
```

If the bot starts without errors, stop it with `Ctrl+C`.

## 7. Run it as a systemd service

There is a sample service file in [deploy/suzani-bot.service.example](/c:/x_programs/xamp/htdocs/laravel_projects/suzani_bot/deploy/suzani-bot.service.example).

Copy it into systemd and adjust the paths/user first:

```bash
sudo cp deploy/suzani-bot.service.example /etc/systemd/system/suzani-bot.service
sudo nano /etc/systemd/system/suzani-bot.service
```

Then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable suzani-bot
sudo systemctl start suzani-bot
sudo systemctl status suzani-bot
```

Useful logs:

```bash
journalctl -u suzani-bot -f
```

## 8. Deploy updates later

When you change the code:

```bash
cd /opt/suzani_bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart suzani-bot
```

## Common deployment checks

- `BOT_TOKEN` is correct.
- `.env` exists in the project root.
- MySQL is reachable from the server.
- The MySQL user/password in `.env` are correct.
- The service `WorkingDirectory` points to the project root.
- The service `ExecStart` points to the virtualenv Python path.
- Outbound internet access is open so the bot can reach Telegram.
