import asyncio

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
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)


# =========================
# CHECK MEMBER
# =========================

async def is_member(
    bot,
    chat_id: int,
    user_id: int
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

    except Exception:

        return False
   # =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    await add_user(
        user.id
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔎 അംഗത്വം പരിശോധിക്കുക",
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

    await add_user(
        user.id
    )

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

    data = await get_user(
        user.id
    )
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


    if data and data.get("invite_link"):

        try:

            await context.bot.revoke_chat_invite_link(
                chat_id=SECRET_CHANNEL_ID,
                invite_link=data["invite_link"]
            )

        except Exception as e:

            print(
                "Invite revoke error:",
                e
            )

    await clear_invite(
        user.id
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
                    "🔐 Secret Channel Join",
                    url=invite.invite_link
                )
            ]
        ]
    )

    await query.message.reply_text(
        SUCCESS_TEXT,
        reply_markup=keyboard
        )
  # =========================
# SECRET CHANNEL EVENTS
# =========================

async def secret_channel_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    member = update.chat_member

    if member.chat.id != SECRET_CHANNEL_ID:
        return

    user = member.from_user

    status = member.new_chat_member.status

    print(
        "SECRET STATUS:",
        status
    )

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
            "Secret Channel Joined:",
            user.id
        )

        return

    if status in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
    ):

        await update_secret(
            user.id,
            False
        )

        await clear_invite(
            user.id
        )

        print(
            "Secret Channel Left:",
            user.id
        )


# =========================
# BACKGROUND MEMBERSHIP CHECK
# =========================

async def membership_checker(application):

    while True:

        cursor = users.find(
            {
                "secret": True
            }
        )

        async for data in cursor:

            user_id = data["_id"]

            main1 = await is_member(
                application.bot,
                MAIN_GROUP_1_ID,
                user_id
            )

            main2 = await is_member(
                application.bot,
                MAIN_GROUP_2_ID,
                user_id
            )

            if not main1 or not main2:

                print(
                    "Removing:",
                    user_id
                )

                try:

                    await application.bot.ban_chat_member(
                        chat_id=SECRET_CHANNEL_ID,
                        user_id=user_id
                    )

                except Exception as e:

                    print(
                        "Ban Error:",
                        e
                    )

                await update_secret(
                    user_id,
                    False
                )

                await clear_invite(
                    user_id
                )

        await asyncio.sleep(30)  
# =========================
# START BACKGROUND TASK
# =========================

job_queue = app.job_queue

job_queue.run_repeating(
    lambda context: asyncio.create_task(
        membership_checker(app)
    ),
    interval=30,
    first=5,
)


# =========================
# HANDLERS
# =========================

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

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

print(
    "Bot Started"
)

app.run_polling(
    allowed_updates=[
        "message",
        "callback_query",
        "chat_member",
    ],
    drop_pending_updates=True
)
