from typing import Literal
import discord, pymongo, certifi, os
from discord import app_commands
from discord.ext import commands


mongo = pymongo.MongoClient(os.getenv("DATABASE"), tlsCAFile=certifi.where())
polaris = mongo["823905036186419201"]
class AutoReact(commands.Cog):
	def __init__(self, bot:commands.bot) -> None:
		self.bot = bot
	autoreact = app_commands.Group(name="autoreact", description="Auto-react Commands")

	@app_commands.checks.has_permissions(manage_guild=True)
	@autoreact.command(name="add", description="Add an auto-react")
	async def ar_add(self, interaction:discord.Interaction, trigger_type:Literal['mention','normal', 'strict', 'startswith', 'endswith'], trigger_content:str, response_type:Literal['react_to_message', 'send_message'], response_content:str, delete_after:float=None):
		if delete_after == None: delete_after = "never"
		trigger_content = trigger_content.lower()
		triggers = []
		for ar in polaris.autoreact.find():
			triggers.append(ar["trigger"])
		if trigger_content in triggers:
			await interaction.response.send_message(f"`{trigger_content}` is an existing trigger.", ephemeral=True)
			return
		polaris.autoreact.insert_one({
			"trigger_type":trigger_type,
			"trigger":trigger_content,
			"response_type":response_type,
			"response_content":response_content,
			"delete_after":delete_after
		})
		
		await interaction.response.send_message(content="Successfully added the autoreaction")


	@app_commands.checks.has_permissions(manage_guild=True)
	@autoreact.command(name="remove", description="Remove an auto-react")
	async def ar_rem(self, interaction:discord.Interaction, trigger:str):
		triggers = []
		for ar in polaris.autoreact.find():
			triggers.append(ar["trigger"])
		if trigger not in triggers:
			await interaction.response.send_message(f"{trigger} is not an existing trigger.")
			return
		polaris.autoreact.delete_one({"trigger":trigger})
		await interaction.response.send_message("Deleted the trigger.")
	
	@app_commands.checks.has_permissions(manage_guild=True)
	@autoreact.command(name="list", description="Sends a list of existing auto reactions in the server")
	async def ar_list(self, interaction:discord.Interaction):
		triggers = ""
		responses = ""
		counter = 0
		for ar in polaris.autoreact.find():
			if counter%2 == 0:
				triggers = triggers +f'(`{ar["trigger_type"].upper()}`) **{ar["trigger"]}**\n'
				responses = responses + f'(`{ar["response_type"][0].upper()}`) **{ar["response_content"]}**\n'
			else:
				triggers = triggers +f'(`{ar["trigger_type"].upper()}`) {ar["trigger"]}\n'
				responses = responses + f'(`{ar["response_type"][0].upper()}`) {ar["response_content"]}\n'
		embed = discord.Embed(color=discord.Color.random(), title="Auto-Reacts of Polaris", description="`S` represents AR's which respond with a message and `R` represents those with an emoji reaction.")
		embed.add_field(name="Triggers", value=triggers, inline=False)
		embed.add_field(name="Responses", value=responses, inline=False)
		await interaction.response.send_message(embed = embed)
	@commands.Cog.listener("on_message")
	async def ar(self, message:discord.Message):
		if message.author.bot:return
		mention_triggers = []
		normal_triggers = []
		strict_triggers = []
		starts_with_triggers = []
		ends_with_triggers = []
		for ar in polaris.autoreact.find():
			if ar["trigger_type"]=="normal":normal_triggers.append(ar["trigger"])
			elif ar["trigger_type"]=="strict":strict_triggers.append(ar["trigger"])
			elif ar["trigger_type"]=="startswith":starts_with_triggers.append(ar["trigger"])
			elif ar["trigger_type"]=="endswith":ends_with_triggers.append(ar["trigger"])
			elif ar["trigger_type"]=="mention":mention_triggers.append(ar["trigger"])
		
		
		for mention in message.mentions:
			if str(mention.id) in mention_triggers:
				trigger = str(mention.id)
				if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"mention"})["response_type"]=="react_to_message":
					await message.add_reaction(polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"mention"})["response_content"])
				else:
					if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"mention"})["delete_after"] == "never":
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"mention"})["response_content"])
					else:
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"mention"})["response_content"], delete_after = polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["delete_after"])
			
		
		
		for trigger in normal_triggers:
			if f" {trigger} " in f" {message.content.lower()} ":
				if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["response_type"]=="react_to_message":
					await message.add_reaction(polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["response_content"])
				else:
					if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["delete_after"] == "never":
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["response_content"])
					else:
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["response_content"], delete_after = polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["delete_after"])
						
		for trigger in strict_triggers:
			if trigger == message.content:
				if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"strict"}) ["response_type"]== "react_to_message":
					await message.add_reaction(polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"strict"})["response_content"])
				else:
					if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"strict"})["delete_after"] == "never":
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"strict"})["response_content"])
					else:
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"strict"})["response_content"], delete_after = polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"strict"})["delete_after"])

		for trigger in starts_with_triggers:
			if (message.content.lower()).startswith(trigger):
				if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"startswith"}) ["response_type"]== "react_to_message":
					await message.add_reaction(polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"startswith"})["response_content"])
				else:
					if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"startswith"})["delete_after"] == "never":
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"startswith"})["response_content"])
					else:
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"startswith"})["response_content"], delete_after = polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"startswith"})["delete_after"])
		
		for trigger in ends_with_triggers:
			if (message.content.lower()).endswith(trigger):
				if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"endswith"}) ["response_type"]== "react_to_message":
					await message.add_reaction(polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"endswith"})["response_content"])
				else:
					if polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"normal"})["startswith"] == "never":
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"endswith"})["response_content"])
					else:
						await message.channel.send(content=polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"endswith"})["response_content"], delete_after = polaris.autoreact.find_one({"trigger":trigger, "trigger_type":"endswith"})["delete_after"])


async def setup(bot:commands.Bot):
	await bot.add_cog(AutoReact(bot), guilds=[discord.Object(979221209680068608),discord.Object(823905036186419201)])