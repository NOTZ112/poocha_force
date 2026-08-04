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



# CHECK MEMBER
async def is_member(
    bot,
    chat_id: int,
    user_id: int
):

    try:

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




# START COMMAND
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
                    "✅ Check Access",
                    callback_data="check_access"
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


    await update.message.reply_text(
        START_TEXT,
        reply_markup=keyboard
    )





# CHECK ACCESS
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




    data = await get_user(
        user.id
    )



    if data and data.get("secret"):

        still_member = await is_member(
            context.bot,
            SECRET_GROUP_ID,
            user.id
        )


        if still_member:

            await query.message.reply_text(
                "✅ Secret Group access already active."
            )

            return


        else:

            await update_secret(
                user.id,
                False
            )



    # CREATE NEW INVITE

    await clear_invite(
        user.id
    )


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

    

# SECRET GROUP JOIN SAVE
async def secret_group_monitor(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.chat_member is None:
        return

    chat_id = update.chat_member.chat.id

    if chat_id != SECRET_GROUP_ID:
        return

    member = update.chat_member.new_chat_member

    print(
        "SECRET UPDATE:",
        member.user.id,
        member.status
    )

    if member.status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR
    ):

        user = member.user

        await update_secret(
            user.id,
            True
        )

        print(
            f"Secret Access Added : {user.id}"
        )



# MAIN GROUP LOCK
async def monitor_groups(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print("MAIN GROUP UPDATE RECEIVED")

    if update.chat_member is None:
        return


    # DEBUG CHECK
    print(
        update.chat_member.old_chat_member.status,
        "->",
        update.chat_member.new_chat_member.status
    )


    chat_id = update.chat_member.chat.id


    # Only main groups
    if chat_id not in (
        MAIN_GROUP_1_ID,
        MAIN_GROUP_2_ID
    ):
        return



    user = update.chat_member.new_chat_member.user


    if user.is_bot:
        return



    # Check both main groups
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


    # User still in both groups
    if main1 and main2:
        return



    # Remove from secret group
    try:

        await context.bot.ban_chat_member(
            chat_id=SECRET_GROUP_ID,
            user_id=user.id,
            revoke_messages=False
        )

        await context.bot.unban_chat_member(
            chat_id=SECRET_GROUP_ID,
            user_id=user.id,
            only_if_banned=True
        )

        member = await context.bot.get_chat_member(
            SECRET_GROUP_ID,
            user.id
        )

        print(
            "SECRET STATUS:",
            member.status
        )

        await update_secret(
            user.id,
            False
        )

        await clear_invite(
            user.id
        )

        print(
            f"Removed From Secret : {user.id}"
        )

    except Exception as e:

        print(
            f"Remove Error : {e}"
        )


# =========================
# BROADCAST START
# =========================

def is_admin(user_id):
    return user_id in ADMIN_IDS


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Reply to a message and use /broadcast"
        )
        return

    users = await get_all_users()

    sent = 0
    failed = 0

    status = await update.message.reply_text(
        "Broadcasting..."
    )

    for user_id in users:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.reply_to_message.message_id
            )
            sent += 1
        except:
            failed += 1

    await status.edit_text(
        f"Done\n\nSent : {sent}\nFailed : {failed}"
    )

# =========================
# BROADCAST END
# =========================





# HANDLERS


app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CommandHandler(
        "broadcast",
        broadcast
    )
)

app.add_handler(
    CallbackQueryHandler(
        check_access,
        pattern="check_access"
    )
)



app.add_handler(
    ChatMemberHandler(
        monitor_groups,
        ChatMemberHandler.CHAT_MEMBER
    )
)


app.add_handler(
    ChatMemberHandler(
        secret_group_monitor,
        ChatMemberHandler.CHAT_MEMBER
    )
)





print(
    "Secret Lock Bot Started..."
)



app.run_polling(
    allowed_updates=[
        "message",
        "callback_query",
        "chat_member"
    ]
)
