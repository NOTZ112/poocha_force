import os


# =========================================================
# BOT
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================================================
# MAIN GROUP 1
# =========================================================

MAIN_GROUP_1_ID = int(
    os.getenv(
        "MAIN_GROUP_1_ID",
        "0",
    )
)

MAIN_GROUP_1_LINK = os.getenv(
    "MAIN_GROUP_1_LINK",
    "",
)


# =========================================================
# MAIN GROUP 2
# =========================================================

MAIN_GROUP_2_ID = int(
    os.getenv(
        "MAIN_GROUP_2_ID",
        "0",
    )
)

MAIN_GROUP_2_LINK = os.getenv(
    "MAIN_GROUP_2_LINK",
    "",
)


# =========================================================
# SECRET GROUP
# =========================================================

SECRET_GROUP_ID = int(
    os.getenv(
        "SECRET_GROUP_ID",
        "0",
    )
)


# =========================================================
# TEXTS
# =========================================================

START_TEXT = """
👋 സ്വാഗതം.

🔒 സീക്രട്ട് ഗ്രൂപ്പിൽ പ്രവേശിക്കാൻ
ആദ്യം താഴെയുള്ള രണ്ട് Main Group-കളിലും
അംഗമാകണം.

ശേഷം താഴെയുള്ള
"✅ Check Access" ബട്ടൺ അമർത്തുക.
"""


FAILED_TEXT = """
❌ Access ലഭിച്ചിട്ടില്ല.

🔐 Secret Group-ൽ പ്രവേശിക്കാൻ
താഴെയുള്ള രണ്ട് Main Group-കളിലും
join ചെയ്തിരിക്കണം.

രണ്ടും join ചെയ്ത ശേഷം
"🔄 Check Again" അമർത്തുക.
"""


SUCCESS_TEXT = """
🎉 Access Verified Successfully!

✅ നിങ്ങൾ രണ്ട് Main Group-കളിലും അംഗമാണ്.

🔐 താഴെയുള്ള ബട്ടൺ അമർത്തി
Secret Group-ൽ പ്രവേശിക്കാം.

⚠️ ഈ invite link ഒരു user-ന് മാത്രമാണ്.
"""


ALREADY_SECRET_TEXT = """
✅ നിങ്ങൾ ഇതിനകം Secret Group-ൽ അംഗമാണ്.

🔐 നിങ്ങൾക്ക് Access നിലവിലുണ്ട്.
"""


REMOVED_TEXT = """
⚠️ Secret Group Access Removed.

❌ നിങ്ങൾ Main Group-കളിൽ ഒന്നിൽ നിന്ന്
leave ചെയ്തതിനാൽ Secret Group access
നീക്കം ചെയ്തിരിക്കുന്നു.

🔐 വീണ്ടും access ലഭിക്കാൻ
രണ്ട് Main Group-കളിലും join ചെയ്യുക.
"""
