import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

MAIN_GROUP_1_ID = int(os.getenv("MAIN_GROUP_1_ID"))
MAIN_GROUP_2_ID = int(os.getenv("MAIN_GROUP_2_ID"))
SECRET_GROUP_ID = int(os.getenv("SECRET_GROUP_ID"))
MAIN_GROUP_1_LINK = os.getenv("MAIN_GROUP_1_LINK")
MAIN_GROUP_2_LINK = os.getenv("MAIN_GROUP_2_LINK")
OWNER_USERNAME = os.getenv("OWNER_USERNAME")

ADMIN_IDS = [
    int(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
]

START_TEXT = """
👋 Welcome!

To access the Secret Group, you must join both Main Groups.

After joining both groups, press the button below to verify.
"""

SUCCESS_TEXT = """
✅ Verification Successful!

You are eligible to join the Secret Group.
"""

FAILED_TEXT = """
❌ Verification Failed!

Please join both Main Groups first.
"""

REMOVED_TEXT = """
🔒 Your Secret Group access has been removed.

You left one of the required Main Groups, so you have been removed from the Secret Group.

Join both Main Groups again and send /start to receive a new invite link.
"""
