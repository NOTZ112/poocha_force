from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI


client = AsyncIOMotorClient(MONGO_URI)

db = client.secret_access_bot

users = db.users



async def add_user(user_id: int):

    exists = await users.find_one(
        {
            "user_id": user_id
        }
    )

    if not exists:

        await users.insert_one(
            {
                "user_id": user_id,

                "main1": False,
                "main2": False,

                "secret": False,

                "invite_link": None,
                "invite_used": False,

                "banned": False
            }
        )



async def get_user(user_id: int):

    return await users.find_one(
        {
            "user_id": user_id
        }
    )



async def update_main1(
    user_id: int,
    status: bool
):

    await add_user(user_id)

    await users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set":
            {
                "main1": status
            }
        }
    )



async def update_main2(
    user_id: int,
    status: bool
):

    await add_user(user_id)

    await users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set":
            {
                "main2": status
            }
        }
    )



async def update_secret(
    user_id: int,
    status: bool
):

    await add_user(user_id)

    await users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set":
            {
                "secret": status
            }
        }
    )



async def save_invite(
    user_id: int,
    link: str
):

    await add_user(user_id)

    await users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set":
            {
                "invite_link": link,
                "invite_used": False
            }
        }
    )



async def mark_invite_used(
    user_id: int
):

    await users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set":
            {
                "invite_used": True
            }
        }
    )



async def clear_invite(
    user_id: int
):

    await users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set":
            {
                "invite_link": None,
                "invite_used": False
            }
        }
    )



async def set_banned(
    user_id: int,
    status: bool
):

    await add_user(user_id)

    await users.update_one(
        {
            "user_id": user_id
        },
        {
            "$set":
            {
                "banned": status
            }
        }
    )



async def total_users():

    return await users.count_documents({})
