import asyncio
import nest_asyncio
import emoji
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Bot

# 👇 Flask и Thread — добавлены для пинга
from flask import Flask
from threading import Thread

nest_asyncio.apply()

OWNER_ID = 7774584060

WELCOME_MESSAGE = (
    "👋 Привет!\n\n"
    "Я — бот для пользователей SpamBlock.\n"
    "Отправь мне любое сообщение, и я быстро передам его моему владельцу.\n\n"
    "⚠️ Важно: он сможет ответить тебе напрямую здесь.\n\n"
    "✉️ Просто напиши что-нибудь и отправь!"
)

forwarded_messages = {}

def is_emoji_only(text: str) -> bool:
    text = text.strip()
    return all(char in emoji.EMOJI_DATA or char.isspace() for char in text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = update.effective_user

    if not msg:
        return

    if user.id == OWNER_ID and msg.reply_to_message:
        replied_msg_id = msg.reply_to_message.message_id

        if replied_msg_id in forwarded_messages:
            recipient_id = forwarded_messages[replied_msg_id]
            response_text = msg.text.strip() if msg.text else ""

            reply_text = (
                f"📨 *Ответ от владельца:*\n\n"
                f"{response_text}"
            )
            try:
                await context.bot.send_message(
                    chat_id=recipient_id,
                    text=reply_text,
                    parse_mode="Markdown"
                )
                await msg.reply_text("✅ Ответ успешно отправлен пользователю!")
            except Exception as e:
                await msg.reply_text(f"❌ Не удалось отправить сообщение пользователю:\n{e}")
        else:
            await msg.reply_text("⚠️ Ошибка: ответьте именно на пересланное сообщение пользователя.")
        return

    if user.id != OWNER_ID:
        try:
            forwarded_message = await msg.forward(chat_id=OWNER_ID)
            forwarded_messages[forwarded_message.message_id] = user.id

            if msg.text:
                if is_emoji_only(msg.text):
                    msg_type = "📦 Эмодзи"
                else:
                    msg_type = "📝 Текстовое сообщение"
            elif msg.animation:
                msg_type = "🎞️ GIF / Premium Emoji"
            elif msg.sticker:
                msg_type = "🖼️ Стикер"
            elif msg.voice:
                msg_type = "🎤 Голосовое сообщение"
            elif msg.video_note:
                msg_type = "🎥 Видеосообщение"
            elif msg.video:
                msg_type = "🎬 Видео"
            elif msg.photo:
                msg_type = "📷 Фото"
            else:
                msg_type = "📦 Неизвестный тип сообщения"

            sender_info = (
                f"*Новое сообщение от пользователя*\n"
                f"────────────────────────\n"
                f"*Тип сообщения:* {msg_type}\n\n"
                f"👤 *Информация об отправителе:*\n"
                f"• ID: `{user.id}`\n"
                f"• Username: @{user.username if user.username else 'нет username'}\n"
                f"────────────────────────"
            )

            await context.bot.send_message(chat_id=OWNER_ID, text=sender_info, parse_mode="Markdown")
            await msg.reply_text("✅ Сообщение отправлено владельцу!")

        except Exception as e:
            await msg.reply_text(f"❌ Ошибка при отправке владельцу:\n{e}")

# 👇 Flask-сервер для пинга (добавлено)
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = Thread(target=run)
    thread.start()

async def send_uptime_mention(bot: Bot, chat_id: int):
    me = await bot.get_me()
    user_id = me.id
    bot_username = me.username

    text = f'UptimeRobot: проверка бота [@{bot_username}](tg://user?id={user_id})'
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        print("✅ UptimeRobot mention sent")
    except Exception as e:
        print(f"❌ Ошибка при отправке упоминания UptimeRobot:\n{e}")

async def main():
    TOKEN = "7196108749:AAF5nzJLyohQKWq5LHJe3eKSL_diTCL20mI"
    CHAT_ID_UPTIME = OWNER_ID  # Можно заменить на другой чат ID для упоминания

    keep_alive()  # ⬅️ Запуск Flask перед Telegram-ботом

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))

    # Отправляем упоминание UptimeRobot при старте бота
    await send_uptime_mention(app.bot, CHAT_ID_UPTIME)

    print("✅ Бот запущен. Ожидание сообщений...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
