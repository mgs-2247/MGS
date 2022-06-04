import discord, pymongo, certifi, os
from discord import app_commands
from discord.ext import commands


mongo = pymongo.MongoClient(os.getenv("DATABASE"), tlsCAFile=certifi.where())

polaris = mongo["823905036186419201"]
counts = polaris["counts"]
config = polaris["config"]
grinder = polaris["grinder"]
test = polaris["test"]

def format(number:int):
	"""Helper function to add commas to the parameter number."""
	return str('{:,}'.format(number))

class Tags(commands.Cog, app_commands.Group, name="tag"):
	def __init__(self, bot:commands.Bot) -> None:
		super().__init__()
		self.bot = bot
	
	@app_commands.command(name="set")
	async def set_tag(self, interaction:discord.Interaction, content:str):
		test.update_one({"name":"test"}, {"$set":{"content":content}})
		await interaction.response.send_message("done")
	
	@app_commands.command(name="testtag")
	async def test_tag(self, interaction:discord.Interaction):
		cont:str = test.find_one({"name":"test"})["content"]
		cont=cont.format(user=interaction.user, channel=interaction.channel, guild=interaction.guild)
		await interaction.response.send_message(cont)


async def setup(bot:commands.Bot):
	await bot.add_cog(Tags(bot), guilds=[discord.Object(979221209680068608),discord.Object(823905036186419201)])