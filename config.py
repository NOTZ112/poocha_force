import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

MAIN_GROUP_1_ID = int(os.getenv("MAIN_GROUP_1_ID"))
MAIN_GROUP_2_ID = int(os.getenv("MAIN_GROUP_2_ID"))

MAIN_GROUP_1_LINK = os.getenv("MAIN_GROUP_1_LINK")
MAIN_GROUP_2_LINK = os.getenv("MAIN_GROUP_2_LINK")

SECRET_CHANNEL_ID = int(os.getenv("SECRET_CHANNEL_ID"))

OWNER_USERNAME = os.getenv("OWNER_USERNAME")


START_TEXT = """
👋 സ്വാഗതം.

Secret Channel ലഭിക്കാൻ
ആദ്യം താഴെയുള്ള രണ്ട് Main Group-ലും Join ചെയ്യുക.

ശേഷം Check Access അമർത്തുക.
"""

FAILED_TEXT = """
❌ നിങ്ങൾ രണ്ട് Main Group-ലും Join ചെയ്തിട്ടില്ല.
"""

SUCCESS_TEXT = """
✅ Access Approved.

താഴെയുള്ള Button ഉപയോഗിച്ച് Secret Channel Join ചെയ്യുക.

⚠️ Link ഒരാൾക്ക് മാത്രം ഉപയോഗിക്കാം.
"""

ALREADY_SECRET_TEXT = """
✅ നിങ്ങൾ ഇതിനകം Secret Channel അംഗമാണ്.
"""

REMOVED_TEXT = """
🚫 Main Group വിട്ടതിനാൽ
Secret Channel Access Remove ചെയ്തു.
"""
