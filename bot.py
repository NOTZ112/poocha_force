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


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# MEMBER STATUS
# =========================================================

ACTIVE_STATUSES = (
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
)


# =========================================================
# CHECK MEMBER
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

        return status in ACTIVE_STATUSES

    except Exception as e:
        logger.error(
            "MEMBER CHECK ERROR | chat=%s user=%s error=%s",
            chat_id,
            user_id,
            e,
        )

        return False


# =========================================================
# REMOVE USER FROM SECRET CHANNEL
# =========================================================

async def remove_from_secret(
    application: Application,
    user_id: int,
    invite_link=None,
):

    bot = application.bot

    logger.warning(
        "REMOVE FROM SECRET START | user=%s",
        user_id,
    )

    # -----------------------------------------------------
    # REVOKE OLD INVITE
    # -----------------------------------------------------

    if invite_link:

        try:
            await bot.revoke_chat_invite_link(
                chat_id=SECRET_CHANNEL_ID,
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

    # -----------------------------------------------------
    # CHECK SECRET CHANNEL
    # -----------------------------------------------------

    secret_status = None

    try:

        member = await bot.get_chat_member(
            chat_id=SECRET_CHANNEL_ID,
            user_id=user_id,
        )

        secret_status = member.status

        logger.info(
            "SECRET MEMBER STATUS | user=%s | status=%s",
            user_id,
            secret_status,
        )

    except Exception as e:

        logger.info(
            "SECRET MEMBER CHECK | user=%s | %s",
            user_id,
            e,
        )

    # -----------------------------------------------------
    # REMOVE USER
    # -----------------------------------------------------

    if secret_status in ACTIVE_STATUSES:

        try:

            await bot.ban_chat_member(
                chat_id=SECRET_CHANNEL_ID,
                user_id=user_id,
            )

            logger.warning(
                "SECRET USER REMOVED/BANNED | user=%s",
                user_id,
            )

            # -------------------------------------------------
            # UNBAN IMMEDIATELY
            # User is removed but not permanently banned.
            # -------------------------------------------------

            try:

                await bot.unban_chat_member(
                    chat_id=SECRET_CHANNEL_ID,
                    user_id=user_id,
                    only_if_banned=True,
                )

                logger.info(
                    "SECRET USER UNBANNED | user=%s",
                    user_id,
                )

            except Exception as e:

                logger.warning(
                    "SECRET UNBAN FAILED | user=%s | %s",
                    user_id,
                    e,
                )

        except Exception as e:

            logger.error(
                "SECRET REMOVE FAILED | user=%s | %s",
                user_id,
                e,
            )

    else:

        logger.info(
            "USER NOT ACTIVE IN SECRET | user=%s",
            user_id,
        )

    # -----------------------------------------------------
    # CLEAR DATABASE
    # -----------------------------------------------------

    try:

        await update_secret(
            user_id,
            False,
        )

        await clear_invite(
            user_id,
        )

        logger.info(
            "SECRET ACCESS CLEARED | user=%s",
            user_id,
        )

    except Exception as e:

        logger.error(
            "DATABASE CLEAR ERROR | user=%s | %s",
            user_id,
            e,
        )

    # -----------------------------------------------------
    # NOTIFY USER
    # -----------------------------------------------------

    try:

        await bot.send_message(
            chat_id=user_id,
            text=REMOVED_TEXT,
        )

        logger.info(
            "REMOVAL MESSAGE SENT | user=%s",
            user_id,
        )

    except Exception as e:

        logger.info(
            "REMOVAL MESSAGE FAILED | user=%s | %s",
            user_id,
            e,
        )

    logger.warning(
        "REMOVE FROM SECRET COMPLETE | user=%s",
        user_id,
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

    await add_user(user_id)

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

    await query.answer()

    user_id = query.from_user.id

    await add_user(user_id)

    # -----------------------------------------------------
    # CHECK MAIN GROUP 1
    # -----------------------------------------------------

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        user_id,
    )

    # -----------------------------------------------------
    # CHECK MAIN GROUP 2
    # -----------------------------------------------------

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        user_id,
    )

    logger.info(
        "MANUAL ACCESS CHECK | user=%s | main1=%s | main2=%s",
        user_id,
        main1,
        main2,
    )

    # -----------------------------------------------------
    # NOT BOTH
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # GET USER DATA
    # -----------------------------------------------------

    data = await get_user(user_id)

    # -----------------------------------------------------
    # ALREADY SECRET ACTIVE
    # -----------------------------------------------------

    if data and data.get("secret"):

        still_member = await is_member(
            context.bot,
            SECRET_CHANNEL_ID,
            user_id,
        )

        if still_member:

            await query.message.reply_text(
                ALREADY_SECRET_TEXT,
            )

            return

        # DB active but actually not inside
        await update_secret(
            user_id,
            False,
        )

        await clear_invite(
            user_id,
        )

    # -----------------------------------------------------
    # REMOVE OLD BAN
    # -----------------------------------------------------

    try:

        await context.bot.unban_chat_member(
            chat_id=SECRET_CHANNEL_ID,
            user_id=user_id,
            only_if_banned=True,
        )

        logger.info(
            "OLD BAN CLEARED | user=%s",
            user_id,
        )

    except Exception as e:

        logger.info(
            "OLD BAN CHECK | user=%s | %s",
            user_id,
            e,
        )

    # -----------------------------------------------------
    # CREATE SINGLE USE INVITE
    # -----------------------------------------------------

    try:

        invite = await context.bot.create_chat_invite_link(
            chat_id=SECRET_CHANNEL_ID,
            member_limit=1,
        )

        await save_invite(
            user_id,
            invite.invite_link,
        )

        logger.info(
            "NEW INVITE CREATED | user=%s",
            user_id,
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

    # -----------------------------------------------------
    # SEND INVITE
    # -----------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔐 Join Secret Channel",
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
# SECRET CHANNEL MEMBER UPDATE
# =========================================================

async def secret_channel_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    member_update = update.chat_member

    if not member_update:
        return

    chat_id = member_update.chat.id

    if chat_id != SECRET_CHANNEL_ID:
        return

    user = member_update.new_chat_member.user
    new_status = member_update.new_chat_member.status

    logger.info(
        "SECRET CHANNEL UPDATE | user=%s | new_status=%s",
        user.id,
        new_status,
    )

    # -----------------------------------------------------
    # USER JOINED
    # -----------------------------------------------------

    if new_status in ACTIVE_STATUSES:

        await update_secret(
            user.id,
            True,
        )

        logger.info(
            "SECRET ACCESS ACTIVE | user=%s",
            user.id,
        )

        return

    # -----------------------------------------------------
    # USER LEFT SECRET CHANNEL
    # -----------------------------------------------------

    if new_status in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
    ):

        await update_secret(
            user.id,
            False,
        )

        await clear_invite(
            user.id,
        )

        logger.info(
            "SECRET ACCESS CLEARED AFTER LEAVE | user=%s",
            user.id,
        )


# =========================================================
# MAIN GROUP MEMBER UPDATE
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

    new_status = member_update.new_chat_member.status

    old_status = member_update.old_chat_member.status

    logger.info(
        "MAIN GROUP UPDATE | chat=%s | user=%s | old=%s | new=%s",
        chat_id,
        user.id,
        old_status,
        new_status,
    )

    # -----------------------------------------------------
    # ONLY LEAVE / BAN
    # -----------------------------------------------------

    if new_status not in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
    ):

        return

    user_id = user.id

    logger.warning(
        "MAIN GROUP LEFT/BANNED | chat=%s | user=%s",
        chat_id,
        user_id,
    )

    # -----------------------------------------------------
    # CHECK BOTH GROUPS
    # -----------------------------------------------------

    main1 = await is_member(
        context.bot,
        MAIN_GROUP_1_ID,
        user_id,
    )

    main2 = await is_member(
        context.bot,
        MAIN_GROUP_2_ID,
        user_id,
    )

    logger.info(
        "ACCESS CHECK AFTER LEAVE | user=%s | main1=%s | main2=%s",
        user_id,
        main1,
        main2,
    )

    # -----------------------------------------------------
    # BOTH STILL ACTIVE
    # -----------------------------------------------------

    if main1 and main2:

        logger.info(
            "USER STILL MEMBER OF BOTH | user=%s",
            user_id,
        )

        return

    # -----------------------------------------------------
    # GET DATABASE
    # -----------------------------------------------------

    data = await get_user(user_id)

    if not data:

        logger.info(
            "USER NOT FOUND | user=%s",
            user_id,
        )

        return

    # -----------------------------------------------------
    # NO SECRET ACCESS
    # -----------------------------------------------------

    if not data.get("secret"):

        logger.info(
            "NO SECRET ACCESS | user=%s",
            user_id,
        )

        # Even if DB secret is false,
        # revoke an unused invite if one exists.

        old_invite = data.get("invite_link")

        if old_invite:

            try:

                await context.bot.revoke_chat_invite_link(
                    chat_id=SECRET_CHANNEL_ID,
                    invite_link=old_invite,
                )

            except Exception:
                pass

            await clear_invite(user_id)

        return

    # -----------------------------------------------------
    # ACCESS LOST
    # -----------------------------------------------------

    logger.warning(
        "SECRET ACCESS LOST | user=%s",
        user_id,
    )

    await remove_from_secret(
        context.application,
        user_id,
        data.get("invite_link"),
    )


# =========================================================
# BACKGROUND AUTO CHECKER
# =========================================================

async def auto_remove_checker(
    application: Application,
):

    logger.info(
        "AUTO CHECKER STARTED",
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

                # -------------------------------------------------
                # MAIN GROUP 1
                # -------------------------------------------------

                main1 = await is_member(
                    application.bot,
                    MAIN_GROUP_1_ID,
                    user_id,
                )

                # -------------------------------------------------
                # MAIN GROUP 2
                # -------------------------------------------------

                main2 = await is_member(
                    application.bot,
                    MAIN_GROUP_2_ID,
                    user_id,
                )

                logger.info(
                    "AUTO CHECK | user=%s | main1=%s | main2=%s",
                    user_id,
                    main1,
                    main2,
                )

                # -------------------------------------------------
                # BOTH OK
                # -------------------------------------------------

                if main1 and main2:
                    continue

                # -------------------------------------------------
                # ACCESS LOST
                # -------------------------------------------------

                logger.warning(
                    "AUTO REMOVE DETECTED | user=%s",
                    user_id,
                )

                await remove_from_secret(
                    application,
                    user_id,
                    user.get("invite_link"),
                )

            logger.info(
                "AUTO CHECK COMPLETE | active_users_checked=%s",
                checked,
            )

        except Exception as e:

            logger.exception(
                "AUTO CHECKER ERROR | %s",
                e,
            )

        # -----------------------------------------------------
        # CHECK EVERY 30 SECONDS
        # -----------------------------------------------------

        await asyncio.sleep(30)


# =========================================================
# POST INIT
# =========================================================

async def post_init(
    application: Application,
):

    application.create_task(
        auto_remove_checker(
            application,
        )
    )

    logger.info(
        "BACKGROUND CHECKER TASK CREATED",
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
# START
# =========================================================

app.add_handler(
    CommandHandler(
        "start",
        start,
    )
)


# =========================================================
# CHECK ACCESS
# =========================================================

app.add_handler(
    CallbackQueryHandler(
        check_access,
        pattern=r"^check_access$",
    )
)


# =========================================================
# SECRET CHANNEL HANDLER
# =========================================================

app.add_handler(
    ChatMemberHandler(
        secret_channel_check,
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
# START BOT
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
