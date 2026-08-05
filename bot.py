from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import asyncio

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

        except Exception:
            pass

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
# =========================
# SECRET CHANNEL CHECK
# =========================

async def secret_channel_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    member = update.chat_member

    if member.chat.id != SECRET_CHANNEL_ID:
        return

    user = member.from_user

    new_status = member.new_chat_member.status

    print(
        "SECRET STATUS:",
        new_status
    )

    # USER JOINED
    if new_status in (
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

    # USER LEFT / REMOVED
    if new_status in (
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
# MAIN GROUP LEAVE CHECK
# =========================

async def main_group_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print("MAIN UPDATE RECEIVED")

    member = update.chat_member

    print(
        "CHAT:",
        member.chat.id
    )

    print(
        "OLD:",
        member.old_chat_member.status
    )

    print(
        "NEW:",
        member.new_chat_member.status
    )

    if member.chat.id not in (
        MAIN_GROUP_1_ID,
        MAIN_GROUP_2_ID
    ):
        return

    user = member.from_user

    old_status = member.old_chat_member.status
    new_status = member.new_chat_member.status

    # User left / was removed / banned from a Main Group
    if (
        old_status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
        and
        new_status in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED,
        )
    ):

        await update_secret(
            user.id,
            False
        )

        data = await get_user(
            user.id
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

        try:

            await context.bot.ban_chat_member(
                chat_id=SECRET_CHANNEL_ID,
                user_id=user.id
            )

            print(
                "Removed from Secret Channel:",
                user.id
            )

        except Exception as e:

            print(
                "Remove error:",
                e
            )

        try:

            await context.bot.send_message(
                chat_id=user.id,
                text=REMOVED_TEXT
            )

        except Exception:
            pass 
# =========================
# BACKGROUND MEMBERSHIP CHECK
# =========================

async def membership_checker(app):

    while True:

        users = db.users.find(
            {
                "secret": True
            }
        )

        async for user in users:

            user_id = user["_id"]

            main1 = await is_member(
                app.bot,
                MAIN_GROUP_1_ID,
                user_id
            )

            main2 = await is_member(
                app.bot,
                MAIN_GROUP_2_ID,
                user_id
            )

            if not main1 or not main2:

                try:

                    await app.bot.ban_chat_member(
                        chat_id=SECRET_CHANNEL_ID,
                        user_id=user_id
                    )

                    await app.bot.unban_chat_member(
                        chat_id=SECRET_CHANNEL_ID,
                        user_id=user_id
                    )

                except Exception as e:

                    print(e)

                await update_secret(
                    user_id,
                    False
                )

                await clear_invite(
                    user_id
                )

        await asyncio.sleep(30)            
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

app.add_handler(
    ChatMemberHandler(
        main_group_check,
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
        "chat_member"
    ]
)
