import logging
import asyncio
import re

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


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# ACTIVE STATUSES
# =========================================================

ACTIVE_STATUSES = (
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
)


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# =========================================================
# MEMBER CHECK
# =========================================================

async def is_member(
    bot,
    chat_id,
    user_id,
):

    try:

        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )

        status = member.status

        logger.info(
            "MEMBER CHECK | chat=%s user=%s status=%s",
            chat_id,
            user_id,
            status,
        )

        if status in ACTIVE_STATUSES:
            return True

        if status in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED,
        ):
            return False

        return False

    except Exception as e:

        logger.error(
            "MEMBER CHECK ERROR | chat=%s user=%s error=%s",
            chat_id,
            user_id,
            e,
        )

        # API error is NOT equal to user left
        return None


# =========================================================
# REMOVE FROM SECRET GROUP
# =========================================================

async def remove_from_secret(
    application: Application,
    user_id: int,
    invite_link=None,
):

    logger.warning(
        "REMOVE FROM SECRET START | user=%s",
        user_id,
    )

    bot = application.bot

    # =====================================================
    # REVOKE INVITE
    # =====================================================

    if invite_link:

        try:

            await bot.revoke_chat_invite_link(
                chat_id=SECRET_GROUP_ID,
                invite_link=invite_link,
            )

            logger.info(
                "INVITE REVOKED | user=%s",
                user_id,
            )

        except Exception as e:

            logger.warning(
                "INVITE REVOKE FAILED | user=%s | %s",
                user_id,
                e,
            )

    # =====================================================
    # CHECK SECRET GROUP
    # =====================================================

    try:

        member = await bot.get_chat_member(
            chat_id=SECRET_GROUP_ID,
            user_id=user_id,
        )

        secret_status = member.status

        logger.info(
            "SECRET MEMBER STATUS | user=%s | status=%s",
            user_id,
            secret_status,
        )

    except Exception as e:

        logger.error(
            "SECRET MEMBER CHECK ERROR | user=%s | %s",
            user_id,
            e,
        )

        return

    # =====================================================
    # REMOVE USER
    # =====================================================

    if secret_status in ACTIVE_STATUSES:

        try:

            await bot.ban_chat_member(
                chat_id=SECRET_GROUP_ID,
                user_id=user_id,
            )

            logger.warning(
                "SECRET GROUP BAN SUCCESS | user=%s",
                user_id,
            )

        except Exception as e:

            logger.error(
                "SECRET GROUP BAN ERROR | user=%s | %s",
                user_id,
                e,
            )

            return

        # =================================================
        # UNBAN IMMEDIATELY
        # =================================================

        try:

            await bot.unban_chat_member(
                chat_id=SECRET_GROUP_ID,
                user_id=user_id,
                only_if_banned=True,
            )

            logger.info(
                "SECRET GROUP UNBAN SUCCESS | user=%s",
                user_id,
            )

        except Exception as e:

            logger.error(
                "SECRET GROUP UNBAN ERROR | user=%s | %s",
                user_id,
                e,
            )

    else:

        logger.info(
            "USER NOT ACTIVE IN SECRET GROUP | user=%s",
            user_id,
        )

    # =====================================================
    # CLEAR DATABASE
    # =====================================================

    try:

        await update_secret(
            user_id,
            False,
        )

        await clear_invite(
            user_id,
        )

        logger.info(
            "ACCESS CLEARED | user=%s",
            user_id,
        )

    except Exception as e:

        logger.error(
            "DATABASE CLEAR ERROR | user=%s | %s",
            user_id,
            e,
        )

    # =====================================================
    # NOTIFY
    # =====================================================

    try:

        await bot.send_message(
            chat_id=user_id,
            text=REMOVED_TEXT,
        )

    except Exception as e:

        logger.warning(
            "NOTIFICATION ERROR | user=%s | %s",
            user_id,
            e,
        )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    await add_user(
        user_id,
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Check Access",
                    callback_data="check_access",
                )
            ]
        ]
    )

    if update.message:

        await update.message.reply_text(
            START_TEXT,
            reply_markup=keyboard,
        )


# =========================================================
# CHECK ACCESS
# =========================================================

async def check_access(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = query.from_user.id

    await add_user(
        user_id,
    )

    # =====================================================
    # MAIN GROUP 1
    # =====================================================

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        user_id,
    )

    if main1 is None:

        await query.message.reply_text(
            "⚠️ ഇപ്പോൾ membership പരിശോധിക്കാൻ കഴിഞ്ഞില്ല.\n"
            "കുറച്ച് കഴിഞ്ഞ് വീണ്ടും ശ്രമിക്കുക."
        )

        return

    # =====================================================
    # MAIN GROUP 2
    # =====================================================

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        user_id,
    )

    if main2 is None:

        await query.message.reply_text(
            "⚠️ ഇപ്പോൾ membership പരിശോധിക്കാൻ കഴിഞ്ഞില്ല.\n"
            "കുറച്ച് കഴിഞ്ഞ് വീണ്ടും ശ്രമിക്കുക."
        )

        return

    # =====================================================
    # NOT JOINED
    # =====================================================

    if not main1 or not main2:

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📢 Main Group 1",
                        url=MAIN_GROUP_1_LINK,
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📢 Main Group 2",
                        url=MAIN_GROUP_2_LINK,
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Check Again",
                        callback_data="check_access",
                    )
                ],
            ]
        )

        await query.message.reply_text(
            FAILED_TEXT,
            reply_markup=keyboard,
        )

        return

    # =====================================================
    # DATABASE
    # =====================================================

    data = await get_user(
        user_id,
    )

    # =====================================================
    # ALREADY ACTIVE
    # =====================================================

    if data and data.get("secret"):

        still_member = await is_member(
            context.bot,
            SECRET_GROUP_ID,
            user_id,
        )

        if still_member is None:

            await query.message.reply_text(
                "⚠️ Secret Group membership പരിശോധിക്കാൻ കഴിഞ്ഞില്ല."
            )

            return

        if still_member:

            await query.message.reply_text(
                ALREADY_SECRET_TEXT,
            )

            return

        await update_secret(
            user_id,
            False,
        )

    # =====================================================
    # REMOVE OLD BAN
    # =====================================================

    try:

        await context.bot.unban_chat_member(
            chat_id=SECRET_GROUP_ID,
            user_id=user_id,
            only_if_banned=True,
        )

    except Exception as e:

        logger.info(
            "OLD BAN CHECK | user=%s | %s",
            user_id,
            e,
        )

    # =====================================================
    # CREATE INVITE
    # =====================================================

    try:

        invite = await context.bot.create_chat_invite_link(
            chat_id=SECRET_GROUP_ID,
            member_limit=1,
        )

        await save_invite(
            user_id,
            invite.invite_link,
        )

    except Exception as e:

        logger.error(
            "INVITE CREATE ERROR | user=%s | %s",
            user_id,
            e,
        )

        await query.message.reply_text(
            "❌ Invite link create ചെയ്യാൻ കഴിഞ്ഞില്ല.",
        )

        return

    # =====================================================
    # SEND INVITE
    # =====================================================

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔐 Join Secret Group",
                    url=invite.invite_link,
                )
            ]
        ]
    )

    await query.message.reply_text(
        SUCCESS_TEXT,
        reply_markup=keyboard,
    )


# =========================================================
# SECRET GROUP UPDATE
# =========================================================

async def secret_group_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    member_update = update.chat_member

    if not member_update:
        return

    if member_update.chat.id != SECRET_GROUP_ID:
        return

    user = member_update.new_chat_member.user

    status = member_update.new_chat_member.status

    logger.info(
        "SECRET GROUP UPDATE | user=%s | status=%s",
        user.id,
        status,
    )

    if status in ACTIVE_STATUSES:

        await update_secret(
            user.id,
            True,
        )

        logger.info(
            "SECRET ACCESS ACTIVE | user=%s",
            user.id,
        )


# =========================================================
# MAIN GROUP UPDATE
# =========================================================

async def main_group_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    member_update = update.chat_member

    if not member_update:
        return

    chat_id = member_update.chat.id

    if chat_id not in (
        MAIN_GROUP_1_ID,
        MAIN_GROUP_2_ID,
    ):
        return

    user = member_update.new_chat_member.user

    status = member_update.new_chat_member.status

    logger.info(
        "MAIN GROUP UPDATE | chat=%s | user=%s | status=%s",
        chat_id,
        user.id,
        status,
    )

    if status not in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
    ):
        return

    user_id = user.id

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        user_id,
    )

    if main1 is None:

        logger.warning(
            "LEAVE CHECK SKIPPED | MAIN1 API ERROR | user=%s",
            user_id,
        )

        return

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        user_id,
    )

    if main2 is None:

        logger.warning(
            "LEAVE CHECK SKIPPED | MAIN2 API ERROR | user=%s",
            user_id,
        )

        return

    if main1 and main2:
        return

    data = await get_user(
        user_id,
    )

    if not data:
        return

    if not data.get("secret"):
        return

    await remove_from_secret(
        context.application,
        user_id,
        data.get("invite_link"),
    )


# =========================================================
# AUTO CHECKER
# =========================================================

async def auto_remove_checker(
    application: Application,
):

    logger.info(
        "AUTO CHECKER STARTED"
    )

    while True:

        try:

            users = await all_users()

            checked = 0

            for user in users:

                if not user.get("secret"):
                    continue

                user_id = user.get("_id")

                if not user_id:
                    continue

                checked += 1

                main1 = await is_member(
                    application.bot,
                    MAIN_GROUP_1_ID,
                    user_id,
                )

                if main1 is None:

                    logger.warning(
                        "AUTO CHECK SKIPPED | MAIN1 API ERROR | user=%s",
                        user_id,
                    )

                    continue

                main2 = await is_member(
                    application.bot,
                    MAIN_GROUP_2_ID,
                    user_id,
                )

                if main2 is None:

                    logger.warning(
                        "AUTO CHECK SKIPPED | MAIN2 API ERROR | user=%s",
                        user_id,
                    )

                    continue

                logger.info(
                    "AUTO CHECK | user=%s | main1=%s | main2=%s",
                    user_id,
                    main1,
                    main2,
                )

                if main1 and main2:
                    continue

                logger.warning(
                    "AUTO REMOVE DETECTED | user=%s",
                    user_id,
                )

                await remove_from_secret(
                    application,
                    user_id,
                    user.get("invite_link"),
                )

        except Exception as e:

            logger.exception(
                "AUTO CHECKER ERROR | %s",
                e,
            )

        await asyncio.sleep(30)


# =========================================================
# BROADCAST BUTTON PARSER
# =========================================================

BUTTON_PATTERN = re.compile(
    r"^\s*\[(.+?)\]\s*-\s*(https?://\S+)\s*$"
)


def parse_broadcast(text: str):

    lines = text.splitlines()

    message_lines = []
    keyboard_rows = []

    for line in lines:

        # -------------------------------------------------
        # MULTIPLE BUTTONS IN ONE ROW
        # -------------------------------------------------

        if "|" in line and "[" in line:

            parts = line.split("|")

            row = []

            valid_row = True

            for part in parts:

                match = BUTTON_PATTERN.match(
                    part.strip()
                )

                if not match:

                    valid_row = False
                    break

                button_text = match.group(1).strip()
                button_url = match.group(2).strip()

                row.append(
                    InlineKeyboardButton(
                        button_text,
                        url=button_url,
                    )
                )

            if valid_row and row:

                keyboard_rows.append(
                    row
                )

                continue

        # -------------------------------------------------
        # SINGLE BUTTON
        # -------------------------------------------------

        match = BUTTON_PATTERN.match(
            line
        )

        if match:

            button_text = match.group(1).strip()
            button_url = match.group(2).strip()

            keyboard_rows.append(
                [
                    InlineKeyboardButton(
                        button_text,
                        url=button_url,
                    )
                ]
            )

            continue

        # -------------------------------------------------
        # NORMAL MESSAGE LINE
        # -------------------------------------------------

        message_lines.append(
            line
        )

    message = "\n".join(
        message_lines
    ).strip()

    keyboard = None

    if keyboard_rows:

        keyboard = InlineKeyboardMarkup(
            keyboard_rows
        )

    return message, keyboard


# =========================================================
# BROADCAST
# =========================================================

async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    if not is_admin(user_id):

        await update.message.reply_text(
            "❌ നിങ്ങൾക്ക് ഈ command ഉപയോഗിക്കാൻ അനുവാദമില്ല."
        )

        return

    if not update.message:

        return

    raw_text = update.message.text or ""

    # Remove /broadcast
    content = raw_text[
        len("/broadcast"):
    ].strip()

    if not content:

        await update.message.reply_text(
            "❌ Broadcast message ഇല്ല.\n\n"
            "Format:\n\n"
            "/broadcast\n"
            "🔥 Hello Everyone!\n\n"
            "[📢 JOIN NOW] - https://t.me/example"
        )

        return

    # =====================================================
    # PARSE
    # =====================================================

    message, keyboard = parse_broadcast(
        content
    )

    if not message:

        await update.message.reply_text(
            "❌ Broadcast message empty ആണ്."
        )

        return

    # =====================================================
    # GET USERS
    # =====================================================

    users = await all_users()

    sent = 0
    failed = 0

    await update.message.reply_text(
        "📢 Broadcast started..."
    )

    # =====================================================
    # SEND
    # =====================================================

    for user in users:

        target_id = user.get("_id")

        if not target_id:
            continue

        try:

            await context.bot.send_message(
                chat_id=target_id,
                text=message,
                reply_markup=keyboard,
            )

            sent += 1

        except Exception as e:

            failed += 1

            logger.warning(
                "BROADCAST FAILED | user=%s | %s",
                target_id,
                e,
            )

        # Avoid Telegram flood
        await asyncio.sleep(0.05)

    # =====================================================
    # RESULT
    # =====================================================

    await update.message.reply_text(
        "✅ Broadcast completed.\n\n"
        f"📨 Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )


# =========================================================
# USERS
# =========================================================

async def users_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Admin only."
        )

        return

    users = await all_users()

    total = len(users)

    active_secret = 0

    for user in users:

        if user.get("secret"):
            active_secret += 1

    await update.message.reply_text(
        "👥 USER STATISTICS\n\n"
        f"👤 Total Users: {total}\n"
        f"🔐 Secret Active: {active_secret}"
    )


# =========================================================
# CHECK USER
# =========================================================

async def check_user_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Admin only."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "Format:\n\n"
            "/checkuser 123456789"
        )

        return

    try:

        target_user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid user ID."
        )

        return

    # =====================================================
    # DATABASE
    # =====================================================

    data = await get_user(
        target_user_id
    )

    # =====================================================
    # MAIN 1
    # =====================================================

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        target_user_id,
    )

    # =====================================================
    # MAIN 2
    # =====================================================

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        target_user_id,
    )

    # =====================================================
    # SECRET
    # =====================================================

    secret = await is_member(
        context.bot,
        SECRET_GROUP_ID,
        target_user_id,
    )

    # =====================================================
    # FORMAT
    # =====================================================

    def status_text(value):

        if value is True:
            return "✅ YES"

        if value is False:
            return "❌ NO"

        return "⚠️ API ERROR"

    db_secret = (
        "✅ YES"
        if data and data.get("secret")
        else "❌ NO"
    )

    await update.message.reply_text(
        "🔎 USER CHECK\n\n"
        f"👤 User ID: `{target_user_id}`\n\n"
        f"📢 Main Group 1: {status_text(main1)}\n"
        f"📢 Main Group 2: {status_text(main2)}\n"
        f"🔐 Secret Group: {status_text(secret)}\n"
        f"💾 DB Secret Access: {db_secret}",
        parse_mode="Markdown",
    )


# =========================================================
# POST INIT
# =========================================================

async def post_init(
    application: Application,
):

    application.create_task(
        auto_remove_checker(
            application
        )
    )

    logger.info(
        "BACKGROUND CHECKER TASK CREATED"
    )


# =========================================================
# APPLICATION
# =========================================================

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(post_init)
    .build()
)


# =========================================================
# USER HANDLERS
# =========================================================

app.add_handler(
    CommandHandler(
        "start",
        start,
    )
)

app.add_handler(
    CallbackQueryHandler(
        check_access,
        pattern=r"^check_access$",
    )
)


# =========================================================
# ADMIN HANDLERS
# =========================================================

app.add_handler(
    CommandHandler(
        "broadcast",
        broadcast,
    )
)

app.add_handler(
    CommandHandler(
        "users",
        users_command,
    )
)

app.add_handler(
    CommandHandler(
        "checkuser",
        check_user_command,
    )
)


# =========================================================
# SECRET GROUP HANDLER
# =========================================================

app.add_handler(
    ChatMemberHandler(
        secret_group_check,
        ChatMemberHandler.CHAT_MEMBER,
    )
)


# =========================================================
# MAIN GROUP HANDLER
# =========================================================

app.add_handler(
    ChatMemberHandler(
        main_group_check,
        ChatMemberHandler.CHAT_MEMBER,
    )
)


# =========================================================
# START
# =========================================================

logger.info(
    "BOT STARTING..."
)


app.run_polling(
    allowed_updates=[
        "message",
        "callback_query",
        "chat_member",
    ],
    drop_pending_updates=True,
)
