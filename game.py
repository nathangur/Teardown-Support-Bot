from interactions import (
    Button,
    ButtonStyle,
    Client,
    ComponentContext,
    Extension,
    component_callback,
    slash_command,
    SlashContext,
    Embed,
    spread_to_rows,
    ActionRow,
    File,
    listen,
)
from interactions.ext.paginators import Paginator
import json
import os
import asyncio
import random
import datetime

# This is a prop hunt mini game that is too advanced for the discord API to handle because it sucks. 

maps = ["hollowrock", "frustrum", "marina", "villa", "quillez", "hub", "lee", "isle", "evertides", "muratori", "other"]

game_instances = {}

class Main(Extension): 
    def __init__(self, client: Client):
        self.client = client

    # Create a new function to update buttons  

    async def update_buttons(self, ctx: ComponentContext, game):
        if ctx.author.id in game.players:
            disabled = False 

            # Only check if guesses if current round
            if game.current_round:

                # Ensure player is in game
                if ctx.author.id in game.players: 

                    # Check if player guessed this round
                    if ctx.author.id in game.current_round["guesses"]:
                        disabled = True
            components = spread_to_rows(
                Button(style=ButtonStyle.RED, label="Leave Game", custom_id="leave"), 
                *[
                    Button(style=ButtonStyle.SECONDARY, label=f"{map_name}", custom_id=f"guess_{i}",  
                        disabled=False)  
                    for i, map_name in enumerate(maps)
                ]
            )
            await ctx.edit_origin(content="Buttons have been updated!", components=components)
        else:
            components = [
                ActionRow(
                    Button(style=ButtonStyle.GREEN, label="Start Game", custom_id="start"),
                    Button(style=ButtonStyle.GREEN, label="Join Game", custom_id="join"),
                )
            ]
            await ctx.send("Buttons have been updated!", components=components, ephemeral=True)      

    @slash_command(
        name="geo",
        description="Initalize the main geo menu",
    )
    async def geo(self, ctx: ComponentContext): 
        # Game instances are created per user, not per guild
        if ctx.guild.id not in game_instances:
            game_instances[ctx.guild.id] = Game(ctx.channel, ctx.author.id, self.client)

        game = game_instances[ctx.guild.id]
        await self.update_buttons(ctx, game)  

        if game.message is None or game.game_status != "active":
            await game.update_message(ctx.author.id, ctx)  
            
    @component_callback("start")
    async def start_callback(self, ctx: ComponentContext):
        game = game_instances[ctx.guild.id]
        game.load_scores()
        game.game_status = "active"
        await game.add_player(ctx.author.id, ctx)  
        await game.start_new_round()
        await self.update_buttons(ctx, game)   
        await game.update_message(ctx.author.id, ctx)   

    
    @component_callback("join")
    async def join_callback(self, ctx: ComponentContext):
        game = game_instances[ctx.guild.id]
        await game.add_player(ctx.author.id)
        await self.update_buttons(ctx, game)
        await ctx.send("You have joined the game!", ephemeral=True)
        
    @component_callback("leave")
    async def leave_callback(self, ctx: ComponentContext):
        game = game_instances[ctx.guild.id]
        await game.remove_player(ctx.author.id, ctx)

    @listen("on_component")
    async def make_guess_callback(self, component):
        # Ignore non guess buttons
        if not component.ctx.custom_id.startswith("guess"):
            return            

        map_id = component.ctx.custom_id.split("_")[1]
        # Check if map_id is within the range
        if not 0 <= int(map_id) < len(maps):
            print(f"Received invalid map_id: {map_id}")
            return 

        game = game_instances[component.ctx.guild.id]
        map_guess = maps[int(map_id)]
        print(f"Received guess: {map_guess}")
        await game.handle_guess(component.ctx.author.id, map_guess, component.ctx)
        if await game.check_all_players_guessed() or len(game.players) == 1:
            await game.start_new_round()
        # Wrapped the HTTP interaction in a try-except block
        try:
            await game.update_message(component.ctx.author.id, component.ctx)
        except Exception as e:
            print(f"Error in updating message: {str(e)}")


    @component_callback("leaderboard")
    async def leaderboard_callback(self, ctx: ComponentContext):
        game = game_instances[ctx.guild.id]
        game.load_scores()  # Load the scores from the file
        leaderboard = sorted(game.all_players.items(), key=lambda x: x[1], reverse=True)[:10]  # Take top 10 scores
        embeds = [Embed(title="Leaderboard")]
        for player, score in leaderboard:
            user = await self.client.fetch_user(player)  # Fetch user details
            embeds[-1].add_field(name=f"{user.display_name}", value=str(score), inline=True)
        self.paginator = Paginator.create_from_embeds(self.client, *embeds) 
        await self.paginator.send(ctx)

    @component_callback("back")
    async def back_callback(self, ctx: ComponentContext):
        game = game_instances[ctx.guild.id]
        initial_message = "Welcome to Geoguesser! Click 'Start Game' to begin a new game, or 'Join Game' to join an existing game. You can also view the leaderboard."
        components = [
            ActionRow(
                Button(style=ButtonStyle.GREEN, label="Start Game", custom_id="start"),
                Button(style=ButtonStyle.GREEN, label="Join Game", custom_id="join", disabled=(game.game_status != "active")),
                Button(style=ButtonStyle.BLURPLE, label="Leaderboard", custom_id="leaderboard"),
            )
        ]
        await ctx.edit_origin(content=initial_message, components=components)

class Game:
    # These are global because for some reason it didn't like it being nested

    message = None  
    game_status = "idle"
    players = {}  
    all_players = {}  # Store all players from score.json
    images = {}  

    def __init__(self, channel, host, client: Client):
        self.current_message_id = None
        self.current_round = None
        self.current_round_id = None  # Unique identifier for each round
        self.image_dir = "/root/TTS/hunt/Images/"  
        self.channel = channel
        self.host = host
        self.client = client
        #self.client = client  
        self.refresh_images()  

        self.first_place = None  # Track the first place player
        self.score_file = "/root/TTS/scores.json"  # JSON file to store scores
        self.load_scores()
        self.timer_length = 20  # Duration of each round in seconds
        self.round_task = None  # Task for the round timer

    def refresh_images(self):
        self.images = os.listdir(self.image_dir)

    async def add_player(self, player_id, ctx=None):
        if player_id not in self.all_players:
            self.players[player_id] = 0
            self.save_scores()

    async def remove_player(self, player_id, ctx: ComponentContext):
        if player_id in self.round_task:
            await self.round_task[player_id]
            self.round_task[player_id].cancel()
        self.players.pop(player_id, None)
        self.save_scores()
        if player_id in self.current_round["guesses"]:
            del self.current_round["guesses"][player_id]
        if not self.players:  # If no more players, set game to idle
            self.game_status = "idle"
            # Cancel round timer task if it exists
            if self.round_task:
                self.round_task.cancel()
                self.round_task = None
        initial_message = "Welcome to Geoguesser! Click 'Start Game' to begin a new game, or 'Join Game' to join an existing game. You can also view the leaderboard."
        components = [
            ActionRow(
                Button(style=ButtonStyle.GREEN, label="Start Game", custom_id="start"),
                Button(style=ButtonStyle.GREEN, label="Join Game", custom_id="join", disabled=(self.game_status != "active")),
                Button(style=ButtonStyle.BLURPLE, label="Leaderboard", custom_id="leaderboard"),
            )
        ]
        await ctx.edit_origin(content=initial_message, components=components)

    async def start_new_round(self):
        self.game_status = "active"
        if self.current_round is None:
            self.current_round = {}

        self.refresh_images()

        # Remove previously selected image
        if "image_file" in self.current_round:
            self.images.remove(self.current_round["image_file"])

        # Do not start a new round if there are no players
        if not self.players:
            return

        image_file = random.choice(self.images)
        map_name = self.parse_image_file(image_file)

        self.current_round_id = asyncio.get_event_loop().time()  # Generate a new round ID
        self.current_round = {
            "map_name": map_name,
            "image_file": image_file,
            "start_time": self.current_round_id,
            "guesses": {player_id: None for player_id in self.players}  # Reset guesses for each round
        }

        self.round_task = asyncio.create_task(self.round_timer())

    def parse_image_file(self, image_file):
        map_name = image_file.split('_')[0] # Use first part of name before
        if map_name not in maps:
            map_name = "other"
        return map_name

    async def handle_guess(self, player_id, map_guess, ctx: ComponentContext):
        game = game_instances[ctx.guild.id] 

        # Additional validation 
        if self.game_status != "active":
            return

        if player_id not in self.players:
            return

        self.current_round["map_name"] = self.parse_image_file(self.current_round["image_file"])
        print(f"Comparing {self.current_round['map_name']} with {map_guess}")
        map_correct = self.current_round["map_name"] == map_guess
        self.current_round["map_name"] = None  # Reset current round map name after checking a guess

        if map_correct: 
            if player_id in self.all_players:
                self.all_players[player_id] += 100
            else:
                self.all_players[player_id] = 100
        else: 
            if player_id in self.all_players:
                self.all_players[player_id] -= 50
            else:
                self.all_players[player_id] = -50

        self.save_scores()
    
        self.current_round["guesses"][player_id] = map_guess  # Record the player's guess

        # After handling the guess, check if all players have guessed
        if await self.check_all_players_guessed():
            await self.start_new_round()
        else:
            # If not all players have guessed, disable the buttons for the player who has guessed
            await Main.update_buttons(self, ctx, game)

    async def check_all_players_guessed(self):

        # Immediately proceed to next round if there's only one player
        if len(self.players) == 1:
            await self.start_new_round()
    
        current_players = set(self.current_round["guesses"].keys())
        return current_players == set(self.players.keys())


    async def update_message(self, player_id, ctx: ComponentContext): 
        remaining_time = 0
        if self.game_status != "active":
            return
        if self.current_round is not None:
            remaining_time = self.timer_length - (asyncio.get_event_loop().time() - self.current_round["start_time"])
            user = await self.client.fetch_user(player_id)  # Fetch user details

            with open(os.path.join(self.image_dir, self.current_round["image_file"]), "rb") as img_file:
                file = File(img_file, file_name="image.png")
                embed = Embed(  
                    title=f"Game by {user.display_name}",
                    description=f"Time Remaining: {remaining_time:.2f}s",
                    color=0x0066FF
                )
                embed.set_image(url="attachment://image.png")

                # Updating leaderboard
                leaderboard_sorted = sorted(self.all_players.items(), key=lambda x: x[1], reverse=True)[:10]  # Take top 10 scores
                leaderboard_string = "\n".join(f"{i+1}. <@{user}>: {score}" for i, (user, score) in enumerate(leaderboard_sorted[:3]))
                embed.add_field(name="Leaderboard", value=(leaderboard_string if leaderboard_string is not None else 0))

                # Update number of players in the footer
                embed.set_footer(text=f"Number of players: {len(self.players)}")

                if len(self.players) == 0:
                    self.game_status = "idle"
                    # Cancel round timer task if it exists
                    if self.round_task:
                        self.round_task.cancel()
                        self.round_task = None
                    await self.message.delete()

                if self.message is not None:
                    await self.message.delete()

                if not self.current_message_id:
                    self.current_message_id = (await ctx.channel.send(embed=embed, file=file)).id

                if self.current_message_id:
                    message = await ctx.channel.fetch_message(self.current_message_id) 
                    await message.edit(embed=embed, file=file)
                
                await self.round_timer()    

    async def round_timer(self):
        round_id_at_start_of_timer = self.current_round_id  # Save the current round ID

        await asyncio.sleep(self.timer_length)

        # Verify if the round is still the same as when the timer was started
        if self.current_round_id == round_id_at_start_of_timer:
            if self.current_round is not None and set(self.current_round["guesses"].keys()) != set(self.players.keys()):
                print("Not all players have guessed. Ending round...")
                await self.start_new_round()

    def save_scores(self):
        with open(self.score_file, 'w') as f:
            json.dump(self.all_players, f)

    def load_scores(self):
        try:
            with open(self.score_file, 'r') as f:
                self.all_players = json.load(f)
        except Exception as e:
            print(f"Error loading scores: {e}")
        self.players = {k: v for k, v in self.all_players.items() if k in self.players}  # Filter out players not currently in game
    
def setup(bot):
     Main(bot)