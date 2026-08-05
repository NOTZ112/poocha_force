from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI


client = AsyncIOMotorClient(MONGO_URI)

db = client["forcejoin"]

users = db["users"]


# =========================
# ADD USER
# =========================

async def add_user(user_id):

    await users.update_one(
        {"_id": user_id},
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

async def get_user(user_id):

    return await users.find_one(
        {"_id": user_id}
    )


# =========================
# SECRET ACCESS
# =========================

async def update_secret(user_id, value):

    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "secret": value
            }
        }
    )


# =========================
# SAVE INVITE LINK
# =========================

async def save_invite(
    user_id,
    invite_link
):

    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "invite_link": invite_link
            }
        },
        upsert=True
    )


# =========================
# GET INVITE LINK
# =========================

async def get_invite(user_id):

    user = await get_user(user_id)

    if not user:
        return None

    return user.get("invite_link")


# =========================
# CLEAR INVITE LINK
# =========================

async def clear_invite(user_id):

    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "invite_link": None
            }
        }
    )


# =========================
# ALL USERS
# =========================

async def get_all_users():

    ids = []

    async for user in users.find():

        ids.append(
            user["_id"]
        )

    return ids
