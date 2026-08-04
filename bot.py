from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ChatMemberStatus

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    ContextTypes,
)

from config import *

from database import *


app = (
    Application
    .builder()
    .token(BOT_TOKEN)
    .build()
)
async def is_member(
    bot,
    chat_id: int,
    user_id: int
):  
    try:
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    await add_user(user.id)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="✅ Check Access",
                    callback_data="check_access"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Owner",
                    url=f"https://t.me/{OWNER_USERNAME}"
                )
            ]
        ]
    )
async def check_access(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    user = query.from_user

    await add_user(user.id)

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        user.id
    )

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        user.id
    )

    if not main1 or not main2:

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📢 Join Main Group 1",
                        url=MAIN_GROUP_1_LINK
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📢 Join Main Group 2",
                        url=MAIN_GROUP_2_LINK
                    )
                ],
                [
                    InlineKeyboardButton(
                        "👤 Owner",
                        url=f"https://t.me/{OWNER_USERNAME}"
                    )
                ]
            ]
        )

        await query.message.reply_text(
            FAILED_TEXT,
            reply_markup=keyboard
        )

        return

    data = await get_user(user.id)

    if data.get("secret"):

        await query.message.reply_text(
            "✅ You are already in the Secret Group."
        )

        return

    if data.get("invite_link") and not data.get("invite_used"):

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔐 Join Secret Group",
                        url=data["invite_link"]
                    )
                ]
            ]
        )

        await query.message.reply_text(
            "♻️ Your previous invite link is still active.",
            reply_markup=keyboard
        )

        return

    invite = await context.bot.create_chat_invite_link(
        chat_id=SECRET_GROUP_ID,
        member_limit=1
    )

    await save_invite(
        user.id,
        invite.invite_link
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔐 Join Secret Group",
                    url=invite.invite_link
                )
            ]
        ]
    )

    await query.message.reply_text(
        SUCCESS_TEXT,
        reply_markup=keyboard
        )
    await update.message.reply_text(
        START_TEXT,
        reply_markup=keyboard
    )
        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )

        return member.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        )

    except Exception:

        return False
async def monitor_groups(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.chat_member is None:
        return

    chat = update.chat_member.chat

    if chat.id not in (
        MAIN_GROUP_1_ID,
        MAIN_GROUP_2_ID
    ):
        return

    user = update.chat_member.new_chat_member.user

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        user.id
    )

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        user.id
    )

    if main1 and main2:
        return

    try:
        await context.bot.ban_chat_member(
            chat_id=SECRET_GROUP_ID,
            user_id=user.id
        )

        await update_secret(user.id, False)
        await clear_invite(user.id)
        await set_banned(user.id, True)

    except Exception as e:
        print(f"Ban Error: {e}")

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👤 Owner",
                    url=f"https://t.me/{OWNER_USERNAME}"
                )
            ]
        ]
    )

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=REMOVED_TEXT,
            reply_markup=keyboard
        )
    except Exception:
        pass
