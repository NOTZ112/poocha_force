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

    except Exception as e:

        print(
            "Member Check Error:",
            chat_id,
            user_id,
            e
        )

        return False


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

    # =========================
    # ALREADY ACTIVE
    # =========================

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
            "Old ban removed:",
            user.id
        )

    except Exception as e:

        print(
            "Unban Error:",
            e
        )

    # =========================
    # CREATE NEW INVITE
    # =========================

    try:

        invite = await context.bot.create_chat_invite_link(
            chat_id=SECRET_CHANNEL_ID,
            member_limit=1
        )

        await save_invite(
            user.id,
            invite.invite_link
        )

    except Exception as e:

        print(
            "Invite Error:",
            e
        )

        await query.message.reply_text(
            "❌ Invite link create ചെയ്യാൻ കഴിഞ്ഞില്ല."
        )

        return

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
# SECRET CHANNEL MEMBER CHECK
# =========================

async def secret_channel_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    member = update.chat_member

    if not member:
        return

    if member.chat.id != SECRET_CHANNEL_ID:
        return

    user = member.new_chat_member.user
    status = member.new_chat_member.status

    print(
        "SECRET CHANNEL UPDATE:",
        user.id,
        status
    )

    # =========================
    # USER JOINED
    # =========================

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
# MAIN GROUP LEAVE CHECK
# =========================

async def main_group_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    member = update.chat_member

    if not member:
        return

    chat_id = member.chat.id

    # Only monitor the two main groups
    if chat_id not in (
        MAIN_GROUP_1_ID,
        MAIN_GROUP_2_ID,
    ):
        return

    user = member.new_chat_member.user
    status = member.new_chat_member.status

    print(
        "MAIN GROUP UPDATE:",
        chat_id,
        user.id,
        status
    )

    # =========================
    # ONLY WHEN LEFT / KICKED
    # =========================

    if status not in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
    ):
        return

    print(
        "MAIN GROUP LEFT:",
        user.id
    )

    # =========================
    # CHECK OTHER MAIN GROUP
    # =========================

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

    # Still member in both groups
    if main1 and main2:
        return

    # =========================
    # GET USER DATA
    # =========================

    data = await get_user(
        user.id
    )

    if not data:
        return

    if not data.get("secret"):
        return

    # =========================
    # REVOKE INVITE
    # =========================

    invite_link = data.get(
        "invite_link"
    )

    if invite_link:

        try:

            await context.bot.revoke_chat_invite_link(
                chat_id=SECRET_CHANNEL_ID,
                invite_link=invite_link
            )

            print(
                "Invite Revoked:",
                user.id
            )

        except Exception as e:

            print(
                "Revoke Error:",
                user.id,
                e
            )

    # =========================
    # REMOVE FROM SECRET
    # =========================

    try:

        await context.bot.ban_chat_member(
            chat_id=SECRET_CHANNEL_ID,
            user_id=user.id
        )

        print(
            "Secret Channel Ban:",
            user.id
        )

        # Immediately unban.
        # This removes the user from the channel
        # while allowing them to join again later
        # if they regain access.

        await context.bot.unban_chat_member(
            chat_id=SECRET_CHANNEL_ID,
            user_id=user.id,
            only_if_banned=True
        )

        print(
            "Secret Channel Removed:",
            user.id
        )

    except Exception as e:

        print(
            "Secret Remove Error:",
            user.id,
            e
        )

    # =========================
    # CLEAR ACCESS
    # =========================

    await update_secret(
        user.id,
        False
    )

    await clear_invite(
        user.id
    )

    # =========================
    # NOTIFY USER
    # =========================

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=REMOVED_TEXT
        )

    except Exception as e:

        print(
            "Notification Error:",
            user.id,
            e
        )


# =========================
# BACKGROUND AUTO CHECKER
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

                # =========================
                # CHECK MAIN GROUP 1
                # =========================

                main1 = await is_member(
                    application.bot,
                    MAIN_GROUP_1_ID,
                    uid
                )

                # =========================
                # CHECK MAIN GROUP 2
                # =========================

                main2 = await is_member(
                    application.bot,
                    MAIN_GROUP_2_ID,
                    uid
                )

                # Still joined both
                if main1 and main2:
                    continue

                print(
                    "AUTO REMOVE DETECTED:",
                    uid
                )

                # =========================
                # REVOKE INVITE
                # =========================

                invite_link = user.get(
                    "invite_link"
                )

                if invite_link:

                    try:

                        await application.bot.revoke_chat_invite_link(
                            chat_id=SECRET_CHANNEL_ID,
                            invite_link=invite_link
                        )

                        print(
                            "Invite Revoked:",
                            uid
                        )

                    except Exception as e:

                        print(
                            "Revoke Error:",
                            uid,
                            e
                        )

                # =========================
                # REMOVE FROM SECRET
                # =========================

                try:

                    await application.bot.ban_chat_member(
                        chat_id=SECRET_CHANNEL_ID,
                        user_id=uid
                    )

                    print(
                        "Banned from Secret:",
                        uid
                    )

                    await application.bot.unban_chat_member(
                        chat_id=SECRET_CHANNEL_ID,
                        user_id=uid,
                        only_if_banned=True
                    )

                    print(
                        "Removed from Secret:",
                        uid
                    )

                except Exception as e:

                    print(
                        "Remove Error:",
                        uid,
                        e
                    )

                # =========================
                # CLEAR ACCESS
                # =========================

                await update_secret(
                    uid,
                    False
                )

                await clear_invite(
                    uid
                )

                # =========================
                # NOTIFY USER
                # =========================

                try:

                    await application.bot.send_message(
                        chat_id=uid,
                        text=REMOVED_TEXT
                    )

                except Exception as e:

                    print(
                        "Notify Error:",
                        uid,
                        e
                    )

        except Exception as e:

            print(
                "Checker Error:",
                e
            )

        await asyncio.sleep(30)


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
# START HANDLER
# =========================

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


# =========================
# CHECK ACCESS HANDLER
# =========================

app.add_handler(
    CallbackQueryHandler(
        check_access,
        pattern="^check_access$"
    )
)


# =========================
# SECRET CHANNEL HANDLER
# =========================

app.add_handler(
    ChatMemberHandler(
        secret_channel_check,
        ChatMemberHandler.CHAT_MEMBER
    )
)


# =========================
# MAIN GROUP HANDLER
# =========================

app.add_handler(
    ChatMemberHandler(
        main_group_check,
        ChatMemberHandler.CHAT_MEMBER
    )
)


# =========================
# START BOT
# =========================

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
