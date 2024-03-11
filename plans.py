# plans.py
from telethon import events
from config import ADMINS

async def plans_command(m):
    user_id = m.sender_id
    user = await m.client.get_entity(user_id)

    if user_id in ADMINS:
        # Premium user
        reply_text = f"You are already a premium user, {user.first_name}! 🌟"
    else:
        # Free user
        full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
        reply_text = f"User ID: {user_id}\nName: {full_name}\n\n💠 Premium\n\n  ✓ Download Upto 2.0 GB\n  ✓ Task Limit: NO LIMIT\n  ✓ Time Gap: NO\n  ✓ No Anti-Spam Timer\n  ✓ Validity: 1 MONTH\n\n  Amount: 60 INR ₹\n\nBUY NOW FROM : @Mavisup_bot"

    await m.reply(reply_text, parse_mode="markdown")
