import logging
import asyncio
import re
import random

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

from telegram.error import (
    RetryAfter,
    TimedOut,
    NetworkError,
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
    level=getattr(logging, LOG_LEVEL, logging.INFO),
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
# BULK / API SETTINGS
# =========================================================

# ഒരേസമയം ഇത്ര Telegram API requests മാത്രം
API_CONCURRENCY = 10

# API error വന്നാൽ maximum retries
API_RETRIES = 4

# Auto checker-ൽ ഒരാൾ കഴിഞ്ഞ് ചെറിയ delay
CHECK_DELAY = 0.08

# Broadcast delay
BROADCAST_DELAY = 0.08


# =========================================================
# API SEMAPHORE
# =========================================================

api_semaphore = asyncio.Semaphore(
    API_CONCURRENCY
)


# =========================================================
# USER REMOVE LOCK
# =========================================================

remove_locks = {}

remove_locks_guard = asyncio.Lock()


async def get_remove_lock(user_id: int):

    async with remove_locks_guard:

        if user_id not in remove_locks:

            remove_locks[user_id] = asyncio.Lock()

        return remove_locks[user_id]


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id: int) -> bool:

    return user_id in ADMIN_IDS


# =========================================================
# SAFE TELEGRAM CALL
# =========================================================

async def safe_telegram_call(
    func,
    *args,
    **kwargs,
):

    delay = 1

    for attempt in range(
        API_RETRIES
    ):

        try:

            async with api_semaphore:

                return await func(
                    *args,
                    **kwargs,
                )

        except RetryAfter as e:

            wait_time = int(
                getattr(
                    e,
                    "retry_after",
                    delay,
                )
            )

            wait_time += random.uniform(
                0.2,
                0.8,
            )

            logger.warning(
                "TELEGRAM FLOOD LIMIT | waiting=%s",
                wait_time,
            )

            await asyncio.sleep(
                wait_time
            )

        except (
            TimedOut,
            NetworkError,
        ) as e:

            logger.warning(
                "TELEGRAM NETWORK ERROR | attempt=%s/%s | %s",
                attempt + 1,
                API_RETRIES,
                e,
            )

            if attempt == API_RETRIES - 1:

                raise

            await asyncio.sleep(
                delay + random.uniform(
                    0,
                    0.5,
                )
            )

            delay = min(
                delay * 2,
                10,
            )

        except Exception:

            raise


# =========================================================
# MEMBER CHECK
# =========================================================

async def is_member(
    bot,
    chat_id,
    user_id,
):

    try:

        member = await safe_telegram_call(
            bot.get_chat_member,
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

        # API error ≠ user left
        return None


# =========================================================
# REMOVE FROM SECRET GROUP
# =========================================================

async def remove_from_secret(
    application: Application,
    user_id: int,
    invite_link=None,
):

    lock = await get_remove_lock(
        user_id
    )

    # ഒരേ user-നെ രണ്ടുതവണ ഒരേസമയം remove ചെയ്യാതിരിക്കാൻ
    async with lock:

        logger.warning(
            "REMOVE FROM SECRET START | user=%s",
            user_id,
        )

        bot = application.bot

        # =================================================
        # REVOKE INVITE
        # =================================================

        if invite_link:

            try:

                await safe_telegram_call(
                    bot.revoke_chat_invite_link,
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

        # =================================================
        # CHECK SECRET GROUP
        # =================================================

        try:

            member = await safe_telegram_call(
                bot.get_chat_member,
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

            # API error ആണെങ്കിൽ DB access clear ചെയ്യരുത്
            return

        # =================================================
        # REMOVE USER
        # =================================================

        if secret_status in ACTIVE_STATUSES:

            try:

                await safe_telegram_call(
                    bot.ban_chat_member,
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

            # =============================================
            # IMMEDIATE UNBAN
            # =============================================

            try:

                await safe_telegram_call(
                    bot.unban_chat_member,
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

        # =================================================
        # CLEAR DATABASE
        # =================================================

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

        # =================================================
        # NOTIFY USER
        # =================================================

        try:

            await safe_telegram_call(
                bot.send_message,
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
        user_id
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
        user_id
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
        user_id
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
                ALREADY_SECRET_TEXT
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

        await safe_telegram_call(
            context.bot.unban_chat_member,
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

        invite = await safe_telegram_call(
            context.bot.create_chat_invite_link,
            chat_id=SECRET_GROUP_ID,
            member_limit=INVITE_MEMBER_LIMIT,
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
            "❌ Invite link create ചെയ്യാൻ കഴിഞ്ഞില്ല."
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

    # =====================================================
    # CHECK BOTH GROUPS
    # =====================================================

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

    # =====================================================
    # DATABASE
    # =====================================================

    data = await get_user(
        user_id
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
# BULK CHECK ONE USER
# =========================================================

async def check_active_user(
    application: Application,
    user: dict,
):

    if not user.get("secret"):
        return

    user_id = user.get("_id")

    if not user_id:
        return

    try:

        main1 = await is_member(
            application.bot,
            MAIN_GROUP_1_ID,
            user_id,
        )

        if main1 is None:
            return

        main2 = await is_member(
            application.bot,
            MAIN_GROUP_2_ID,
            user_id,
        )

        if main2 is None:
            return

        if main1 and main2:
            return

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
            "USER CHECK ERROR | user=%s | %s",
            user_id,
            e,
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

            active_users = [
                user
                for user in users
                if user.get("secret")
                and user.get("_id")
            ]

            total = len(
                active_users
            )

            logger.info(
                "AUTO CHECK START | active_users=%s",
                total,
            )

            # =================================================
            # PROCESS IN CONTROLLED BATCHES
            # =================================================

            for index in range(
                0,
                total,
                API_CONCURRENCY,
            ):

                batch = active_users[
                    index:index + API_CONCURRENCY
                ]

                tasks = []

                for user in batch:

                    tasks.append(
                        asyncio.create_task(
                            check_active_user(
                                application,
                                user,
                            )
                        )
                    )

                if tasks:

                    await asyncio.gather(
                        *tasks,
                        return_exceptions=True,
                    )

                # Small pause between batches
                await asyncio.sleep(
                    CHECK_DELAY
                )

            logger.info(
                "AUTO CHECK COMPLETE | active_users=%s",
                total,
            )

        except asyncio.CancelledError:

            logger.info(
                "AUTO CHECKER CANCELLED"
            )

            raise

        except Exception as e:

            logger.exception(
                "AUTO CHECKER ERROR | %s",
                e,
            )

        await asyncio.sleep(
            AUTO_CHECK_INTERVAL
        )


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

        # =================================================
        # MULTIPLE BUTTONS
        # =================================================

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

                button_text = match.group(
                    1
                ).strip()

                button_url = match.group(
                    2
                ).strip()

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

        # =================================================
        # SINGLE BUTTON
        # =================================================

        match = BUTTON_PATTERN.match(
            line
        )

        if match:

            button_text = match.group(
                1
            ).strip()

            button_url = match.group(
                2
            ).strip()

            keyboard_rows.append(
                [
                    InlineKeyboardButton(
                        button_text,
                        url=button_url,
                    )
                ]
            )

            continue

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

    message, keyboard = parse_broadcast(
        content
    )

    if not message:

        await update.message.reply_text(
            "❌ Broadcast message empty ആണ്."
        )

        return

    users = await all_users()

    sent = 0
    failed = 0

    await update.message.reply_text(
        "📢 Broadcast started..."
    )

    for user in users:

        target_id = user.get(
            "_id"
        )

        if not target_id:
            continue

        try:

            await safe_telegram_call(
                context.bot.send_message,
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

        await asyncio.sleep(
            BROADCAST_DELAY
        )

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

    total = len(
        users
    )

    active_secret = sum(
        1
        for user in users
        if user.get("secret")
    )

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

    data = await get_user(
        target_user_id
    )

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        target_user_id,
    )

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        target_user_id,
    )

    secret = await is_member(
        context.bot,
        SECRET_GROUP_ID,
        target_user_id,
    )

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

    if AUTO_CHECK_ENABLED:

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

if BROADCAST_ENABLED:

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
