"""
CREDITS:

-GGProGaming / Nathan G: creator of this bot
-Micro: for hosting the bot and giving feedback
-funlennysub: for the original bot
-Thomasims: Teardown API scraper script

-Source Code: https://github.com/GGProGaming/Teardown-Support-Bot
"""

import interactions
from interactions import Client, slash_command, SlashCommandOption, SlashCommandChoice, SlashContext, Intents, EmbedAttachment, cooldown, Buckets, subcommand, slash_option, OptionType, AutocompleteContext, EmbedAttachment, Task, IntervalTrigger, listen, Member, File, Permissions, ActionRow, Button, ButtonStyle, StringSelectMenu, component_callback, ComponentContext, spread_to_rows, Extension
from interactions.client.errors import CommandOnCooldown
from interactions.ext import prefixed_commands
from interactions.ext.prefixed_commands import prefixed_command, PrefixedContext
import json
import os
import re
import io
import collections
import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging
import steam_workshop
import typst
import subprocess
import tempfile
import random
import numpy as np
from PyPDF2 import PdfReader
from typing import Generator, Dict
from PIL import ImageOps, Image, ImageDraw
from pdf2image import convert_from_path
import matplotlib.pyplot as plt
# this import should be EXACTLY in this format
from interactions.client import const
const.CLIENT_FEATURE_FLAGS["FOLLOWUP_INTERACTIONS_FOR_IMAGES"] = True

bot = Client(intents=Intents.DEFAULT, sync_interactions=True, asyncio_debug=True)
prefixed_commands.setup(bot)

# List of roles that can delete tags
required_roles = ["Tech Support", "Moderator", "Admin"]

# Helper function to check if the user has required roles
def has_required_role(member):
    if isinstance(member, Member):
        return any(role.name in required_roles for role in member.roles)
    else:
        return False
    
def load_muted_users():
    if os.path.exists('/root/TTS/muted_users.json'):
        with open('/root/TTS/muted_users.json', 'r') as mute_file:
            data = mute_file.read()
            return json.loads(data) if data else {}
    else:
        return {}

# Create a task that runs every minute
@Task.create(IntervalTrigger(minutes=1))
async def decrease_mute_time():
    # Check if the mute file exists
    if os.path.exists('/root/TTS/muted_users.json'):
        # Load the mute file
        with open('/root/TTS/muted_users.json', 'r') as mute_file:
            muted_users = json.load(mute_file)

        # Get the current time
        current_time = datetime.utcnow()

        # Create a list of users to remove from the mute file
        users_to_remove = []

        # Iterate over the muted users
        for user, end_time_str in muted_users.items():
            # Convert the end time from string to datetime
            end_time = datetime.fromisoformat(end_time_str)

            # If the current time is later than or equal to the end time, add the user to the list of users to remove
            if current_time >= end_time:
                users_to_remove.append(user)

        # Remove the users from the mute file
        for user in users_to_remove:
            del muted_users[user]

        # Write the updated mute file
        with open('muted_users.json', 'w') as mute_file:
            json.dump(muted_users, mute_file)

@listen()
async def on_startup():
    decrease_mute_time.start()

# Scope variable...

# Writing this like 4 months later. I have no idea what this does but something in the interactions-py docs need it.
scope = [760105076755922996, 831277268873117706]

@slash_command(name="managemute", description="Manage user mute status", scopes=scope, dm_permission=False, default_member_permissions=Permissions.MANAGE_EMOJIS_AND_STICKERS)
@slash_option(
    name="action",
    description="Choose an action",
    opt_type=OptionType.STRING,
    required=True,
    choices=[
        {"name": "Mute User", "value": "mute"},
        {"name": "View Muted Users", "value": "view"},
        {"name": "Unmute User", "value": "remove"},
    ],
)

@slash_option(name="user", description="The user", opt_type=OptionType.USER, required=False, autocomplete=True)
@slash_option(name="duration", description="Duration of the mute in minutes", opt_type=OptionType.INTEGER, required=False)
async def moderate(ctx: SlashContext, action: str, user: str = None, duration: int = None):
    has_role = has_required_role(ctx.author)
    if not has_role:
        await ctx.send("You do not have permission to use this command.", silent=True, ephemeral=True)
        return

    if action == "mute":
        if user and duration:
            await mute_user(ctx, user, duration)
        else:
            await ctx.send("You must provide a user and duration to mute a user.", silent=True, ephemeral=True)
    elif action == "view":
        await view_muted_users(ctx)
    elif action == "remove":
        if user:
            await remove_mute(ctx, user)
        else:
            await ctx.send("You must provide a user to remove a mute.", silent=True, ephemeral=True)

async def mute_user(ctx: SlashContext, user: Member, duration: int):
    usage_statistics["Muted"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    mute_end_time = datetime.utcnow() + timedelta(minutes=duration)
    muted_users = load_muted_users()

    muted_users[str(user.id)] = mute_end_time.isoformat()
    with open('/root/TTS/muted_users.json', 'w') as mute_file:
        json.dump(muted_users, mute_file)

    if duration >= 1440:
        mute_duration = f"{duration // 1440} days"
    elif duration >= 60:
        mute_duration = f"{duration // 60} hours, {duration % 60} minutes"
    else:
        mute_duration = f"{duration} minutes"

    await ctx.send(f"Muted {user.display_name} for {mute_duration}.", silent=True, ephemeral=True)

async def view_muted_users(ctx: SlashContext):
    muted_users = load_muted_users()
    if muted_users:
        response = "```"
        for user_id, end_time_str in muted_users.items():
            end_time = datetime.fromisoformat(end_time_str)
            remaining_time = end_time - datetime.utcnow()
            user = await ctx.bot.fetch_user(int(user_id))
            if remaining_time.days > 0:
                response += f"{user.display_name} : {remaining_time.days} days remaining\n"
            elif remaining_time.seconds >= 3600:
                hours = remaining_time.seconds // 3600
                minutes = (remaining_time.seconds % 3600) // 60
                response += f"{user.display_name} : {hours} hours, {minutes} minutes remaining\n"
            elif remaining_time.seconds >= 60:
                response += f"{user.display_name} : {remaining_time.seconds // 60} minutes, {remaining_time.seconds % 60} seconds remaining\n"
            else:
                response += f"{user.display_name} : {remaining_time.seconds} seconds remaining\n"
        response += "```"
        embed = interactions.Embed(title="Muted Users", description=response, color=0xe9254e)
        await ctx.send(embed=embed, silent=True, ephemeral=True)    
    else:
        await ctx.send("No users are currently muted.", silent=True, ephemeral=True)

async def remove_mute(ctx: SlashContext, user: Member):
    muted_users = load_muted_users()
    if str(user.id) in muted_users:
        del muted_users[str(user.id)]
        with open('/root/TTS/muted_users.json', 'w') as mute_file:
            json.dump(muted_users, mute_file)
        await ctx.send(f"Unmuted {user.display_name}.", silent=True, ephemeral=True)

async def check_mute(ctx: SlashContext):
    muted_users = load_muted_users()
    if str(ctx.author.id) in muted_users:
        end_time = datetime.fromisoformat(muted_users[str(ctx.author.id)])
        remaining_time = end_time - datetime.utcnow()
        if remaining_time.days > 0:
            await ctx.send(f"You are currently muted and cannot use the bot. You have {remaining_time.days} days remaining before you can try again.", ephemeral=True)
        elif remaining_time.seconds >= 3600:
            hours = remaining_time.seconds // 3600
            minutes = (remaining_time.seconds % 3600) // 60
            await ctx.send(f"You are currently muted and cannot use the bot. You have {hours} hours, {minutes} minutes remaining before you can try again.", ephemeral=True)
        elif remaining_time.seconds >= 60:
            await ctx.send(f"You are currently muted and cannot use the bot. You have {remaining_time.seconds // 60} minutes, {remaining_time.seconds % 60} seconds remaining before you can try again.", ephemeral=True)
        else:
            await ctx.send(f"You are currently muted and cannot use the bot. You have {remaining_time.seconds} seconds remaining before you can try again.", ephemeral=True)
        raise ValueError("User is muted")

# Tech Support Slash Command
@slash_command(name="techsupport", description="Get answers to basic tech support questions", options=[SlashCommandOption(name="question", description="Enter your question", type=3, required=True)])
async def _techsupport(ctx: SlashContext, question: str):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Tech Support"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    image = None
    if question == 'drivers':
        response = (
        '1. For Nvidia Users:\nYou can update drivers via Geforce Experience or their [driver page](https://www.nvidia.com/download/index.aspx).\n'
        '2. For AMD Users:\nYou can check for updates using the AMD Radeon Settings or by navigating to their [driver page](https://www.amd.com/en/support).\n'
        '3. After updating drivers, search for "Windows Update" in the Start menu and install any available updates.\n'
        '4. Once updates are installed, restart your computer.')
        embed = interactions.Embed(title="Update drivers and Windows and reboot", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    elif question == 'verify':
        response = ('1. Open the Steam client.\n'
                    '2. Navigate to your Library.\n'
                    '3. Right-click on Teardown and select "Properties".\n'
                    '4. Click on the "Local Files" tab.\n'
                    '5. Click "Verify Integrity of Game Files".')
        image_url = 'https://media.discordapp.net/attachments/1070933425005002812/1102841814676951060/Screenshot_1.png'
        image = EmbedAttachment(url=image_url)
        embed = interactions.Embed(title="Verify Steam Files", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    elif question == 'appdata':
        response = (
        '1. Press the Windows key + R to open the Run dialog. Or open file explorer and select the top search bar.\n'
        '2. Type %localappdata% and press Enter.\n'
        '3. Navigate to the "Teardown" folder.')
        embed = interactions.Embed(title="Find Appdata local files", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    elif question == 'cpu_gpu':
        response = (
        '1. Press the Windows key type in "Task Manager" or enter the shortcut, "ctrl+shift+esc"\n'
        '2. Go to the Performance tab and look for CPU and GPU sections.\n'
        '3. You can see the name, usage, speed, and temperature of your CPU and GPU.\n'
        '4. Relevant information the support team will need is the name of the CPU and GPU.'
        )
        image_url = 'https://cdn.discordapp.com/attachments/1092731528808775780/1092820549203398787/image0.jpg'
        image = EmbedAttachment(url=image_url)
        embed = interactions.Embed(title="Find CPU and GPU information", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    elif question == 'ddu':
        response = (
            '1. Download Display Driver Uninstaller (DDU) from the official website: https://www.wagnardsoft.com/.\n'
            '2. Boot your computer into [Safe Mode](https://support.microsoft.com/en-us/windows/start-your-pc-in-safe-mode-in-windows-92c27cff-db89-8644-1ce4-b3e5e56fe234#WindowsVersion=Windows_11).\n'
            '3. Run DDU and select your GPU manufacturer from the drop-down menu.\n'
            '4. Click "Clean and restart".\n'
            '5. After restarting, download and install the latest GPU drivers from the manufacturer\'s website.'
        )
        embed = interactions.Embed(title="Perform DDU Process", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    elif question == 'artifacts':
        response = (
          '1. Update your graphics card drivers to the latest version.\n'
          '2. Disable any overlays such as the Razer Overlay.\n'
      )
        image_url = 'https://media.discordapp.net/attachments/1069850310782234635/1069850311235207258/image.png?width=1562&height=905'
        image = EmbedAttachment(url=image_url)
        embed = interactions.Embed(title="Artifacts", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    elif question == "nosound":
        response = (
          'When starting Teardown, avoid alt-tabbing or unfocusing the window while it starts.'
      )
        embed = interactions.Embed(title="No Sound", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    elif question == "disable":
        response = (
            'Open the mod menu in Teardown, right click in the middle column, and select "Disable All"'
        )
        image_url = 'https://media.discordapp.net/attachments/831277268873117709/1108495756488364042/image.png'
        image = EmbedAttachment(url=image_url)
        embed = interactions.Embed(title="Disable Mods", description=response, color=0x41bfff)
        if image:
            embed.image = image
        await ctx.send(embed=embed, silent=True)
    else:
        response = 'Invalid question'
        embed = interactions.Embed(title="Tech Support", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True, delete_after=4)

@_techsupport.autocomplete("question")
async def techsupport_autocomplete(ctx: AutocompleteContext):
    choices = [
        {"name": "Update drivers and Windows", "value": "drivers"},
        {"name": "Verify Steam files", "value": "verify"},
        {"name": "Find AppData local files", "value": "appdata"},
        {"name": "Find CPU and GPU information", "value": "cpu_gpu"},
        {"name": "Perform DDU process", "value": "ddu"},
        {"name": "Artifacts", "value": "artifacts"},
        {"name": "No Sound", "value": "nosound"},
        {"name": "Disable Mods", "value": "disable"},
    ]

    matching_choices = [
        choice for choice in choices if ctx.input_text.lower() in choice["name"].lower()
    ]

    await ctx.send(choices=matching_choices)

# FAQ Slash Command
@slash_command(name="faq", description="Get answers to frequently asked questions", options=[SlashCommandOption(name="question", description="Enter your question", type=3, required=True)])
async def _faq(ctx: SlashContext, question: str):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["FAQ"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    if question == 'progress':
        response = "You can reset your game progress by going to options in the main menu, clicking the game button, and then clicking reset progress."
        embed = interactions.Embed(title="How do I reset my progress?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'resources':
        response = (
            '1. The official Teardown modding documentation can be found [here](https://teardowngame.com/modding/index.html).\n'
            '2. The official Teardown modding API documentation can be found [here](https://teardowngame.com/modding/api.html).\n'
            '3. The offical voxtool... tool can be found [here](https://teardowngame.com/voxtool/).\n'
            '4. There are many tutorials and guides found here: https://discord.com/channels/760105076755922996/771750716456697886.\n'
            '5. You can find the magicavoxel application [here](https://ephtracy.github.io/).\n'
            '6. You can ask questions in https://discord.com/channels/760105076755922996/768940642767208468.\n'
        )
        embed = interactions.Embed(title="Modding Resources", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'part3':
        response = "There will not be a Part 3. Teardown is a complete game and will not be receiving any more main campaign updates."
        embed = interactions.Embed(title="Will there be a part 3?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'multiplayer':
        response = "Currently, Teardown does not have native multiplayer support. It is possible multiplayer will be added in the future."
        embed = interactions.Embed(title="Will there be multiplayer?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'languages':
        response = "Teardown is currently only available in English. We might look into localization at a later stage."
        embed = interactions.Embed(title="Is Teardown available in other languages?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'consolemods':
        response = "Information about mods for consoles will be released soon"
        embed = interactions.Embed(title="Console Mods", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'creativemode':
        response = "To some extent, you are able to save out individual shapes and get them as .vox-files that can be packed to a mod, but you won't be able to modify a level and share that level with your additions."
        embed = interactions.Embed(title="Can I Upload Creative Mode Creations?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'vr':
        response = "Teardown does not support VR."
        embed = interactions.Embed(title="Can you play the game in VR?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'expansions':
        response = "Future expansions are unknown at this time, so keep an eye out for any announcements."
        embed = interactions.Embed(title="Will there be more expansions?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'update':
        response = "Updates are released when they are ready. We do not have a set schedule for updates."
        embed = interactions.Embed(title="When will the next update be released?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'requirements':
        response = "Requires a 64-bit processor and operating system \nThe minimum system requirements are as follows:\n**OS:** Windows 7 \n**Processor:** Quad Core \n**CPU Memory:** 4 GB RAM \n**Graphics:** NVIDIA GeForce GTX 1060 or similar. 3 Gb VRAM.\n**Storage:** 4 GB available space \n**Additional Notes:** Intel integrated graphics cards not supported."
        embed = interactions.Embed(title="What are the minimum system requirements?", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    elif question == 'botinfo':
        response = "**Credits:**\nGGProGaming: creator of this bot\nMicro: for hosting the bot and giving feedback\nfunlennysub: for the original bot\nThomasims: Teardown API scraper script\n\n**Source Code:**\nhttps://github.com/GGProGaming/Teardown-Support-Bot"
        embed = interactions.Embed(title="Bot Info", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True)
    else:
        response = 'Invalid question'
        embed = interactions.Embed(title="FAQ", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True, delete_after=4)

@_faq.autocomplete("question")
async def faq_autocomplete(ctx: AutocompleteContext):
    choices = [
        {"name": "What are the minimum system requirements?", "value": "requirements"},
        {"name": "Will there be multiplayer?", "value": "multiplayer"},
        {"name": "Is Teardown available in other languages?", "value": "languages"},
        {"name": "Will there be a part 3?", "value": "part3"},
        {"name": "Modding Resources", "value": "resources"},
        {"name": "Console Mods", "value": "consolemods"},
        {"name": "Can I Upload Creative Mode Creations?", "value": "creativemode"},
        {"name": "Can you play the game in VR?", "value": "vr"},
        {"name": "Will there be more expansions?", "value": "expansions"},
        {"name": "When will the next update be released?", "value": "update"},
        {"name": "How do I reset my progress?", "value": "progress"},
        {"name": "Bot Info", "value": "botinfo"},
    ]

    matching_choices = [
        choice for choice in choices if ctx.input_text.lower() in choice["name"].lower()
    ]

    await ctx.send(choices=matching_choices)

with open('/root/TTS/teardown_api.json', 'r') as f:
    TEARDOWN_API = json.load(f)

def search_teardown_api(query: str):
    results = []
    for function in TEARDOWN_API['functions']:
        if function['name'].lower() == query.lower():
            results.append(function)
    return results

autocomplete_api = [function['name'] for function in TEARDOWN_API['functions']]

@slash_command(name="docs", description="Search the Teardown API documentation")
@slash_option(
    name="autocomplete",
    description="Enter your search query",
    required=True,
    opt_type=OptionType.STRING,
    autocomplete=True
)
async def _teardowndocs(ctx: SlashContext, autocomplete: str):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Docs"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    results = search_teardown_api(autocomplete)

    if not results:
        response = f'Doc "{autocomplete}" not found.'
        title = f'**{autocomplete}**'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        await ctx.send(embed=embed, delete_after=4, silent=True)
        return

    for result in results:
        title = f'**{result["name"]}**'
        description = result['description']

        # Include the function definition in a code block
        function_def = f'```lua\n{result["name"]}({", ".join([arg["name"] for arg in result["arguments"]])})\n```'
        description += f'\n\n**Function Definition**\n{function_def}'

        if 'arguments' in result:
            arguments = '\n'.join([
              f'- **{arg["name"]}** ({arg["type"]}): {arg["desc"]}'
              for arg in result['arguments']
            ])
            if arguments == '':
              arguments = 'None'
            description += f'\n**Arguments**\n{arguments}'
        # If'ssss
        if 'returns' in result:
            returns = '\n'.join(
              [f'- **{ret["type"]}**: {ret["desc"]}' for ret in result['returns']])
            if returns == '':
              returns = 'None'
            description += f'\n\n**Returns**\n{returns}'

        if 'examples' in result:
            example = f'```lua\n{result["examples"][0]}\n```'
            if example == '':
              example = 'None'
            description += f'\n\n**Example**\n{example}'

        title = f'**{result["name"]}**'
        url = f'https://teardowngame.com/modding/api.html#{result["name"]}'
        embed = interactions.Embed(title=title, url=url, description=description, color=0xbc9946)
        # Set the footer with the API version in small italics
        embed.set_footer(text=f'API Version: {TEARDOWN_API["version"]}')
        await ctx.send(embed=embed, silent=True, delete_after=86400)

@_teardowndocs.autocomplete("autocomplete")
async def docs_autocomplete(ctx: AutocompleteContext):
    matching_api = [api for api in autocomplete_api if ctx.input_text.lower() in api.lower()]

    matching_api = sorted(matching_api)[:25]  # Get the first 25 matching API functions

    choices = [{"name": api, "value": api} for api in matching_api]
    await ctx.send(choices=choices)

# Load the Autumn API from the parsed_functions.json file
with open('/root/TTS/parsed_functions.json', 'r') as f:
    AUTUMN_API = json.load(f)

def search_autumn_api(query: str):
    results = []
    for function in AUTUMN_API['functions']:
        if function['name'].lower() == query.lower():
            results.append(function)
    return results

autocomplete_api2 = [function['name'] for function in AUTUMN_API['functions']]

# This works fine, Autumn needs to fix her docs though because (with every offensive in mind ;) they suck

@slash_command(name="autodocs", description="Search the Automatic framework")
@slash_option(
    name="autocomplete",
    description="Enter your search query",
    required=True,
    opt_type=OptionType.STRING,
    autocomplete=True
)
async def _autodocs(ctx: SlashContext, autocomplete: str):
    results = search_autumn_api(autocomplete)

    if not results:
        response = f'Doc "{autocomplete}" not found.'
        title = f'**{autocomplete}**'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        await ctx.send(embed=embed, delete_after=4, silent=True)
        return

    for result in results:
        title = f'**{result["name"]}**'
        description = f'```{result["description"]}```'

        # Include the function definition in a code block
        function_def = f'```lua\n{result["function_definition"]}\n```'
        description += f'\n\n**Function Definition**\n{function_def}'

        if 'arguments' in result:
            arguments = '\n'.join([
              f'- **{arg["name"]}** ({arg["type"]}): {arg["desc"]}'
              for arg in result['arguments']
            ])
            if arguments == '':
              arguments = 'None'
            description += f'\n**Arguments**\n{arguments}'

        if 'returns' in result:
            returns = '\n'.join(
              [f'- **{ret["name"]}**: {ret["desc"]}' for ret in result['returns']])
            if returns == '':
              returns = 'None'
            description += f'\n\n**Returns**\n{returns}'

        if 'examples' in result and result['examples']:
            example = f'```lua\n{result["examples"][0]}\n```'
            description += f'\n\n**Example**\n{example}'

        title = f'**{result["name"]}**'
        embed = interactions.Embed(title=title, description=description, color=0xbc9946)
        # Set the footer with the API version in small italics
        embed.set_footer(text=f'API Version: {AUTUMN_API["version"]}')
        await ctx.send(embed=embed, silent=True, delete_after=86400)

@_autodocs.autocomplete("autocomplete")
async def autodocs_autocomplete(ctx: AutocompleteContext):
    matching_api2 = [api for api in autocomplete_api2 if ctx.input_text.lower() in api.lower()]

    matching_api2 = sorted(matching_api2)[:25]  # Get the first 25 matching API functions

    choices = [{"name": api, "value": api} for api in matching_api2]
    await ctx.send(choices=choices)

# List of the Teardown tags


# Provided by the Dennispedia site, link is above
TEARDOWN_TAGS = {
  "autobreak":
  "Body tag. Makes body require a smaller inertia to trigger a break event. This is used/set/handled by the engine for the vehicle body.",
  "awake":
  "Body and shape tag. When the level loads, the tagged body will not be asleep. Handled by data/script/awake.lua.",
  "boat":
  "Vehicle tag. Makes the vehicle act like a boat, including looking for and using a propeller location, and not being able to use wheels.",
  "bomb":
  'Shape tag. Will countdown the time until it reaches 0, which then the shape is exploded and removed. The time is in seconds. This is used/set/handled by the engine for bombs and pipebombs.',
  "bombstrength":
  'Shape tag. Used as explosion size by bomb tag. "size" is a number in the range 0.5 to 4. This is used/set/handled by the engine for bombs and pipebombs.',
  "booster":
  'Shape tag. "time" is a number in the range 0 to 10. A time of 10 or greater will cause the tag to be removed. A time of 0 will cause the tag to be ignored. A time less than 0 will be set to 0. A time between 0 and 7 (exclusive) will cause flames and smoke to shoot out from the origin of the shape in the +Z direction. The time will gradually increase at a rate of 1 per second. This is set by the engine for rocket boosters.',
  "breakall":
  'Shape tag. Automatically breaks the other shape that touches this tagged shape. This is used/set by data/script/robot.lua and used/set by the engine if an explosive entity is thrown.',
  "camera":
  'Location tag. Defines where the 3rd person camera is. Defaults to player location.',
  "crane":
  'Vehicle tag. All hinge joints on vehicle are controllable with vehicle_raise/vehicle_lower, and display crane controls. Hook is also controllable.',
  "cranebottom":
  'Vehicle tag. All hinge joints on vehicle are controllable with vehicle_raise/vehicle_lower, and display crane base controls.',
  "cranetop": 'Vehicle tag. Display crane arm controls.',
  "dumptruck":
  'Vehicle tag. All hinge joints on vehicle are controllable with vehicle_raise/vehicle_lower, and display bed controls.',
  "exhaust":
  'Location tag. Defines where/what direction exhaust is emitted from the vehicle. "amount" is a number.',
  "explosive":
  'Body and shape tag. Entity explodes when broken. "size" is a number in the range 0.5 to 4. If applied to an already broken shape, it instantly blows up.',
  "extend":
  'Joint tag. Joint can be controlled by up/down when the player is in a crane vehicle.',
  "forklift":
  'Vehicle tag. All prismatic joints on the vehicle are controllable with vehicle_raise/vehicle_lower, and display forklift controls.',
  "frontloader":
  'Vehicle tag. All hinge joints on the vehicle are controllable with vehicle_raise/vehicle_lower, and display arm controls.',
  "fxbreak":
  'Shape tag. Generate particle effects when the shape is broken. "s" is either "l" for liquid or "g" for gas. "#" is a number in the range 1 to 9 representing time in seconds until effects end. Valid colors for liquids are yellow, black, blue, green, and brown. Valid colors for gases are yellow, blue, and green. Default color is white. This is handled by data/script/fx.lua.',
  "fxflicker":
  'Light tag. Makes the light flicker. "#" is a number in the range 1 to 9 (or 1 if not a number). This is handled by data/script/fx.lua.',
  "fxsmoke":
  'Location tag. When positioned near a shape, makes it spawn in smoke particles. "t" is the type; "p" to make the particles change size, anything else to not. "#" is a number in the range 1 to 9 representing time in seconds until effects end. Valid colors are brown and "subtle" (gray). This is handled by data/script/fx.lua.',
  "hook":
  'Body and shape tag. Shape body acts as a vehicle hook which can be controlled by vehicle_action.',
  "inherittags":
  'Body and shape tag. Takes all the tags from the tagged entity and sets them on its debris. It will recursively do this.',
  "interact":
  'Body and shape tag. Makes it so when the player is close to the tagged entity, a prompt shows up to interact with it. GetPlayerInteractShape/GetPlayerInteractBody only works on entities with this tag.',
  "invisible":
  'Shape tag. Makes the tagged shape invisible, however, still impacts the shadow volume.',
  "level":
  'Joint tag. Force skylift joints to have the same rotation amount. (skylift only?)',
  "map":
  'Body tag. Marks body on the map. Defaults to a blue color. Handled by data/ui/map.lua.',
  "night":
  'Light tag. Light will be turned off if the nightlight environment property is currently false.',
  "nocull":
  'Shape tag. Shape will continue to be rendered no matter how far away it is.',
  "nodrive":
  'Vehicle tag. Vehicle is not drivable to the player with no "Drive" prompt.',
  "nonav": 'Shape tag. Shape is entirely disregarded by pathfinding.',
  "nosnow":
  'Shape tag. Shape does not have any snow on it when the level loads.',
  "passive":
  'Vehicle tag. Disables inputs to the vehicle so it does not drive, steer, or gear change, and leaves only the engine idle sounds.',
  "player":
  'Location tag. Defines where the entry point and first-person camera are for a vehicle.',
  "plank": 'Joint tag. (what does it do?)',
  "propeller": 'Location tag. Defines where the propeller is in a boat.',
  "reversebeep": 'Vehicle tag. Vehicle makes beeping sound when reversing.',
  "skylift":
  'Vehicle tag. All hinge joints on the vehicle are controllable with vehicle_raise/vehicle_lower, and display lift controls.',
  "smoke":
  'Shape tag. Emit smoke from shape. This is used/set/handled by the engine for pipebombs.',
  "tank":
  'Vehicle tag. Display tank controls. Handled by data/script/tank.lua and data/ui/hud.lua.',
  "turbo":
  'Shape tag. Similar to booster, but no smoke, the fire is blue, and it only works if the shape is part of a body that is part of a vehicle. Does nothing when the vehicle is inactive, small flames if the vehicle is idle, and big flames if driving forward. Set by the engine for vehicle boosters.',
  "turn":
  'Joint tag. Force joint to be controlled by left/right when in a crane vehicle.',
  "unbreakable":
  'Body and shape tag. Entity is breakable, but still markable by spray paint or burn marks.',
  "vital":
  'Location tag. When voxels at this position are broken, the vehicle is instantly broken. Defines where engine smoke comes from.',
  "wire": 'Joint tag. (What it do?)'
}

autocomplete_tags = []

for key in TEARDOWN_TAGS:
    autocomplete_tags.append(key)

@slash_command(name="tags", description="Get information about Teardown tags")
@slash_option(
    name="autocomplete",
    description="Enter the name of the tag",
    required=True,
    opt_type=OptionType.STRING,
    autocomplete=True
)
async def _teardowntags(ctx: SlashContext, autocomplete: str):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Tags"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    if autocomplete.lower() in TEARDOWN_TAGS:
        response = TEARDOWN_TAGS[autocomplete.lower()]
        title = f'Tag: {autocomplete}'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        embed.add_field(name="Credit", value="[Dennispedia](https://x4fx77x4f.github.io/dennispedia/teardown/tags.html)")
        await ctx.send(embed=embed, delete_after=14400, silent=True)
    else:
        response = f'Tag "{autocomplete}" not found.'
        title = f'Tag: {autocomplete}'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        await ctx.send(embed=embed, delete_after=4, silent=True)

@_teardowntags.autocomplete("autocomplete")
async def tags_autocomplete(ctx: AutocompleteContext):
    matching_tags = [tag for tag in autocomplete_tags if tag.startswith(ctx.input_text.lower())]

    matching_tags = sorted(matching_tags)[:25]  # Get the first 25 matching tags

    choices = [{"name": tag, "value": tag} for tag in matching_tags]
    await ctx.send(choices=choices)
# Long ass list of every reg key

# Provided by the Dennispedia site, link is above
TEARDOWN_REGISTRY = {
  "game.break":
  'No description',
  "game.break.size":
  'No description',
  "game.break.x":
  'No description',
  "game.break.y":
  'No description',
  "game.break.z":
  'No description',
  "game.brokenvoxels":
  'Number of destroyed voxels. Integer. Small bodies despawning do not count toward this. Breaking off a chunk of something will not consider that chunk destroyed; only actually removing the voxels well cause them to be count.',
  "game.canquickload":
  'No description',
  "game.deploy":
  'Always set to 1. Boolean. If falsy, the main menu and hub computer scripts will try to display additional developer only controls, but the script that contains them (data/ui/debug.lua) has its contents stripped in all known builds—except 0.3.0 (perftest), which doesn\'t use a separate file.',
  "game.disableinput":
  'No description',
  "game.disableinteract":
  'No description',
  "game.disablemap":
  'No description',
  "game.disablepause":
  'No description',
  "game.explosion.strength":
  'No description',
  "game.explosion.x":
  'No description',
  "game.explosion.y":
  'No description',
  "game.explosion.z":
  'No description',
  "game.fire.maxcount":
  'No description',
  "game.fire.spread":
  'No description',
  "game.input.crouch":
  'No description',
  "game.input.curdevice":
  'String. Can be either mouse or gamepad.',
  "game.input.down":
  'No description',
  "game.input.flashlight":
  'No description',
  "game.input.grab":
  'No description',
  "game.input.handbrake":
  'No description',
  "game.input.interact":
  'No description',
  "game.input.jump":
  'No description',
  "game.input.left":
  'No description',
  "game.input.lmb":
  'No description',
  "game.input.locktool":
  'No description',
  "game.input.map":
  'No description',
  "game.input.mmb":
  'No description',
  "game.input.mousex":
  'No description',
  "game.input.mousey":
  'No description',
  "game.input.pause":
  'No description',
  "game.input.right":
  'No description',
  "game.input.rmb":
  'No description',
  "game.input.scroll_down":
  'No description',
  "game.input.scroll_up":
  'No description',
  "game.input.up":
  'No description',
  "game.input.usetool":
  'No description',
  "game.input.vehicle_action":
  'No description',
  "game.input.vehicle_lower":
  'No description',
  "game.input.vehicle_raise":
  'No description',
  "game.largeui":
  'No description',
  "game.levelid":
  'No description',
  "game.levelpath":
  'No description',
  "game.loading.alpha":
  'No description',
  "game.loading.text":
  'No description',
  "game.map.enabled":
  'No description',
  "game.map.fade":
  'No description',
  "game.map.focus":
  'No description',
  "game.mod":
  'No description',
  "game.mod.description":
  'No description',
  "game.mod.title":
  'No description',
  "game.music.volume":
  'No description',
  "game.path":
  'No description',
  "game.path.alpha":
  'No description',
  "game.path.current.x":
  'No description',
  "game.path.current.y":
  'No description',
  "game.path.current.z":
  'No description',
  "game.path.length":
  'No description',
  "game.path.loaded":
  'No description',
  "game.path.pos":
  'No description',
  "game.path.recording":
  'No description',
  "game.paused":
  'No description',
  "game.player.cangrab":
  'No description',
  "game.player.caninteract":
  'No description',
  "game.player.canusetool":
  'No description',
  "game.player.disableinput":
  'No description',
  "game.player.grabbing":
  'No description',
  "game.player.health":
  'No description',
  "game.player.hit":
  'No description',
  "game.player.idling":
  'No description',
  "game.player.interactive":
  'No description',
  "game.player.steroid":
  'No description',
  "game.player.throwing":
  'No description',
  "game.player.tool":
  'No description',
  "game.player.tool.scope":
  'No description',
  "game.player.toolselect":
  'No description',
  "game.player.usescreen":
  'No description',
  "game.player.usevehicle":
  'No description',
  "game.saveerror":
  'No description',
  "game.savegamepath":
  'No description',
  "game.screenshot":
  'No description',
  "game.screenshot.bloom":
  'No description',
  "game.screenshot.dof.max":
  'No description',
  "game.screenshot.dof.min":
  'No description',
  "game.screenshot.dof.scale":
  'No description',
  "game.screenshot.exposure":
  'No description',
  "game.screenshot.tool":
  'No description',
  "game.steam.active":
  'No description',
  "game.steam.hascontroller":
  'No description',
  "game.steamdeck":
  'No description',
  "game.tool":
  'No description',
  "game.vehicle.health":
  'No description',
  "game.vehicle.interactive":
  'No description',
  "game.version":
  'No description',
  "game.version.patch":
  'No description',
  "game.workshop":
  'No description',
  "game.workshop.publish":
  'No description',
  "hud.aimdot":
  'Whether to display the crosshair',
  "hud.disable":
  'No description',
  "hud.hasnotification":
  'No description',
  "hud.notification":
  'No description',
  "level.campaign":
  'No description',
  "level.sandbox":
  'No description',
  "level.spawn":
  'No description',
  "level.unlimitedammo":
  'No description',
  "options.audio.ambiencevolume":
  'Ambience volume as an integer',
  "options.audio.menumusic":
  'Whether to play music on the main menu',
  "options.audio.musicvolume":
  'Volume of music as percentage',
  "options.audio.soundvolume":
  'Volume of audio (excluding music) as percentage',
  "options.display.mode":
  'Windowed mode or fullscreen',
  "options.display.resolution":
  'Resolution preset to use',
  "options.game.campaign.ammo":
  'Amount of ammo to add to all tools as a percentage multiplier',
  "options.game.campaign.health":
  'Amount of health to add to max health as a percentage',
  "options.game.campaign.time":
  'Amount of time in seconds to add to timer after alarm goes off in missions',
  "options.game.missionskipping":
  'Whether the option to skip missions on the terminal and mission fail screens should appear',
  "options.game.sandbox.unlocklevels":
  'Whether all sandbox levels should be available, or only unlocked sandbox levels should be available',
  "options.game.sandbox.unlocktools":
  'Whether all tools should always be available in sandbox, or whether only unlocked tools should be available',
  "options.game.spawn":
  'Whether the spawn menu should always be accessible, or only be accessible in sandbox mode. Integer. 1 is enabled, 0 is disabled.',
  "options.gfx.barrel":
  'Whether barrel distortion should be used. Integer. 1 is enabled, 0 is disabled.',
  "options.gfx.dof":
  'Whether depth of field should be used. Integer. 1 is enabled, 0 is disabled.',
  "options.gfx.fov":
  'Field of view in degrees. Integer. Defaults to 90. Intended range is 60 to 120.',
  "options.gfx.gamma":
  'Gamma correction. Integer. Lower makes the scene darker, higher makes the scene brighter. Defaults to 100. Intended range is 50 to 150.',
  "options.gfx.motionblur":
  'Whether motion blur should be used. Integer. 1 is enabled, 0 is disabled.',
  "options.gfx.quality":
  'Render quality. Integer. High is 1, low is 2, medium is 3.',
  "options.gfx.renderscale":
  'Render scale as a percentage. Integer. Intended values are 100, 75, or 50, but higher values work. Lower values not tested.',
  "options.gfx.vsync":
  'Whether vertical synchronization should be used. Integer. 0 is disabled, 1 is "every frame", 2 is "every other frame". -1 is adaptive.',
  "options.input.headbob":
  'Percentage for how much the camera should tilt in response to player movement, and screen shaking on swing/gunshot. Does not affect shake on explosion. Integer. Defaults to 0. Intended range is 0 to 100.',
  "options.input.invert":
  'Whether to invert vertical look movement. Integer. 1 is enabled, 0 is disabled.',
  "options.input.keymap.backward":
  'No description',
  "options.input.keymap.crouch":
  'No description',
  "options.input.keymap.flashlight":
  'No description',
  "options.input.keymap.forward":
  'No description',
  "options.input.keymap.interact":
  'No description',
  "options.input.keymap.jump":
  'No description',
  "options.input.keymap.left":
  'No description',
  "options.input.keymap.right":
  'No description',
  "options.input.sensitivity":
  'Mouse sensitivity percentage multiplier. Integer. Defaults to 100. Intended range is 25 to 200.',
  "options.input.smoothing":
  'Mouse smoothing percentage. Integer. Defaults to 0. Intended range is 0 to 100.',
  "options.input.toolsway":
  'Whether tool models should sway and move in response to player movement. Integer. 1 is enabled, 0 is disabled.',
  "promo.available":
  'No description',
  "promo.groups":
  'No description',
  "savegame.cash":
  'No description',
  "savegame.challenge":
  'No description',
  "savegame.hint.targetlocation":
  'No description',
  "savegame.hub":
  'No description',
  "savegame.lastcompleted":
  'No description',
  "savegame.legalnoticeshown":
  'No description',
  "savegame.message":
  'No description',
  "savegame.mission":
  'No description',
  "savegame.promoclosed":
  'No description',
  "savegame.promoupdated":
  'No description',
  "savegame.reward":
  'No description',
  "savegame.spawn.shortcut":
  'No description',
  "savegame.startcount":
  'No description',
  "savegame.stats.brokentreadmills":
  'No description',
  "savegame.stats.brokenvoxels":
  'No description',
  "savegame.stats.skeetfullscore":
  'No description',
  "savegame.tool":
  'No description',
  "savegame.valuable":
  'No description',
  "mods.available":
  'No description',
  "mods.pending":
  'No description',
  "mods.publish.id":
  'No description',
  "mods.publish.message":
  'Error message if publishing failed. String.',
  "mods.publish.progress":
  'Number.',
  "mods.publish.state":
  'String. Valid values are uploading, ready, failed, and done.',
  "mods.publish.visibility":
  'Integer. 0 is public, 1 is friends only, 2 is private, and 3 is unlisted. A -1 value is referenced in the code but its purpose is unclear.',
}

# Basically the same as the tags

autocomplete_options = []

for key in TEARDOWN_REGISTRY:
    autocomplete_options.append(key)

@slash_command(name="registry", description="Get information about Teardown registry")
@slash_option(
    name="autocomplete",
    description="Enter the name of the registry",
    required=True,
    opt_type=OptionType.STRING,
    autocomplete=True
)
async def _teardownregistry(ctx: SlashContext, autocomplete: str):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Registry"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    if autocomplete.lower() in TEARDOWN_REGISTRY:
        response = TEARDOWN_REGISTRY[autocomplete.lower()]
        if response == "":
            response = "No description"
        title = f'Registry: {autocomplete}'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        embed.add_field(name="Credit", value="[Dennispedia](https://x4fx77x4f.github.io/dennispedia/teardown/registry.html)")
        await ctx.send(embed=embed, silent=True, delete_after=14400)
    else:
        response = f'Registry entry: "{autocomplete}" not found.'
        title = f'Registry: {autocomplete}'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        await ctx.send(embed=embed, delete_after=4, silent=True)

@_teardownregistry.autocomplete("autocomplete")
async def registry_autocomplete(ctx: AutocompleteContext):
    matching_options = [option for option in autocomplete_options if option.startswith(ctx.input_text.lower())]

    matching_options = sorted(matching_options)[:25]  # Get the first 25 matching options

    choices = [{"name": option, "value": option} for option in matching_options]
    await ctx.send(choices=choices)

# Load custom commands from JSON file
if os.path.exists("/root/TTS/tags.json"):
    with open("/root/TTS/tags.json", "r") as f:
        custom_commands = json.load(f)
else:
    custom_commands = {}

SYSTEM_COMMANDS = ['open', 'read', 'write', 'exec', 'import', 'eval', 'execfile']

def load_bad_words():
    with open('/root/TTS/badwords.txt', 'r') as f:
        return [line.strip().lower() for line in f]

BAD_WORDS = load_bad_words()

async def censor(message, ctx: SlashContext):
    
    # Remove non-word characters
    cleaned_message = re.sub(r'\W+', '', message)

    lower_case_message = cleaned_message.lower()

    # Detect bad words so the bot doesn't get abused the hell out of by Autumn
    bad_words_in_message = [word for word in re.findall(r'\w+', lower_case_message) if word in BAD_WORDS]
    if bad_words_in_message:
        print(f"Detected bad words in message: {bad_words_in_message}")  # print to console
        log_error()
        usage_statistics["Censor"] += 1
        save_usage_statistics(usage_statistics)  # Save the updated statistics
        await ctx.send(f"{ctx.author.mention}, inappropriate language is not allowed.", delete_after=3)
        raise ValueError("Inappropriate language")

    # Detect system commands
    system_commands_in_message = [command for command in SYSTEM_COMMANDS if re.search(fr"\b{command}\b\(.*\)", message.lower())]
    if system_commands_in_message:
        print(f"Detected system commands in message: {system_commands_in_message}")  # print to console
        log_error()
        usage_statistics["Censor"] += 1
        save_usage_statistics(usage_statistics)  # Save the updated statistics
        await ctx.send(f"{ctx.author.mention}, execution of system commands is not allowed.", delete_after=3)
        raise ValueError("Execution of system commands is not allowed")


@slash_command(name="tagz", description="Create, edit, or delete a custom tag")
@slash_option(
    name="action",
    description="Choose an action",
    opt_type=OptionType.STRING,
    required=True,
    choices=[
        {"name": "Create Tag", "value": "create"},
        {"name": "Edit Tag", "value": "edit"},
        {"name": "Delete Tag", "value": "delete"},
    ],
)

@slash_option(name="name", description="The name of the tag", opt_type=OptionType.STRING, required=True)
@slash_option(name="response", description="The response of the tag", opt_type=OptionType.STRING, required=True)
@slash_option(name="private", description="Make the tag private", opt_type=OptionType.BOOLEAN, required=False)
async def custom(ctx: SlashContext, action: str, name: str, response: str, private: bool = False):
    name = name.lower()
    if action == "delete":
        await deletetag(ctx, name)
    elif response:
        if action == "create":
            await createtag(ctx, name, response, private)
        elif action == "edit":
            await edittag(ctx, name, response, private)


@cooldown(Buckets.GUILD, 6, 86400)
async def createtag(ctx: SlashContext, name: str, response: str, private: bool = False):
    try:
        await censor(name, ctx)
        await censor(response, ctx)
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Create Tag"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    global custom_commands
    if not response:
        embed = interactions.Embed(title="Error", description="A response must be provided to create a tag.", color=0xe9254e)
    elif name == "all" or name == "pat":
        embed = interactions.Embed(title="Error", description=f"The name {name} is reserved and cannot be used for a tag.", color=0xe9254e)
    elif name not in custom_commands:
        custom_commands[name] = {"response": response, "creator": ctx.author.id, "private": private}
        with open("./tags.json", "w") as f:
            json.dump(custom_commands, f)
        embed = interactions.Embed(title="Tag Created", description=f"{name} has been created.", color=0xe9254e)
    else:
        embed = interactions.Embed(title="Error", description="This tag already exists.", color=0xe9254e)
    await ctx.send(embed=embed, silent=True, delete_after=4)

@slash_command(name="calltag", description="Call a tag. Use `all` to list all tags.")
@slash_option(name="name", description="The name of the tag", required=True, opt_type=OptionType.STRING)
async def calltag(ctx: SlashContext, name: str):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Call Tag"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    name = name.lower()
    if name == "all":
        public_commands = [
            command_name
            for command_name, command_info in custom_commands.items()
            if not command_info.get("private", False)
            or command_info["creator"] == ctx.author.id
            or has_required_role(ctx.author)
        ]
        command_list = "\n".join(public_commands)
        embed = interactions.Embed(title="List of Tags", description=command_list, color=0xe9254e)
        await ctx.send(embed=embed, silent=True, allowed_mentions=interactions.AllowedMentions.none(), ephemeral=True)
    elif name == "pat":
        await ctx.send("nya", silent=True, delete_after=60)
    elif name in custom_commands:
        response = custom_commands[name]["response"]
        creator_id = custom_commands[name]["creator"]
        creator = await ctx.bot.fetch_user(creator_id)
        is_private = custom_commands[name].get("private", False)

        # Determine if the user can view the private tag
        can_view_private = (creator_id == ctx.author.id) or has_required_role(ctx.author)

        if not is_private or can_view_private:
            # Check for image URL
            image_url = re.search(r"(https?://[^\s]+(?:jpg|jpeg|png|gif))", response)
            if image_url:
                image_url = image_url.group(0)
                response = response.replace(image_url, "").strip()
                embed = interactions.Embed(title=name, description=response, color=0xe9254e)
                embed.set_image(url=image_url)
            else:
                embed = interactions.Embed(title=name, description=response.replace('\\n', '\n'), color=0xe9254e)

            embed.set_footer(text=f"Created by {creator}", icon_url=creator.avatar_url)
            await ctx.send(embed=embed, silent=True, delete_after=None if is_private else 120, ephemeral=is_private)
        else:
            embed = interactions.Embed(title="Error", description="You don't have permission to view this tag.", color=0xe9254e)
            await ctx.send(embed=embed, silent=True, delete_after=4)
    else:
        embed = interactions.Embed(title="Error", description="This tag does not exist.", color=0xe9254e)
        await ctx.send(embed=embed, silent=True, delete_after=4)

async def edittag(ctx: SlashContext, name: str, new_response: str, private: bool = False):
    try:
        await censor(name, ctx)
        await censor(new_response, ctx)
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Edit Tag"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    global custom_commands
    user = ctx.author
    has_role = has_required_role(user)

    if name not in custom_commands:
        embed = interactions.Embed(title="Error", description="This tag does not exist.", color=0xe9254e)
    elif not new_response:
        embed = interactions.Embed(title="Error", description="A response must be provided to edit a tag.", color=0xe9254e)
    elif name == "pat" or name == "all":
        embed = interactions.Embed(title="Error", description="You cannot edit this tag.", color=0xe9254e)
    elif custom_commands[name]["creator"] == user.id or has_role:
        custom_commands[name]["response"] = new_response
        custom_commands[name]["private"] = private
        with open("./tags.json", "w") as f:
            json.dump(custom_commands, f)
        embed = interactions.Embed(title="Tag Edited", description=f"{name} has been updated.", color=0xe9254e)
    else:
        embed = interactions.Embed(title="Error", description="You don't have permission to edit this tag.", color=0xe9254e)
    await ctx.send(embed=embed, silent=True, delete_after=4)

async def deletetag(ctx: SlashContext, name: str):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["Delete Tag"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    global custom_commands
    if name in custom_commands:
        user = ctx.author
        has_role = has_required_role(user)
        if custom_commands[name]["creator"] == user.id or has_role:
            del custom_commands[name]
            with open("/root/TTS/tags.json", "w") as f:
                json.dump(custom_commands, f)
            embed = interactions.Embed(title="Tag Deleted", description=f"{name} has been deleted.", color=0xe9254e)
        else:
            embed = interactions.Embed(title="Error", description="You don't have permission to delete this tag.", color=0xe9254e)
    else:
        embed = interactions.Embed(title="Error", description="This tag does not exist.", color=0xe9254e)
    await ctx.send(embed=embed, silent=True, delete_after=4)

# Constants
USAGE_STATISTICS_FILE = "/root/TTS/usage_statistics.json"

# Load usage statistics from file
def load_usage_statistics():
    try:
        with open(USAGE_STATISTICS_FILE, 'r') as f:
            return collections.defaultdict(int, json.load(f))
    except FileNotFoundError:
        return collections.defaultdict(int)

# Save usage statistics to file
def save_usage_statistics(usage_statistics):
    with open(USAGE_STATISTICS_FILE, 'w') as f:
        json.dump(usage_statistics, f, indent=4)

# Load usage statistics on startup
usage_statistics = load_usage_statistics()

@slash_command(name="usage_analytics",
               description="Collect and display usage statistics",
               dm_permission=False,
               default_member_permissions=13)

async def _usage_analytics(ctx: SlashContext):
    has_role = has_required_role(ctx.author)
    if not has_role:
        await ctx.send("You don't have permission to use this command.", delete_after=4, silent=True)
        return
    else:
        usage_statistics["Analytics"] += 1
        save_usage_statistics(usage_statistics)  # Save the updated statistics
        # Display usage statistics
        response = "```\n"
        for command, count in usage_statistics.items():
            response += f"{command}: {count}\n"
        response += "```"

        embed = interactions.Embed(title="Usage Analytics", description=response, color=0xe9254e)
        await ctx.send(embed=embed, silent=True, delete_after=210)

STEAM_API_KEY = "GAH FORGOT TO REMOVE"
WORKSHOP_API_URL = "https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/"

async def fetch_mods_based_on_url(workshop_url: str):
    # Extract workshop item id from url... IF IT BLOODY WORKED GAHHHHHHHHHHHHHHH
    workshop_id = workshop_url.split('id=')[1]

    # Initialize a ClientSession
    async with aiohttp.ClientSession() as session:
        params = {
            "key": STEAM_API_KEY,
            "publishedfileids": [workshop_id]
        }

        # Send the request
        async with session.get(WORKSHOP_API_URL, params=params) as response:
            # Parse the response JSON
            data = await response.text()
            data = json.loads(data)

            # Extract the mod data
            published_file_details = data.get("publishedfiledetails", [])

            # Check if the list is not empty before accessing its elements
            if published_file_details:
                mod = published_file_details[0]
                return mod
            else:
                print(f"No mods found for the workshop URL: {workshop_url}")
                return None

    
async def get_all_mods():
    # Initialize a ClientSession
    async with aiohttp.ClientSession() as session:
        mods = {}
        cursor = ""  # Initializing to an empty string instead of None
        while True:
            # Set up the parameters for the API request
            params = {
                "key": STEAM_API_KEY,
                "query_type": 1,
                "return_metadata": 1,
                "appid": 1167630,
                "page": 1,
                "cursor": cursor,
            }

            # Print the params to debug
            print(f"Sending request with params: {params}")

            # Send the request
            async with session.get(WORKSHOP_API_URL, params=params) as response:
                # Parse the response JSON
                data = await response.text()
                data = json.loads(data)

                # Extract the mod data and map it to a dictionary
                mods.update({mod["publishedfileid"]: mod for mod in data.get("publishedfiledetails", [])})

                # Get the next cursor
                cursor = data.get('next_cursor', '')  # Providing a default value of ''

                if cursor == '':
                    break

        return mods
# FRICK YOU STEAM. WHY DOES YOU DOCUMENTATION SUCK ASS
async def find_similar_mods(workshop_url: str):
    # Fetch the details of the mod from the workshop url
    target_mod = await fetch_mods_based_on_url(workshop_url)

    # Get the list of mods from the Steam workshop 
    mods = await get_all_mods()

    # Find similar mods
    similar_mods = []
    for mod_id, mod in mods.items():
        match_counter = 0

        # Compare title, description, file size
        if mod["title"] == target_mod["title"]:
            match_counter += 1
        if mod.get("description") == target_mod.get("description"):
            match_counter += 1
        if mod["file_size"] == target_mod["file_size"]:
            match_counter += 1

        # If 2 out of 3 attributes match, it's considered similar
        if match_counter >= 2:
            similar_mods.append(mod)

    return similar_mods

@slash_command(name="find-similar-mods", description="Find mods similar to the given mod in the Steam workshop")
@slash_option(name="workshop_url", description="The Steam workshop URL of the mod", required=True, opt_type=OptionType.STRING)
async def find_similar_mods_command(ctx: SlashContext, workshop_url: str):
    # Find similar mods
    similar_mods = await find_similar_mods(workshop_url)

    # Handle the situation when no mods were found for the given workshop URL
    if similar_mods is None:
        await ctx.send(f"No mods found for the workshop URL: {workshop_url}")
        return

    # Send a message with links to the original and similar mods
    if similar_mods:
        embed = interactions(title="Similar mods found", color=0xe9254e)
        for mod in similar_mods:
            embed.add_field(name=f"Title: {mod['title']}", value=f"[Go to mod]({mod['url']})")
        await ctx.send(embed=embed)
    else:
        await ctx.send("No similar mods found.")

@slash_command(name="system", description="Collect and display system usage statistics")
async def _system_stats(ctx: SlashContext):
    try:
        await check_mute(ctx)
    except ValueError:
        return
    usage_statistics["system"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    message = await ctx.send("Collecting data...", delete_after=75)
    start_time = asyncio.get_running_loop().time()

    # Initialize time and cpu usage lists
    time_data = []
    # define cpu_data as an empty numpy array
    cpu_data = np.array([])

    while True:
        # Break the loop after 60 seconds
        if asyncio.get_running_loop().time() - start_time > 60:
            break

        # Retrieve system statistics
        cpu_usage = await run_command('top -b -n1 | grep "Cpu(s)" | awk \'{print $2 + $4}\'')
        memory_usage = await run_command('free -m | awk \'NR==2{printf "Memory Usage: %.2f%%", $3*100/$2 }\'')
        top_process = await run_command('ps aux --sort=-%mem | head -2 | tail -1 | awk \'{print $11}\'')
        ping_time = await run_command('ping -c 1 google.com | tail -1| awk \'{print $4}\' | cut -d \'/\' -f 2')

        # Accumulate time and cpu usage data
        elapsed_time = asyncio.get_running_loop().time() - start_time
        time_data.append(elapsed_time)

        # check if cpu_usage is not None and can be converted to a float
        if cpu_usage is not None:
            try:
                cpu_data = np.concatenate((cpu_data, np.array([float(cpu_usage)])))
            except ValueError:
                pass

        # Convert the cpu_data list to a numpy array for easier manipulation
        cpu_data = np.array(cpu_data)

        # Get the top 5 memory consuming processes and their respective memory usage in percentage
        mem_processes = await run_command('ps aux --sort=-%mem | awk \'{print $11, $4}\' | head -6')

        # Split the result into process names and memory usage
        if mem_processes is not None:
            mem_processes = mem_processes.split("\n")[1:]  # Ignore the first line which is the command itself
            mem_processes = [p.split() for p in mem_processes]
            mem_names = [p[0] for p in mem_processes]
            mem_usage = [float(p[1]) for p in mem_processes]
        else:
            mem_names = []
            mem_usage = []

        # Generate graph
        fig, axs = plt.subplots(1, 2, figsize=(12, 6))  # Create a figure with 1 row and 2 columns

        # Draw the CPU usage line chart
        axs[0].plot(time_data, cpu_data)
        axs[0].set_title("CPU Usage Over Time")
        axs[0].set_xlabel("Elapsed Time (seconds)")
        axs[0].set_ylabel("CPU Usage (%)")
        axs[0].set_ylim(0, 100)

        # Draw the memory usage pie chart
        axs[1].pie(mem_usage, labels=mem_names, autopct='%1.1f%%')
        axs[1].set_title("Memory Usage by Process")

        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Upload the image
        file = interactions.File(buf, "graph.png")

        # Embed the image in the message
        response = f"CPU Usage: {cpu_usage}%\n{memory_usage}\nMost consuming process: {top_process}\nPing time: {ping_time} ms"
        embed = interactions.Embed(title="System Stats", description=response, color=0xe9254e)
        embed.set_image(url="attachment://graph.png")

        # Edit the message with the new embed
        await message.edit(content=None, embed=embed, file=file)

        # Clear the current figure
        plt.clf()

        # Delete the BytesIO object
        buf.close()

        # Wait before the next update
        await asyncio.sleep(5)

async def run_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if stdout:
        return stdout.decode().strip()
    if stderr:
        return stderr.decode().strip()

# Set up the prefixed commands extension
#prefixed_commands.setup(bot, default_prefix="!")

@prefixed_command(name="typst")
async def render_prefixed(ctx:PrefixedContext, *, typst_code: str):
    try:
        await censor(typst_code, ctx)
        await check_mute(ctx)
    except ValueError:
        return
    try:
        # Check if typst_code is provided within a codeblock
        if not (typst_code.startswith("```") and typst_code.endswith("```")):
            # Check if a file named message.txt is attached
            if ctx.message.attachments and ctx.message.attachments[0].filename == "message.txt":
                async with aiohttp.ClientSession() as session:
                    async with session.get(ctx.message.attachments[0].url) as resp:
                        typst_code = await resp.text()
            else:
                await ctx.reply(f"Please provide the Typst code within a codeblock or as an attached file named message.txt.")
                return
        else:
            # Remove the backticks from the typst_code
            typst_code = typst_code[3:-3]

        simple_conversion = True
        #Append the desired setting to the beginning of the typst code if it's not already there
        if '#set page' not in typst_code:
            typst_code = f'#set page(width: auto, height: auto, margin: (x: 4pt, y: 4pt));' + typst_code

        with tempfile.NamedTemporaryFile(suffix=".typ", delete=False) as temp:
            temp.write(typst_code.encode())
            temp_path = temp.name

        compiler = typst.Compiler(".")
        pdf_bytes = compiler.compile(temp_path, output=None)  # compiles the Typst code to a PDF in memory

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        # Convert Pages One by One and Send:
        for count, img in convert_pages_to_images(temp_pdf_path, simple_conversion):
            img_bytes = io.BytesIO()
            img.save(img_bytes, 'PNG')
            img_bytes.seek(0)
            await ctx.reply(file=interactions.File(img_bytes, f'out{count}.png'))

        # Cleanup: Delete the temporary files
        os.remove(temp_path)
        os.remove(temp_pdf_path)

    except Exception as e:
        log_error()
        embed = interactions.Embed(title="Error", description=f"Sorry, but that couldn't be processed... Here is the error: {str(e)}", color=0xFF0000)
        await ctx.reply(embed=embed, delete_after=20)

@slash_command(name="typst", description="Typst stuff")
@slash_option(name="typst_code", description="A typst code string", required=True, opt_type=OptionType.STRING)
@slash_option(name="page_width", description="Width of the page", required=False, opt_type=OptionType.STRING)
@slash_option(name="page_height", description="Height of the page", required=False, opt_type=OptionType.STRING)
@slash_option(name="simple_conversion", description="Bypass rendering and simply convert PDF to image", required=False, opt_type=OptionType.BOOLEAN)
async def render(ctx: SlashContext, *, typst_code: str, page_width: str='auto', page_height: str='auto', simple_conversion: bool=False):
    try:
        await censor(typst_code, ctx)
        await censor(page_width, ctx)
        await censor(page_height, ctx)
        await check_mute(ctx)
    except ValueError:
        return
    try:
        # Append the desired setting to the beginning of the typst code
        if '#set page' not in typst_code:
            typst_code = f'#set page(width: {page_width}, height: {page_height}, margin: (x: 4pt, y: 4pt));' + typst_code

        with tempfile.NamedTemporaryFile(suffix=".typ", delete=False) as temp:
            temp.write(typst_code.encode())
            temp_path = temp.name

        compiler = typst.Compiler(".")
        pdf_bytes = compiler.compile(temp_path, output=None)  # compiles the Typst code to a PDF in memory

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        # Convert Pages One by One and Send:
        for count, img in convert_pages_to_images(temp_pdf_path, simple_conversion):
            img_bytes = io.BytesIO()
            img.save(img_bytes, 'PNG')
            img_bytes.seek(0)
            await ctx.send(file=interactions.File(img_bytes, f'out{count}.png'))

        # Cleanup: Delete the temporary files
        os.remove(temp_path)
        os.remove(temp_pdf_path)
            
    except Exception as e:
        log_error()
        embed = interactions.Embed(title="Error", description=f"Sorry, but that couldn't be processed... Here is the error: {str(e)}", color=0xFF0000)
        await ctx.send(embed=embed, delete_after=20)

def convert_pages_to_images(pdf_path: str, simple_conversion: bool) -> Generator:
    usage_statistics["typst"] += 1
    save_usage_statistics(usage_statistics)  # Save the updated statistics
    #Converts each page of the PDF to an image one by one.
    with open(pdf_path, "rb") as pdf_file:
        reader = PdfReader(pdf_file)

        for count, page in enumerate(reader.pages, start=1):
            image_page = convert_from_path(pdf_path, dpi=400, first_page=count, last_page=count)[0]  # converts the PDF to images

            if simple_conversion:
                img = image_page  # simply use the original page image
            else:
                img = process_image(image_page)  # apply the image processing steps
            
            yield count, img

def process_image(page):
    try:
        # Resize to larger for better antialiasing
        img = page.resize((page.width*2, page.height*2), Image.LANCZOS).convert("RGBA")
        # Create border
        border_size = 18 # assuming 1pt = 1px
        border = Image.new('RGBA', (img.width + 2 * border_size, img.height + 2 * border_size), "#9ca7b1")
        border = add_gradient(border)

        # Create content with solid color and rounded corners
        content = Image.new('RGBA', (img.width, img.height), "#1f1f1f")
        rounded_content = round_corners(content)

        # Apply rounded corners to the image directly
        img = round_corners(img, radius=60) # Increase radius parameter

        # Extract text from rounded image
        text_img = img.copy()
        text_data = text_img.load()
        width, height = text_img.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = text_data[x, y]
                if r < 128 or g < 128 or b < 128: # assuming the text is darker than the background
                    text_data[x, y] = (255, 255, 255, a) # change text color to white
                else:
                    text_data[x, y] = (0, 0, 0, 0) # make background transparent

        # Merge rounded content and text image
        content_text = Image.alpha_composite(rounded_content, text_img)

        # Merge border and content_text
        border.paste(content_text, (border_size, border_size))

        # Resize back to original size with LANZCOS
        border = border.resize((page.width, page.height), Image.LANCZOS)

        return border

    except Exception as e:
        log_error()

def add_gradient(image):
    top = random.randint(0, 255)
    bottom = top + 5
    draw = ImageDraw.Draw(image)
    for i, color in enumerate(range(top, bottom)):
        draw.line([(i, 0), (i, image.height)], tuple([color]*3), width=1)
    return image

def round_corners(image, radius=30):
    # Create a mask with white rounded corners
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, image.width, image.height), radius, fill=255)

    # Apply the mask to the image
    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)

    return output
    
def log_error():
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    log_file_path = f"/root/TTS/logs/{date_string}.txt"

    # create the logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info(f"Logging started at {now.strftime('%H:%M:%S')}")

    try:
        pass
    except Exception as e:
        logging.error(str(e) + "\n")

    logging.info(f"Logging ended at {datetime.now().strftime('%H:%M:%S')}")

bot.load_extension("game")

# I ain't giving you the bot's token... You crazy??

bot.start(
  "YOUR_TOKEN_HERE")
