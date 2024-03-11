import asyncio
import os
import time
from uuid import uuid4

import telethon
import redis
from telethon import TelegramClient, events
from telethon.tl import functions
from telethon.types import Message, UpdateNewMessage
from telethon.tl.functions.messages import ForwardMessagesRequest

from plans import plans_command  # Import the new feature file
from cansend import CanSend
from config import *
from terabox import get_data
from tools import (
    convert_seconds,
    download_file,
    download_image_to_bytesio,
    extract_code_from_url,
    get_formatted_size,
    get_urls_from_string,
    is_user_on_chat,
)

bot = TelegramClient("tele", API_ID, API_HASH)


db = redis.Redis(
    host=HOST,
    port=PORT,
    password=PASSWORD,
    decode_responses=True,
)


@bot.on(events.NewMessage(pattern="/start$", incoming=True, outgoing=False))
async def start(m: UpdateNewMessage):
    reply_text = f"""
 𝐇𝐞𝐥𝐥𝐨! 𝐈 𝐚𝐦 𝐓𝐞𝐫𝐚𝐛𝐨𝐱 𝐕𝐢𝐝𝐞𝐨 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐫 𝐁𝐨𝐭.
𝐒𝐞𝐧𝐝 𝐦𝐞 𝐭𝐞𝐫𝐚𝐛𝐨𝐱 𝐯𝐢𝐝𝐞𝐨 𝐥𝐢𝐧𝐤 & 𝐈 𝐰𝐢𝐥𝐥 𝐬𝐞𝐧𝐝 𝐕𝐢𝐝𝐞𝐨.

𝐏𝐋𝐀𝐍'𝐒 : /plans"""

    # Check if the user is a member of both channels
    channel1 = "@mavimods2"
    channel2 = "@mavibot_support"  # Replace with the actual username of your second channel

    if not await is_user_on_chat(bot, channel1, m.peer_id) or not await is_user_on_chat(bot, channel2, m.peer_id):
        return await m.reply("𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 @mavimods2 𝐚𝐧𝐝 @mavibot_support 𝐛𝐞𝐟𝐨𝐫𝐞 𝐮𝐬𝐢𝐧𝐠 𝐭𝐡𝐞 𝐛𝐨𝐭.")

    await m.reply(reply_text, link_preview=False, parse_mode="markdown")

@bot.on(events.NewMessage(pattern="/start (.*)", incoming=True, outgoing=False))
async def start(m: UpdateNewMessage):
    text = m.pattern_match.group(1)
    fileid = db.get(str(text))

    # Define the channels
    channel1 = "@mavimods2"
    channel2 = "@mavibot_support"

    # Check if the user is a member of both channels
    check_channel1 = await is_user_on_chat(bot, channel1, m.peer_id)
    check_channel2 = await is_user_on_chat(bot, channel2, m.peer_id)

    if not check_channel1 or not check_channel2:
        return await m.reply("𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 @mavimods2 𝐚𝐧𝐝 @mavibot_support 𝐛𝐞𝐟𝐨𝐫𝐞 𝐮𝐬𝐢𝐧𝐠 𝐭𝐡𝐞 𝐛𝐨𝐭.")

    await bot(
        ForwardMessagesRequest(
            from_peer=PRIVATE_CHAT_ID,
            id=[int(fileid)],
            to_peer=m.chat.id,
            drop_author=True,
            noforwards=False,
            background=True,
            drop_media_captions=False,
            with_my_score=True,
        )
    )

# Add the new feature to the bot
@bot.on(events.NewMessage(pattern="/plans$", incoming=True, outgoing=False))
async def plans_command_wrapper(event):
    await plans_command(event)

@bot.on(events.NewMessage(pattern="/adduser (\d+)$", incoming=True, outgoing=False, from_users=ADMINS))
async def add_user_command(m: UpdateNewMessage):
    user_id_to_add = int(m.pattern_match.group(1))
    
    if user_id_to_add not in ADMINS:
        ADMINS.append(user_id_to_add)
        update_config_file()
        await m.reply(f"User ID {user_id_to_add} added to ADMINS list.")
    else:
        await m.reply(f"User ID {user_id_to_add} is already in the ADMINS list.")

def update_config_file():
    with open('config.py', 'r') as config_file:
        lines = config_file.readlines()
    
    for i, line in enumerate(lines):
        if line.startswith("ADMINS = "):
            lines[i] = f"ADMINS = {ADMINS}\n"
            break
    
    with open('config.py', 'w') as config_file:
        config_file.writelines(lines)

@bot.on(
    events.NewMessage(
        pattern="/remove (.*)", incoming=True, outgoing=False, from_users=ADMINS
    )
)
async def remove(m: UpdateNewMessage):
    user_id = m.pattern_match.group(1)
    if db.get(f"check_{user_id}"):
        db.delete(f"check_{user_id}")
        await m.reply(f"Removed {user_id} from the list.")
    else:
        await m.reply(f"{user_id} is not in the list.")


@bot.on(
    events.NewMessage(
        incoming=True,
        outgoing=False,
        func=lambda message: message.text
        and get_urls_from_string(message.text)
        and message.is_private,
    )
)
async def get_message(m: Message):
    asyncio.create_task(handle_message(m))


async def handle_message(m: Message):
    # Define the channels
    channel1 = "@mavimods2"
    channel2 = "@mavibot_support" # Replace with your second channel

    # Check if the user is a member of both channels
    check_channel1 = await is_user_on_chat(bot, channel1, m.peer_id)
    check_channel2 = await is_user_on_chat(bot, channel2, m.peer_id)

    if not check_channel1 or not check_channel2:
        return await m.reply(f"Please join {channel1} and {channel2} then send link.")

    url = get_urls_from_string(m.text)
    if not url:
        return await m.reply("Please enter a valid URL.")

    check_if = await is_user_on_chat(bot, channel1, m.peer_id)
    if not check_if:
        return await m.reply(f"Please join {channel1} then send me the link again.")

    
    hm = await m.reply("Sending you the media, please wait...")

    count = db.get(f"check_{m.sender_id}")
    if count and int(count) > 10:
        return await hm.edit("You are limited now. Please come back after 30 minuts or use another account.")

    shorturl = extract_code_from_url(url)
    if not shorturl:
        return await hm.edit("Seems like your link is invalid.")

    fileid = db.get(shorturl)
    if fileid:
        try:
            await hm.delete()
        except:
            pass

        await bot(
            ForwardMessagesRequest(
                from_peer=PRIVATE_CHAT_ID,
                id=[int(fileid)],
                to_peer=m.chat.id,
                drop_author=True,
                noforwards=False,
                background=True,
                drop_media_captions=False,
                with_my_score=True,
            )
        )

        return

    data = get_data(url)
    if not data:
        return await hm.edit("Sorry! API is dead or maybe your link is broken.")
    db.set(m.sender_id, time.monotonic(), ex=60)
    if (
        not data["file_name"].endswith(".mp4")
        and not data["file_name"].endswith(".mkv")
        and not data["file_name"].endswith(".Mkv")
        and not data["file_name"].endswith(".webm")
        and not data["file_name"].endswith(".MP4")
        and not data["file_name"].endswith(".png")
        and not data["file_name"].endswith(".PNG")
        and not data["file_name"].endswith(".JPG")
        and not data["file_name"].endswith(".jpg")
        and not data["file_name"].endswith(".jpeg")
        and not data["file_name"].endswith(".JPEG")
    ):
        return await hm.edit(
            f"Sorry! File is not supported for now. I can download only .mp4, .mkv and .webm files."
        )
    if int(data["sizebytes"]) > 500000000 and m.sender_id not in ADMINS:
        return await hm.edit(
            f"Sorry! File is too big. I can download only 500 MB and this file is of {data['size']} ."
        )

    start_time = time.time()
    cansend = CanSend()

    async def progress_bar(current_downloaded, total_downloaded, state="Sending"):

        if not cansend.can_send():
            return
        bar_length = 20
        percent = current_downloaded / total_downloaded
        arrow = "◉" * int(percent * bar_length)
        spaces = "◯" * (bar_length - len(arrow))

        elapsed_time = time.time() - start_time

        head_text = f"{state} `{data['file_name']}`"
        progress_bar = f"[{arrow + spaces}] {percent:.2%}"
        upload_speed = current_downloaded / elapsed_time if elapsed_time > 0 else 0
        speed_line = f"Speed: **{get_formatted_size(upload_speed)}/s**"

        time_remaining = (
            (total_downloaded - current_downloaded) / upload_speed
            if upload_speed > 0
            else 0
        )
        time_line = f"Time Remaining: `{convert_seconds(time_remaining)}`"

        size_line = f"Size: **{get_formatted_size(current_downloaded)}** / **{get_formatted_size(total_downloaded)}**"

        await hm.edit(
            f"{head_text}\n{progress_bar}\n{speed_line}\n{time_line}\n{size_line}",
            parse_mode="markdown",
        )

    uuid = str(uuid4())
    thumbnail = download_image_to_bytesio(data["thumb"], "thumbnail.png")

    try:
        file = await bot.send_file(
            PRIVATE_CHAT_ID,
            file=data["direct_link"],
            thumb=thumbnail if thumbnail else None,
            progress_callback=progress_bar,
            caption=f"""
File Name: `{data['file_name']}`
Size: **{data["size"]}** 
Direct Link: [Click Here](https://t.me/MaviTerabox_bot?start={uuid})

@mavimods2
""",
            supports_streaming=True,
            spoiler=True,
        )

        # pm2 start python3 --name "terabox" -- main.py
    except telethon.errors.rpcerrorlist.WebpageCurlFailedError:
        download = await download_file(
            data["direct_link"], data["file_name"], progress_bar
        )
        if not download:
            return await hm.edit(
                f"Sorry! Download Failed but you can download it from [here]({data['direct_link']}).",
                parse_mode="markdown",
            )
        file = await bot.send_file(
            PRIVATE_CHAT_ID,
            download,
            caption=f"""
File Name: `{data['file_name']}`
Size: **{data["size"]}** 
Direct Link: [Click Here](https://t.me/MaviTerabox_bot?start={uuid})

@mavimods2
""",
            progress_callback=progress_bar,
            thumb=thumbnail if thumbnail else None,
            supports_streaming=True,
            spoiler=True,
        )
        try:
            os.unlink(download)
        except Exception as e:
            print(e)
    except Exception:
        return await hm.edit(
            f"Sorry! Download Failed but you can download it from [here]({data['direct_link']}).",
            parse_mode="markdown",
        )
    try:
        os.unlink(download)
    except Exception as e:
        pass
    try:
        await hm.delete()
    except Exception as e:
        print(e)

    if shorturl:
        db.set(shorturl, file.id)
    if file:
        db.set(uuid, file.id)

        await bot(
            ForwardMessagesRequest(
                from_peer=PRIVATE_CHAT_ID,
                id=[file.id],
                to_peer=m.chat.id,
                top_msg_id=m.id,
                drop_author=True,
                noforwards=False,
                background=True,
                drop_media_captions=False,
                with_my_score=True,
            )
        )


bot.start(bot_token=BOT_TOKEN)
bot.run_until_disconnected()
