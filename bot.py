from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from telegram.constants import ChatMemberStatus

from config import *
from database import *


async def is_member(bot, chat_id, user_id):
    """
    Returns True if user is currently a member/admin/owner
    """
    try:
        member = await bot.get_chat_member(chat_id, user_id)

        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )

    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    await add_user(user.id)

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Check Access",
                callback_data="check"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Owner",
                url=f"https://t.me/{OWNER_USERNAME}"
            )
        ]
    ]

    await update.message.reply_text(
        START_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


app = (
    Application
    .builder()
    .token(BOT_TOKEN)
    .build()
)

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.run_polling()
