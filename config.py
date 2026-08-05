import os
from dotenv import load_dotenv

load_dotenv()


# =========================
# BOT
# =========================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

MONGO_URI = os.getenv(
    "MONGO_URI"
)


# =========================
# MAIN GROUPS
# =========================

MAIN_GROUP_1_ID = int(
    os.getenv(
        "MAIN_GROUP_1_ID"
    )
)

MAIN_GROUP_2_ID = int(
    os.getenv(
        "MAIN_GROUP_2_ID"
    )
)


MAIN_GROUP_1_LINK = os.getenv(
    "MAIN_GROUP_1_LINK"
)

MAIN_GROUP_2_LINK = os.getenv(
    "MAIN_GROUP_2_LINK"
)


# =========================
# SECRET CHANNEL
# =========================

SECRET_CHANNEL_ID = int(
    os.getenv(
        "SECRET_CHANNEL_ID"
    )
)


# =========================
# OWNER
# =========================

OWNER_USERNAME = os.getenv(
    "OWNER_USERNAME"
)


# =========================
# TEXTS
# =========================

START_TEXT = """
👋 സ്വാഗതം.

🔒 Secret Channel access ലഭിക്കാൻ
ആദ്യം രണ്ട് Main Group-ലും join ചെയ്യുക.

ശേഷം താഴെയുള്ള button അമർത്തുക.
"""


FAILED_TEXT = """
❌ Access ലഭിച്ചില്ല.

ആദ്യം രണ്ട് Main Group-ലും join ചെയ്യുക.
"""


SUCCESS_TEXT = """
✅ Access Approved.

👇 Secret Channel join ചെയ്യാൻ താഴെയുള്ള link ഉപയോഗിക്കുക.

⚠️ ഈ link ഒരാൾക്ക് മാത്രം ഉപയോഗിക്കാം.
"""


ALREADY_SECRET_TEXT = """
✅ നിങ്ങൾ ഇതിനകം Secret Channel അംഗമാണ്.
"""


REMOVED_TEXT = """
🚫 നിങ്ങളുടെ Secret Channel access നീക്കം ചെയ്തു.

കാരണം:
Main Group-ൽ നിന്ന് പുറത്തായി.
"""


AUTO_DELETE_MESSAGES = True

KEEP_LAST_MESSAGES = 2
