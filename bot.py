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
    MessageHandler,
    ContextTypes,
    filters,
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

    await add_user(user.id)

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
            SECRET_GROUP_ID,
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
                chat_id=SECRET_GROUP_ID,
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

        await context.bot.unban_chat_member(
            chat_id=SECRET_GROUP_ID,
            user_id=user.id,
            only_if_banned=True
        )

        print(
            "User unbanned:",
            user.id
        )

    except Exception as e:

        print(
            "Unban error:",
            e
        )

    invite = await context.bot.create_chat_invite_link(
        chat_id=SECRET_GROUP_ID,
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
                    "🔐 സീക്രട്ട് ചാനലിൽ ചേരുക",
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
# SECRET GROUP JOIN CHECK
# =========================

async def secret_join_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    member = update.chat_member

    if member.chat.id != SECRET_GROUP_ID:
        return

    user = member.from_user

    new_status = member.new_chat_member.status

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
            "Secret access granted:",
            user.id
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
        secret_join_check,
        ChatMemberHandler.CHAT_MEMBER
    )
)


print(
    "Bot Started"
)


app.run_polling()
