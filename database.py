from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI


client = AsyncIOMotorClient(MONGO_URI)

db = client.forcejoin


users = db.users


# =========================
# USER
# =========================

async def add_user(user_id: int):

    await users.update_one(
        {
            "_id": user_id
        },
        {
            "$setOnInsert": {
                "_id": user_id,
                "secret": False,
                "invite_link": None,
                "last_messages": []
            }
        },
        upsert=True
    )


async def get_user(user_id: int):

    return await users.find_one(
        {
            "_id": user_id
        }
    )


# =========================
# SECRET ACCESS
# =========================

async def update_secret(
    user_id: int,
    value: bool
):

    await users.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "secret": value
            }
        }
    )


# =========================
# INVITE LINK
# =========================

async def save_invite(
    user_id: int,
    invite_link: str
):

    await users.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "invite_link": invite_link
            }
        }
    )


async def clear_invite(user_id: int):

    await users.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "invite_link": None
            }
        }
    )


# =========================
# AUTO DELETE
# =========================

async def save_last_messages(
    user_id: int,
    messages: list
):

    await users.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "last_messages": messages
            }
        }
    )


async def get_last_messages(user_id: int):

    data = await users.find_one(
        {
            "_id": user_id
        }
    )

    if not data:
        return []

    return data.get(
        "last_messages",
        []
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
