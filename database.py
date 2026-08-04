from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)

db = client["forcejoin"]

users = db["users"]


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


async def get_user(user_id):
    return await users.find_one(
        {"_id": user_id}
    )


async def save_invite(user_id, invite_link):
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "invite_link": invite_link
            }
        },
        upsert=True
    )


async def update_secret(user_id, value):
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "secret": value
            }
        }
    )


async def clear_invite(user_id):
    await users.update_one(
        {"_id": user_id},
        {
            "$unset": {
                "invite_link": ""
            }
        }
    )


async def get_all_users():
    data = users.find()

    ids = []

    async for user in data:
        ids.append(user["_id"])

    return ids
