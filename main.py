"""
CREDITS:

-GGProGaming: creator of this bot
-Micro: for hosting the bot and giving feedback
-funlennysub: for the original bot
-Thomasims: Teardown API scraper script

-Source Code: https://github.com/GGProGaming/Teardown-Support-Bot
"""
import interactions
from interactions import Client, slash_command, SlashCommandOption, SlashCommandChoice, SlashContext, Intents, EmbedAttachment, cooldown, Buckets, subcommand, slash_option, OptionType, AutocompleteContext, EmbedAttachment, Task, IntervalTrigger, listen, Member
from interactions.client.errors import CommandOnCooldown
from interactions.ext import prefixed_commands
import json
import os
import re
import collections
import aiohttp
import asyncio
import difflib
import time
import requests

bot = Client(intents=Intents.DEFAULT, sync_interactions=True, asyncio_debug=True)
prefixed_commands.setup(bot)

# Tech Support Slash Command
@slash_command(name="techsupport",
               description="Get answers to basic tech support questions",
               options=[
                   SlashCommandOption(name="question",
                                      description="Enter your question",
                                      type=3,
                                      required=True)
               ])
async def _techsupport(ctx: SlashContext, question: str):
  usage_statistics["Tech Support"] += 1
  image = None
  if question == 'drivers':
    response = (
      '1. For Nvidia Users:\nYou can update drivers via Geforce Experience or their [driver page](https://www.nvidia.com/download/index.aspx).\n'
      '2. For AMD Users:\nYou can check for updates using the AMD Radeon Settings or by navigating to their [driver page](https://www.amd.com/en/support).\n'
      '3. After updating drivers, search for "Windows Update" in the Start menu and install any available updates.\n'
      '4. Once updates are installed, restart your computer.')
  elif question == 'verify':
    response = ('1. Open the Steam client.\n'
                '2. Navigate to your Library.\n'
                '3. Right-click on Teardown and select "Properties".\n'
                '4. Click on the "Local Files" tab.\n'
                '5. Click "Verify Integrity of Game Files".')
    image_url = 'https://media.discordapp.net/attachments/1070933425005002812/1102841814676951060/Screenshot_1.png'
    image = EmbedAttachment(url=image_url)
  elif question == 'appdata':
    response = (
      '1. Press the Windows key + R to open the Run dialog. Or open file explorer and select the top search bar.\n'
      '2. Type %localappdata% and press Enter.\n'
      '3. Navigate to the "Teardown" folder.')
  elif question == 'cpu_gpu':
    response = (
      '1. Press the Windows key type in "Task Manager" or enter the shortcut, "ctrl+shift+esc"\n'
      '2. Go to the Performance tab and look for CPU and GPU sections.\n'
      '3. You can see the name, usage, speed, and temperature of your CPU and GPU.\n'
      '4. Relevant information the support team will need is the name of the CPU and GPU.'
    )
  elif question == 'ddu':
    response = (
      '1. Download Display Driver Uninstaller (DDU) from the official website: https://www.wagnardsoft.com/.\n'
      '2. Boot your computer into Safe Mode.\n'
      '3. Run DDU and select your GPU manufacturer from the drop-down menu.\n'
      '4. Click "Clean and restart".\n'
      '5. After restarting, download and install the latest GPU drivers from the manufacturer\'s website.'
    )
  elif question == 'artifacts':
      response = (
          '1. Update your graphics card drivers to the latest version.\n'
          '2. Disable any overlays such as the Razer Overlay.\n'
      )
      image_url = 'https://media.discordapp.net/attachments/1069850310782234635/1069850311235207258/image.png?width=1562&height=905'
      image = EmbedAttachment(url=image_url)
  elif question == "nosound":
      response = (
          'When starting Teardown, avoid alt-tabbing or unfocusing the window while it starts.'
      )
  else:
        response = 'Invalid question'
        embed = interactions.Embed(title="Tech Support", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True, delete_after=4)
  embed = interactions.Embed(title="Tech Support", description=response, color=0x41bfff)
  if image:
      embed.image = image
  await ctx.send(embed=embed, silent=True)

@_techsupport.autocomplete("question")
async def techsupport_autocomplete(ctx: AutocompleteContext):
    choices = [
        {"name": "Update drivers and Windows and reboot", "value": "drivers"},
        {"name": "Verify Steam files", "value": "verify"},
        {"name": "Find AppData local files", "value": "appdata"},
        {"name": "Find CPU and GPU information", "value": "cpu_gpu"},
        {"name": "Perform DDU process", "value": "ddu"},
        {"name": "Artifacts", "value": "artifacts"},
        {"name": "No Sound", "value": "nosound"},
    ]

    matching_choices = [
        choice for choice in choices if ctx.input_text.lower() in choice["name"].lower()
    ]

    await ctx.send(choices=matching_choices)

# FAQ Slash Command
@slash_command(name="faq",
               description="Get answers to frequently asked questions",
               options=[
                   SlashCommandOption(name="question",
                                      description="Enter your question",
                                      type=3,
                                      required=True)
               ])
async def _faq(ctx: SlashContext, question: str):
    usage_statistics["FAQ"] += 1
    if question == 'progress':
        response = "You can reset your game progress by going to options in the main menu, clicking the game button, and then clicking reset progress."
    elif question == 'resources':
        response = (
            '1. The official Teardown modding documentation can be found [here](https://teardowngame.com/modding/index.html).\n'
            '2. The official Teardown modding API documentation can be found [here](https://teardowngame.com/modding/api.html).\n'
            '3. The offical voxtool... tool can be found [here](https://teardowngame.com/voxtool/).\n'
            '4. There are many tutorials and guides found here: https://discord.com/channels/760105076755922996/771750716456697886.\n'
            '5. You can find the magicavoxel application [here](https://ephtracy.github.io/).\n'
            '6. You can ask questions in https://discord.com/channels/760105076755922996/768940642767208468.\n'
        )
    elif question == 'part3':
        response = "There will not be a Part 3. Teardown is a complete game and will not be receiving any more main campaign updates."
    elif question == 'multiplayer':
        response = "Currently, Teardown does not have native multiplayer support. It is possible multiplayer will be added in the future."
    elif question == 'languages':
        response = "Teardown is currently only available in English. We might look into localization at a later stage."
    elif question == 'vr':
        response = "Teardown does not support VR."
    elif question == 'expansions':
        response = "Future expansions are unknown at this time, so keep an eye out for any announcements."
    elif question == 'update':
        response = "Updates are released when they are ready. We do not have a set schedule for updates."
    elif question == 'requirements':
        response = "Requires a 64-bit processor and operating system \nThe minimum system requirements are as follows:\n**OS:** Windows 7 \n**Processor:** Quad Core \n**CPU Memory:** 4 GB RAM \n**Graphics:** NVIDIA GeForce GTX 1060 or similar. 3 Gb VRAM.\n**Storage:** 4 GB available space \n**Additional Notes:** Intel integrated graphics cards not supported."
    elif question == 'botinfo':
        response = "**Credits:**\nGGProGaming: creator of this bot\nMicro: for hosting the bot and giving feedback\nfunlennysub: for the original bot\nThomasims: Teardown API scraper script\n\n**Source Code:**\nhttps://github.com/GGProGaming/Teardown-Support-Bot"
    else:
        response = 'Invalid question'
        embed = interactions.Embed(title="FAQ", description=response, color=0x41bfff)
        await ctx.send(embed=embed, silent=True, delete_after=4)

    embed = interactions.Embed(title="FAQ", description=response, color=0x41bfff)
    await ctx.send(embed=embed, silent=True)

@_faq.autocomplete("question")
async def faq_autocomplete(ctx: AutocompleteContext):
    choices = [
        {"name": "How do I reset my progress?", "value": "progress"},
        {"name": "Modding Resources", "value": "resources"},
        {"name": "Will there be a part 3?", "value": "part3"},
        {"name": "Will there be multiplayer?", "value": "multiplayer"},
        {"name": "Is Teardown available in other languages?", "value": "languages"},
        {"name": "Can you play the game in VR?", "value": "vr"},
        {"name": "Will there be more expansions?", "value": "expansions"},
        {"name": "When will the next update be released?", "value": "update"},
        {"name": "What are the minimum system requirements?", "value": "requirements"},
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
    usage_statistics["Docs"] += 1
    results = search_teardown_api(autocomplete)

    if not results:
        await ctx.send(f'No results found for "{autocomplete}"', delete_after=4, silent=True)
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
        await ctx.send(embed=embed, silent=True, delete_after=300)

@_teardowndocs.autocomplete("autocomplete")
async def docs_autocomplete(ctx: AutocompleteContext):
    matching_api = [api for api in autocomplete_api if ctx.input_text.lower() in api.lower()]

    matching_api = sorted(matching_api)[:25]  # Get the first 25 matching API functions

    choices = [{"name": api, "value": api} for api in matching_api]
    await ctx.send(choices=choices)

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
    usage_statistics["Tags"] += 1
    if autocomplete.lower() in TEARDOWN_TAGS:
        response = TEARDOWN_TAGS[autocomplete.lower()]
        title = f'Tag: {autocomplete}'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        embed.add_field(name="Credit", value="[Dennispedia](https://x4fx77x4f.github.io/dennispedia/teardown/tags.html)")
        await ctx.send(embed=embed, delete_after=210, silent=True)
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
    usage_statistics["Registry"] += 1
    if autocomplete.lower() in TEARDOWN_REGISTRY:
        response = TEARDOWN_REGISTRY[autocomplete.lower()]
        if response == "":
            response = "No description"
        title = f'Registry: {autocomplete}'
        embed = interactions.Embed(title=title, description=response, color=0xbc9946)
        embed.add_field(name="Credit", value="[Dennispedia](https://x4fx77x4f.github.io/dennispedia/teardown/registry.html)")
        await ctx.send(embed=embed, silent=True, delete_after=210)
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
    usage_statistics["Create Tag"] += 1
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
    usage_statistics["Call Tag"] += 1
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
        await ctx.send(embed=embed, silent=True, delete_after=30, allowed_mentions=interactions.AllowedMentions.none(), ephemeral=True)
    elif name == "pat":
        await ctx.send("nya", silent=True)
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
            await ctx.send(embed=embed, silent=True, delete_after=210, ephemeral=is_private)
        else:
            embed = interactions.Embed(title="Error", description="You don't have permission to view this tag.", color=0xe9254e)
            await ctx.send(embed=embed, silent=True, delete_after=4)
    else:
        embed = interactions.Embed(title="Error", description="This tag does not exist.", color=0xe9254e)
        await ctx.send(embed=embed, silent=True, delete_after=4)

async def edittag(ctx: SlashContext, name: str, new_response: str, private: bool = False):
    usage_statistics["Edit Tag"] += 1
    global custom_commands
    if name not in custom_commands:
        embed = interactions.Embed(title="Error", description="This tag does not exist.", color=0xe9254e)
    elif not new_response:
        embed = interactions.Embed(title="Error", description="A response must be provided to edit a tag.", color=0xe9254e)
    if custom_commands[name]["creator"] == ctx.author.id or has_required_role(ctx.author):
        custom_commands[name]["response"] = new_response
        custom_commands[name]["private"] = private
        with open("./tags.json", "w") as f:
            json.dump(custom_commands, f)
        embed = interactions.Embed(title="Tag Edited", description=f"{name} has been updated.", color=0xe9254e)
    else:
        embed = interactions.Embed(title="Error", description="You don't have permission to edit this tag.", color=0xe9254e)
    await ctx.send(embed=embed, silent=True, delete_after=4)

# List of roles that can delete tags
required_roles = ["Moderator", "Admin"]

# Helper function to check if the user has required roles
def has_required_role(member):
    if isinstance(member, Member):
        return any(role.name in required_roles for role in member.roles)
    else:
        return False

async def deletetag(ctx: SlashContext, name: str):
    usage_statistics["Delete Tag"] += 1
    global custom_commands
    if name in custom_commands:
        user = ctx.author
        has_role = has_required_role(ctx.author)
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
      # Increment the usage counter for this command
      usage_statistics["Analytics"] += 1

      # Display usage statistics
      response = "```\n"
      for command, count in usage_statistics.items():
          response += f"{command}: {count}\n"
      response += "```"

      # Save the updated usage_statistics after using the command
      save_usage_statistics(usage_statistics)

      embed = interactions.Embed(title="Usage Analytics", description=response, color=0xe9254e)
      await ctx.send(embed=embed, silent=True, delete_after=210)
"""
My poor attempt at finding duplicate workshop items. Need help!

STEAM_API_KEY = "STEAM_API_KEY"

async def fetch_workshop_items():
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    data = {
        "key": "F15539D3EE060289D56DC3B3A70248A6",
        "publishedfileids[0]": "1167630",
        "itemcount": 1,
    }
    response = requests.post(url, data=data)

    if response.status_code == 200:
        workshop_items = response.json()["response"]["publishedfiledetails"]
        return workshop_items
    else:
        return None

async def get_duplicate_items(ctx: SlashContext):
    if not has_required_role(ctx.author):
        await ctx.send("You don't have permission to use this command.", silent=True)
        return

    workshop_items = await fetch_workshop_items()

    if workshop_items:
        duplicates = find_duplicates(workshop_items)

        if duplicates:
            message = "Duplicate Workshop Items:\n\n"
            for original, duplicate in duplicates:
                message += f"Original: {original['title']} ({original['file_size']} bytes) - [Link](https://steamcommunity.com/sharedfiles/filedetails/?id={original['publishedfileid']})\n"
                message += f"Duplicate: {duplicate['title']} ({duplicate['file_size']} bytes) - [Link](https://steamcommunity.com/sharedfiles/filedetails/?id={duplicate['publishedfileid']})\n\n"

            await ctx.send(message, silent=True)
        else:
            await ctx.send("No duplicate items found.", silent=True)
    else:
        await ctx.send("Failed to fetch workshop items.", silent=True)

@slash_command(name="findduplicates", description="Find duplicate items in the Teardown workshop")
async def find_duplicates(ctx: SlashContext):
    user = ctx.author
    has_role = has_required_role(ctx.author)
    if has_role:
        workshop_items = await fetch_workshop_items()
        if workshop_items:
            published_file_ids = [item["publishedfileid"] for item in workshop_items]
            item_details = await fetch_workshop_items(published_file_ids)
            duplicate_items = get_duplicate_items(item_details)

            if duplicate_items:
                message = "Found duplicate items:\n"
                for original, duplicate in duplicate_items:
                    message += f'Original: {original["title"]} ({original["file_size"]} bytes) - [Link](https://steamcommunity.com/sharedfiles/filedetails/?id={original["publishedfileid"]})\n'
                    message += f'Duplicate: {duplicate["title"]} ({duplicate["file_size"]} bytes) - [Link](https://steamcommunity.com/sharedfiles/filedetails/?id={duplicate["publishedfileid"]})\n\n'
                await ctx.send(message, silent=True)
            else:
                await ctx.send("No duplicate items found.", silent=True)
        else:
            await ctx.send("Failed to fetch workshop items.", silent=True)

def compare_items(item1, item2, size_threshold=10240, name_similarity=0.8):
    name1 = item1["title"].lower()
    name2 = item2["title"].lower()
    size1 = int(item1["file_size"])
    size2 = int(item2["file_size"])

    # Compare the names using a sequence matcher
    similarity = difflib.SequenceMatcher(None, name1, name2).ratio()

    # Check if the names are similar and the sizes are within the threshold
    if similarity >= name_similarity and abs(size1 - size2) <= size_threshold:
        return True
    return False
"""
# Replace "YOUR_BOT_TOKEN" with the actual token for your bot
bot.start(
  "TOKEN")
