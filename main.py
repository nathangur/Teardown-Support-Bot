from discord.ext import commands
import discord
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.model import SlashCommandOptionType
import json

bot = commands.Bot(command_prefix="/")
slash = SlashCommand(bot, sync_commands=True)


@slash.slash(name="TechSupport",
             description="Get answers to basic tech support questions",
             options=[
               create_option(name="question",
                             description="Select a question",
                             option_type=3,
                             required=True,
                             choices=[{
                               "name": "Update drivers and Windows and reboot",
                               "value": "update"
                             }, {
                               "name": "Verify Steam files",
                               "value": "verify"
                             }, {
                               "name": "Find AppData local files",
                               "value": "appdata"
                             }, {
                               "name": "Find CPU and GPU information",
                               "value": "cpu_gpu"
                             }, {
                               "name": "Perform DDU process",
                               "value": "ddu"
                             }, {
                               "name": "No Sound",
                               "value": "nosound"
                             }, {
                               "name": "Modding Resources",
                               "value": "resources"
                             }, {
                               "name": "Artifacts",
                               "value": "artifacts"
                             }])
             ])
async def _TechSupport(ctx: SlashContext, question: str):
  if question == 'update':
    response = (
      '1. For Nvidia Users:\nYou can update drivers via Geforce Experience or their driver page found here: https://www.nvidia.com/download/index.aspx.\n'
      '2. For AMD Users:\nYou can check for updates using the AMD Radeon Settings or by navigating to their driver page found here: https://www.amd.com/en/support.\n'
      '3. After updating drivers, search for "Windows Update" in the Start menu and install any available updates.\n'
      '4. Once updates are installed, restart your computer.')
  elif question == 'verify':
    response = ('1. Open the Steam client.\n'
                '2. Navigate to your Library.\n'
                '3. Right-click on Teardown and select "Properties".\n'
                '4. Click on the "Local Files" tab.\n'
                '5. Click "Verify Integrity of Game Files".')
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
  elif question == 'resources':
    response = (
        '1. The official Teardown modding documentation can be found here: https://teardowngame.com/modding.html.\n'
        '2. There are many tutorials and guides found here: https://discord.com/channels/760105076755922996/771750716456697886.\n'
        '3. You can ask questions in https://discord.com/channels/760105076755922996/768940642767208468.\n'
    )
  elif question == 'artifacts':
    response = (
        '1. Update your graphics card drivers to the latest version.\n'
        '2. Disable any overlays such as the Razer Overlay.\n'
    )
    image_url = 'https://media.discordapp.net/attachments/1069850310782234635/1069850311235207258/image.png?width=1562&height=905'
    response += f'[Example artifact from overlay]({image_url})'
  elif question == "nosound":
    response = (
      'When starting Teardown, avoid alt-tabbing or unfocusing the window while it starts.'
    )
  else:
    response = 'Invalid question'

  embed = discord.Embed(title="Tech Support", description=response)
  await ctx.send(embed=embed)


with open('TTS/teardown_api.json', 'r') as f:
  TEARDOWN_API = json.load(f)

def search_teardown_api(query: str):
  results = []
  for category in TEARDOWN_API['api']:
    for function in category['functions']:
      if function['name'].lower() == query.lower():
        results.append(function)
  return results


@slash.slash(name="Docs",
             description="Search the Teardown API documentation",
             options=[
               create_option(name="query",
                             description="Enter your search query",
                             option_type=3,
                             required=True)
             ])
async def _teardowndocs(ctx: SlashContext, query: str):
  await ctx.defer()
  results = search_teardown_api(query)

  if not results:
    await ctx.send(f'No results found for "{query}"')
    return

  for result in results:
    title = f'**{result["name"]}**'
    description = result['info']

    # Include the function definition in a code block
    function_def = f'```lua\n{result["def"]}\n```'
    description += f'\n\n**Function Definition**\n{function_def}'

    if 'arguments' in result:
      arguments = '\n'.join([
        f'- **{arg["name"]}** ({arg["type"]}): {arg["desc"]}'
        for arg in result['arguments']
      ])
      description += f'\n**Arguments**\n{arguments}'

    if 'return' in result:
      returns = '\n'.join(
        [f'- **{ret["type"]}**: {ret["desc"]}' for ret in result['return']])
      description += f'\n\n**Returns**\n{returns}'

    if 'example' in result:
      example = f'```lua\n{result["example"]}\n```'
      description += f'\n\n**Example**\n{example}'

    embed = discord.Embed(title=title, description=description)
    # Set the footer with the API version in small italics
    embed.set_footer(text=f'API Version: {TEARDOWN_API["version"]}')
    await ctx.send(embed=embed)


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


@slash.slash(name="Tags",
             description="Get information about Teardown tags",
             options=[
               create_option(name="tag",
                             description="Enter the name of the tag",
                             option_type=3,
                             required=True)
             ])
async def _teardowntags(ctx: SlashContext, tag: str = None):
  if tag == "all":
    response = "```\n" + "\n".join(TEARDOWN_TAGS.keys()) + "\n```"
    title = f'Teardown Tags'
  elif tag and tag.lower() in TEARDOWN_TAGS:
    response = TEARDOWN_TAGS[tag.lower()]
    title = f'Tag: {tag}'
  else:
    response = f'Tag "{tag}" not found.'
    title = f'Tag: {tag}'
  embed = discord.Embed(title=title, description=response)
  embed.add_field(name="Credit", value="[Dennispedia](https://x4fx77x4f.github.io/dennispedia/teardown/tags.html)")
  await ctx.send(embed=embed)


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

# Add the new option for autocomplete entries
autocomplete_options = {
    "game": [],
    "hud": [],
    "level": [],
    "options": [],
    "promo": [],
    "savegame": [],
    "mods": [],
}

# Populate the autocomplete_options with matching keys
for key in TEARDOWN_REGISTRY:
    for option in autocomplete_options:
        if key.startswith(option + "."):
            autocomplete_options[option].append(key)

# Add the new option in the slash command
@slash.slash(
    name="Registry",
    description="Get information about Teardown registry",
    options=[
        create_option(
            name="registry",
            description="Enter the name of the registry",
            option_type=3,
            required=False
        ),
        create_option(
            name="autocomplete",
            description="Enter the name of the autocomplete entry",
            option_type=3,
            required=False,
            choices=list(autocomplete_options.keys())
        )
    ]
)
async def _teardownregistry(ctx: SlashContext, registry: str = None, autocomplete: str = None):
    if registry == "all":
        response = "```\n" + "\n".join(TEARDOWN_REGISTRY.keys()) + "\n```"
        title = f'Teardown Registry'
    elif registry and registry.lower() in TEARDOWN_REGISTRY:
        response = TEARDOWN_REGISTRY[registry.lower()]
        title = f'Registry: {registry}'
    elif autocomplete and autocomplete.lower() in autocomplete_options:
        response = "```\n" + "\n".join(autocomplete_options[autocomplete.lower()]) + "\n```"
        title = f'Autocomplete: {autocomplete}'
    else:
        response = f'Registry entry: "{registry}" not found.'
        title = f'Registry: {registry}'
    embed = discord.Embed(title=title, description=response)
    embed.add_field(name="Credit", value="[Dennispedia](https://x4fx77x4f.github.io/dennispedia/teardown/registry.html)")
    await ctx.send(embed=embed)

# Replace "YOUR_BOT_TOKEN" with the actual token for your bot
bot.run(
  "MTEwMjQyNTQwMzIwMjc0MDM3NA.G1wlTj.vd2wHO6um3lWNz8ZTiMY-ZQtz8VmBDYK3ju-nY")
