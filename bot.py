import discord, pymongo, certifi, os
from discord.ext import commands



mongo = pymongo.MongoClient(os.getenv("DATABASE"), tlsCAFile=certifi.where())

polaris = mongo["823905036186419201"]
counts = polaris["counts"]
config = polaris["config"]
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='mgs ', intents=intents)    




@bot.event
async def on_ready():
	await bot.change_presence(activity= discord.Activity(type=discord.ActivityType.listening, name="mgs"))
	await bot.load_extension('cogs.settings')
	await bot.load_extension('cogs.donation')
	await bot.load_extension('cogs.counting')
	await bot.load_extension('cogs.grinder')
	await bot.load_extension('cogs.ar')
	await bot.load_extension('cogs.tags')
	await bot.tree.sync(guild=discord.Object(823905036186419201))
	#await bot.tree.sync(guild=discord.Object(979221209680068608))

	print('Bot is online')

	
def format(number:int):
	"""Helper function to add commas to the parameter number."""
	return str('{:,}'.format(number))

def number_parse(number:str):
	"""Helper Function to convert shorthands like 2k, 3m, 5b to proper integers."""
	num = number.lower()
	replaced_num = num.replace("k","").replace("m","").replace("b","")
	multiply_with = 1
	if   "k" in num:multiply_with = 1000
	elif "m" in num:multiply_with = 1000000
	elif "b" in num:multiply_with = 1000000000
	try: parsed = float(replaced_num)*multiply_with
	except ValueError: parsed = 0
	return int(parsed)

class SettingsDropdown(discord.ui.Select):
	
	def __init__(self, inter:discord.Interaction):
		self.choice = None
		self.inter = inter
		options = [
			discord.SelectOption(label='Donation', description='View the current donation settings', ),
			discord.SelectOption(label='Counting', description="View the current donation settings",)
		]
		super().__init__(placeholder='Choose the category...', min_values=1, max_values=1, options=options)
	
	async def callback(self, interaction:discord.Interaction):
		if interaction.user.id != self.inter.user.id:
			await interaction.response.send_message("This is not for you.", ephemeral = True)
			return
		embed = discord.Embed(color=0x2f3136)
		self.choice = self.values[0]
		if self.values[0] == "Donation": 
			giveaway_managers = ""
			for role in config.find_one({"config":"gman"})["roles"]:
				giveaway_managers = giveaway_managers + f"<@&{role}>\n"
			dono_roles = ""
			for amt in config.find_one({"config":"donoroles"})["amounts"]:
				dono_roles = dono_roles+f"`{format(amt)}`: <@&{config.find_one({'config':'donoroles'})['roles'][config.find_one({'config':'donoroles'})['amounts'].index(amt)]}>\n"
			log_channel = config.find_one({"config":"donologchannel"})["channel"]
			embed.title = "Donation Settings"
			embed.add_field(name="Giveaway Managers", value=giveaway_managers, inline=True)
			embed.add_field(name="Donation Roles", value=dono_roles)
			embed.add_field(name="Log Channel", value=f"<#{log_channel}>")

		elif self.values[0] == "Counting":
			last_count = config.find_one({"config":"counting"})["last_count"]
			last_user = config.find_one({"config":"counting"})["last_user"]
			count_channel = config.find_one({"config":"counting"})["channel"]
			embed.title = "Counting Settings"
			embed.add_field(name = "Last Count", value = format(last_count))
			embed.add_field(name = "Last User", value = f"<@!{last_user}>")
			embed.add_field(name = "Counting Channel", value = f"<#{count_channel}>")

		embed.set_author(name = "Settings")
		await interaction.response.edit_message(embed = embed)
		

class DropdownView(discord.ui.View):
	def __init__(self, inter:discord.Interaction):
		super().__init__(timeout=20)
		self.inter = inter
		# Adds the dropdown to our view object.
		self.add_item(SettingsDropdown(inter=inter))

	async def on_timeout(self):
		for item in self.children:
			item:discord.ui.Select
			item.disabled = True
		await self.inter.edit_original_message(view = self)


@bot.tree.command(name="settings", guilds=[discord.Object(979221209680068608),discord.Object(823905036186419201)])
async def settings(interaction:discord.Interaction):
	view = DropdownView(interaction)
	await interaction.response.send_message(view=view)
	

#bot.run('ODg4NjQwODYyNzk4NjE4Njc2.YUVpSw.EqV-MXmaruQ427jMx6MR-rhDE5E')
bot.run(os.getenv("BOT_TOKEN"))

