import logging

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

from database import (
    add_user,
    get_user,
    update_secret,
    save_invite,
    clear_invite,
    all_users,
)

logging.basicConfig(
    level=logging.INFO
)

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)


# =========================
# CHECK MEMBER
# =========================

async def is_member(
    bot,
    chat_id,
    user_id
):

    try:

        member = await bot.get_chat_member(
            chat_id,
            user_id
        )

        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )

    except:

        return False


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Check Access",
                    callback_data="check_access"
                )
            ]
        ]
    )

    await update.message.reply_text(
        START_TEXT,
        reply_markup=keyboard
    )
# =========================
# CHECK ACCESS
# =========================

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
                        "📢 Main Group 1",
                        url=MAIN_GROUP_1_LINK
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📢 Main Group 2",
                        url=MAIN_GROUP_2_LINK
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

    if data and data.get("secret"):

        still_member = await is_member(
            context.bot,
            SECRET_CHANNEL_ID,
            user.id
        )

        if still_member:

            await query.message.reply_text(
                ALREADY_SECRET_TEXT
            )

            return

        await update_secret(
            user.id,
            False
        )

    invite = await context.bot.create_chat_invite_link(
        chat_id=SECRET_CHANNEL_ID,
        member_limit=1,
        creates_join_request=False
    )

    await save_invite(
        user.id,
        invite.invite_link
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔐 Secret Channel",
                    url=invite.invite_link
                )
            ]
        ]
    )

    await query.message.reply_text(
        SUCCESS_TEXT,
        reply_markup=keyboard
    )   
import asyncio

# =========================
# SECRET CHANNEL JOIN
# =========================

async def secret_channel_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    member = update.chat_member

    if member.chat.id != SECRET_CHANNEL_ID:
        return

    status = member.new_chat_member.status

    user = member.new_chat_member.user

    if status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):

        await update_secret(
            user.id,
            True
        )

        print(
            "Secret Joined:",
            user.id
        )


# =========================
# AUTO REMOVE CHECKER
# =========================

async def auto_remove_checker(
    app: Application
):

    while True:

        try:

            users = await all_users()

            for user in users:

                if not user.get("secret"):
                    continue

                uid = user["_id"]

                main1 = await is_member(
                    app.bot,
                    MAIN_GROUP_1_ID,
                    uid
                )

                main2 = await is_member(
                    app.bot,
                    MAIN_GROUP_2_ID,
                    uid
                )

                if main1 and main2:
                    continue

                try:

                    await app.bot.ban_chat_member(
                        SECRET_CHANNEL_ID,
                        uid
                    )

                    await app.bot.unban_chat_member(
                        SECRET_CHANNEL_ID,
                        uid,
                        only_if_banned=True
                    )

                except Exception as e:

                    print(e)

                await update_secret(
                    uid,
                    False
                )

                await clear_invite(
                    uid
                )

                try:

                    await app.bot.send_message(
                        uid,
                        REMOVED_TEXT
                    )

                except:
                    pass

        except Exception as e:

            print(e)

        await asyncio.sleep(30)
# =========================
# START BACKGROUND TASK
# =========================

async def post_init(
    application: Application
):

    application.create_task(
        auto_remove_checker(application)
    )


# =========================
# APPLICATION
# =========================

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(post_init)
    .build()
)


# =========================
# HANDLERS
# =========================

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CallbackQueryHandler(
        check_access,
        pattern="^check_access$"
    )
)

app.add_handler(
    ChatMemberHandler(
        secret_channel_check,
        ChatMemberHandler.CHAT_MEMBER
    )
)


print("Bot Started")


app.run_polling(
    allowed_updates=[
        "message",
        "callback_query",
        "chat_member",
    ],
    drop_pending_updates=True
)  
