from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI


client = AsyncIOMotorClient(
    MONGO_URI
)

db = client.forcejoin


users = db.users


# =========================
# ADD USER
# =========================

async def add_user(
    user_id: int
):

    await users.update_one(
        {
            "_id": user_id
        },
        {
            "$setOnInsert": {
                "_id": user_id,
                "secret": False,
                "invite_link": None
            }
        },
        upsert=True
    )


# =========================
# GET USER
# =========================

async def get_user(
    user_id: int
):

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
    link: str
):

    await users.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "invite_link": link
            }
        }
    )


async def clear_invite(
    user_id: int
):

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
