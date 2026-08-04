import os
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

MONGO_URI = os.getenv("MONGO_URI")


MAIN_GROUP_1_ID = int(
    os.getenv("MAIN_GROUP_1_ID")
)

MAIN_GROUP_2_ID = int(
    os.getenv("MAIN_GROUP_2_ID")
)

SECRET_GROUP_ID = int(
    os.getenv("SECRET_GROUP_ID")
)


MAIN_GROUP_1_LINK = os.getenv(
    "MAIN_GROUP_1_LINK"
)

MAIN_GROUP_2_LINK = os.getenv(
    "MAIN_GROUP_2_LINK"
)


OWNER_USERNAME = os.getenv(
    "OWNER_USERNAME"
)


ADMIN_IDS = [
    int(admin)
    for admin in os.getenv(
        "ADMIN_IDS",
        ""
    ).split(",")
    if admin.strip()
]


START_TEXT = """
👋 Welcome!

🔒 Secret Group Access

To enter the Secret Group:

✅ Join Main Group 1
✅ Join Main Group 2

After joining both groups,
press the button below to verify.
"""


SUCCESS_TEXT = """
✅ Verification Successful!

You are eligible to join the Secret Group.

Your single-use invite link is below 👇
"""


FAILED_TEXT = """
❌ Verification Failed!

You must join both Main Groups first.

After joining both groups,
press Check Access again.
"""


REMOVED_TEXT = """
🔒 Secret Group Access Removed

You left one of the required Main Groups.

You have been removed from the Secret Group.

To get access again:

1️⃣ Join both Main Groups
2️⃣ Send /start to the bot
3️⃣ Verify again

Thank you.
"""


ALREADY_SECRET_TEXT = """
✅ You are already a member of the Secret Group.
"""


INVITE_ACTIVE_TEXT = """
♻️ Your previous invite link is still active.
"""
