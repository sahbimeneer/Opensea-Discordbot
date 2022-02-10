from opensea import OpenseaAPI
from discord.ext import tasks
from discord import Client, Embed

from constants import OPENSEA_API_KEY, DISCORD_TOKEN
from constants import NOT_ENOUGH_ARGUMENTS
from constants import NOTIFIERS_FILE_NAME, BOT_SETTINGS_FILE_NAME

import json
import asyncio
import os


class OpenSeaBot(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.opensea_api = OpenseaAPI(apikey=OPENSEA_API_KEY)

        self.metadata = json.load(open(BOT_SETTINGS_FILE_NAME, "r"))
        self.notifiers = json.load(open(NOTIFIERS_FILE_NAME, "r"))

        self.primary_color = hex(int(self.metadata["primary_color"], 16))
        self.error_color = hex(int(self.metadata["error_color"], 16))

        self.prefix = self.metadata["prefix"]
        self.commands = self.metadata["commands"]
        for value in self.commands.values():
            value["function"] = getattr(self, value["function"])

        self.notifier.start()
    
    def add_notifier(self, author_id, collection, floor_price):
        self.notifiers[author_id] = {
            "collection": collection,
            "floor_price": floor_price
        }

        with open(NOTIFIERS_FILE_NAME, "w") as fp:
            fp.write(json.dumps(self.notifiers, indent=4))
    
    async def send_dm(self, user, message=None, embed=None):
        channel = await user.create_dm()
        if embed:
            await channel.send(embed=embed)
        else:
            await channel.send(message)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
    
    @tasks.loop(seconds=30)
    async def notifier(self):
        for author_id, value in self.notifiers.items():
            stats = self.opensea_api.collection_stats(collection_slug=value["collection"])

            current_floor_price = stats["stats"]["floor_price"]
            if current_floor_price < value["floor_price"]:
                embed = Embed(
                    title="Notification", 
                    color=self.primary_color, 
                    description=f"The current floor price of {value['collection']} is {current_floor_price} ETH which is below the floor price you set a notification for ({value['floor_price']} ETH)"
                )

                user = await self.fetch_user(author_id)
                self.send_dm(user, embed=embed)

            await asyncio.sleep(2)

    async def on_message(self, message):
        if message.author.id != self.user.id:
            if message.content.startswith(self.prefix):
                command = message.content.split(" ")[0][len(self.prefix):]
                args = message.content.split(" ")[1:]
                if command in self.commands:
                    if len(args) >= len(self.commands[command]["args"]):
                        await self.commands[command]["function"](message, *args)
                    else:
                        await self.error(message.channel, command, error=NOT_ENOUGH_ARGUMENTS)

    async def error(self, channel, command=None, error=None):
        description = "An error occured when trying to execute your command."

        fields = []
        if error == NOT_ENOUGH_ARGUMENTS:
            args = self.commands[command]["args"]
            args_required = len(args)

            description = "You did not pass enough required arguments"

            how_to_use = f"--{command} "
            for arg in args:
                how_to_use += f"[{arg}] "
            how_to_use = how_to_use[:-1]

            fields.append(("How to use this command", how_to_use))
            fields.append(("Arguments required", str(args_required)))

        embed = Embed(title="Error", color=self.error_color, description=description)
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=False)

        await channel.send(embed=embed)

    async def notify(self, message, collection, floor_price, *args):
        stats = self.opensea_api.collection_stats(collection_slug=collection)

        channel = message.channel
        author = message.author

        embed = Embed(title="Notify", color=self.primary_color)

        floor_price = float(floor_price)
        current_floor_price = stats["stats"]["floor_price"]
        if current_floor_price < floor_price:
            embed.add_field(name="Collection",
                            value=collection,
                            inline=False)
            embed.add_field(name="Current floor price", 
                            value=f"{current_floor_price} ETH",
                            inline=False)
            embed.add_field(name="Error", 
                            value=f"The current floor price is already below {floor_price} ETH", 
                            inline=False)

            await channel.send(embed=embed)
        else:
            self.add_notifier(author.id, collection, floor_price)
            embed.add_field("Success", f"We will send you a DM when the floor price goes below {floor_price} ETH!")
            await channel.send(embed=embed)


opensea_discordbot = OpenSeaBot()
opensea_discordbot.run(DISCORD_TOKEN)