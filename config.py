# =========================================================
# CONFIG.PY
# =========================================================

import os
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# BOT
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")


# =========================================================
# DATABASE
# =========================================================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing")


# =========================================================
# MAIN GROUP 1
# =========================================================

MAIN_GROUP_1_ID = int(
    os.getenv("MAIN_GROUP_1_ID", "0")
)

MAIN_GROUP_1_LINK = os.getenv(
    "MAIN_GROUP_1_LINK",
    ""
)


# =========================================================
# MAIN GROUP 2
# =========================================================

MAIN_GROUP_2_ID = int(
    os.getenv("MAIN_GROUP_2_ID", "0")
)

MAIN_GROUP_2_LINK = os.getenv(
    "MAIN_GROUP_2_LINK",
    ""
)


# =========================================================
# SECRET GROUP
# =========================================================

SECRET_GROUP_ID = int(
    os.getenv("SECRET_GROUP_ID", "0")
)

SECRET_GROUP_LINK = os.getenv(
    "SECRET_GROUP_LINK",
    ""
)


# =========================================================
# OWNER
# =========================================================

OWNER_USERNAME = os.getenv(
    "OWNER_USERNAME",
    ""
)


# =========================================================
# ADMIN IDS
# =========================================================

ADMIN_IDS = []

_admin_ids = os.getenv(
    "ADMIN_IDS",
    ""
)

if _admin_ids:
    for admin_id in _admin_ids.split(","):

        admin_id = admin_id.strip()

        if not admin_id:
            continue

        try:
            ADMIN_IDS.append(
                int(admin_id)
            )
        except ValueError:
            pass


# =========================================================
# TEXTS
# =========================================================

START_TEXT = """
👋 <b>സ്വാഗതം</b>

🔐 Secret Group-ൽ പ്രവേശിക്കാൻ
താഴെയുള്ള രണ്ട് Main Group-കളിലും
ആദ്യം Join ചെയ്യുക.

✅ രണ്ടിലും Join ചെയ്ത ശേഷം
<b>Check Access</b> അമർത്തുക.
"""


FAILED_TEXT = """
❌ <b>Access ലഭിച്ചിട്ടില്ല</b>

Secret Group-ൽ പ്രവേശിക്കാൻ
താഴെയുള്ള രണ്ട് Main Group-കളിലും
Join ചെയ്തിരിക്കണം.

👇 രണ്ടിലും Join ചെയ്ത ശേഷം
<b>Check Again</b> അമർത്തുക.
"""


SUCCESS_TEXT = """
🎉 <b>Access Verified!</b>

🔐 Secret Group-ൽ പ്രവേശിക്കാൻ
താഴെയുള്ള ബട്ടൺ അമർത്തുക.

⚠️ Main Group-കളിൽ ഏതെങ്കിലും ഒന്നിൽ
നിന്നും Leave ചെയ്താൽ Secret Access
നഷ്ടപ്പെടും.
"""


ALREADY_SECRET_TEXT = """
✅ <b>Secret Group Access ഇതിനകം ഉണ്ട്.</b>

🔐 നിങ്ങൾ Secret Group-ൽ നിലവിൽ അംഗമാണ്.
"""


REMOVED_TEXT = """
⚠️ <b>Secret Access Removed</b>

Main Group-കളിൽ ഏതെങ്കിലും ഒന്നിൽ നിന്ന്
നിങ്ങൾ Leave ചെയ്തതിനാൽ Secret Group
Access നീക്കം ചെയ്തിരിക്കുന്നു.

🔒 വീണ്ടും Access ലഭിക്കാൻ രണ്ട് Main Group-കളിലും
Join ചെയ്യുക.
"""


# =========================================================
# BROADCAST
# =========================================================

BROADCAST_ENABLED = True

# Broadcast message-ൽ Inline Button support
BROADCAST_BUTTON_ENABLED = True


# =========================================================
# AUTO USER CHECK
# =========================================================

AUTO_CHECK_ENABLED = True

# 30 seconds
AUTO_CHECK_INTERVAL = 30


# =========================================================
# SECRET GROUP INVITE
# =========================================================

# ഓരോ user-നും ഒരു invite മാത്രം ഉപയോഗിക്കാൻ
INVITE_MEMBER_LIMIT = 1


# =========================================================
# LOGGING
# =========================================================

LOG_LEVEL = "INFO"
