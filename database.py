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
