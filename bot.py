import logging
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

    except Exception:

        return False


# =========================
# ADMIN CHECK
# =========================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # User database-ൽ save ചെയ്യും

    await add_user(
        update.effective_user.id
    )

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
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Check Again",
                        callback_data="check_access"
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

    # Already active access

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

    # =========================
    # REMOVE OLD BAN
    # =========================

    try:

        await context.bot.unban_chat_member(
            SECRET_CHANNEL_ID,
            user.id,
            only_if_banned=True
        )

        print(
            "Unbanned:",
            user.id
        )

    except Exception as e:

        print(
            "Unban Error:",
            e
        )

    # CREATE NEW SECRET INVITE

    invite = await context.bot.create_chat_invite_link(
        chat_id=SECRET_CHANNEL_ID,
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
                    "🔐 Join Secret Channel",
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
# SECRET CHANNEL JOIN CHECK
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
    application: Application
):

    while True:

        try:

            users = await all_users()

            for user in users:

                if not user.get("secret"):
                    continue

                uid = user["_id"]

                main1 = await is_member(
                    application.bot,
                    MAIN_GROUP_1_ID,
                    uid
                )

                main2 = await is_member(
                    application.bot,
                    MAIN_GROUP_2_ID,
                    uid
                )

                if main1 and main2:
                    continue

                # REVOKE INVITE

                if user.get("invite_link"):

                    try:

                        await application.bot.revoke_chat_invite_link(
                            SECRET_CHANNEL_ID,
                            user["invite_link"]
                        )

                        print(
                            "Invite Revoked:",
                            uid
                        )

                    except Exception as e:

                        print(
                            "Revoke Error:",
                            e
                        )

                # REMOVE FROM SECRET CHANNEL

                try:

                    await application.bot.ban_chat_member(
                        SECRET_CHANNEL_ID,
                        uid
                    )

                    await application.bot.unban_chat_member(
                        SECRET_CHANNEL_ID,
                        uid,
                        only_if_banned=True
                    )

                    print(
                        "Removed Secret:",
                        uid
                    )

                except Exception as e:

                    print(
                        "Remove Error:",
                        e
                    )

                await update_secret(
                    uid,
                    False
                )

                await clear_invite(
                    uid
                )

                try:

                    await application.bot.send_message(
                        uid,
                        REMOVED_TEXT
                    )

                except:

                    pass

        except Exception as e:

            print(
                "Checker Error:",
                e
            )

        await asyncio.sleep(30)


# =========================
# ADMIN - USERS COUNT
# =========================

async def users_count(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    users = await all_users()

    await update.message.reply_text(
        f"👥 TOTAL USERS\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 Users: {len(users)}\n"
        f"━━━━━━━━━━━━━━"
    )


# =========================
# ADMIN - BROADCAST
# =========================

async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    # Broadcast ചെയ്യേണ്ട message-ന് reply ചെയ്യണം

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "📢 Broadcast ചെയ്യേണ്ട message-ന് "
            "Reply ചെയ്ത് /broadcast അയക്കുക.\n\n"
            "🔘 Button വേണമെങ്കിൽ:\n"
            "/broadcast Button Name | https://example.com"
        )

        return

    source = update.message.reply_to_message

    # =========================
    # ONE URL BUTTON
    # =========================

    keyboard = None

    if context.args:

        raw = " ".join(
            context.args
        )

        if "|" in raw:

            button_text, button_url = raw.split(
                "|",
                1
            )

            button_text = button_text.strip()

            button_url = button_url.strip()

            if button_text and button_url:

                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                button_text,
                                url=button_url
                            )
                        ]
                    ]
                )

    # =========================
    # GET USERS
    # =========================

    users = await all_users()

    total = len(users)

    success = 0

    failed = 0

    status_message = await update.message.reply_text(
        f"📢 BROADCAST STARTED\n\n"
        f"👥 Total Users: {total}\n"
        f"⏳ Sending..."
    )

    # =========================
    # SEND
    # =========================

    for user in users:

        user_id = user.get("_id")

        if not user_id:
            continue

        try:

            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=source.chat.id,
                message_id=source.message_id,
                reply_markup=keyboard
            )

            success += 1

            await asyncio.sleep(0.05)

        except Exception as e:

            failed += 1

            print(
                "Broadcast Error:",
                user_id,
                e
            )

    # =========================
    # RESULT
    # =========================

    try:

        await status_message.edit_text(
            f"✅ BROADCAST COMPLETED\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"👥 Total Users: {total}\n"
            f"✅ Sent: {success}\n"
            f"❌ Failed: {failed}\n"
            f"━━━━━━━━━━━━━━"
        )

    except:

        await update.message.reply_text(
            f"✅ BROADCAST COMPLETED\n\n"
            f"👥 Total Users: {total}\n"
            f"✅ Sent: {success}\n"
            f"❌ Failed: {failed}"
        )


# =========================
# BACKGROUND TASK
# =========================

async def post_init(
    application: Application
):

    application.create_task(
        auto_remove_checker(
            application
        )
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


# =========================
# ADMIN HANDLERS
# =========================

app.add_handler(
    CommandHandler(
        "users",
        users_count
    )
)

app.add_handler(
    CommandHandler(
        "broadcast",
        broadcast
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
