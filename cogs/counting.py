import discord, pymongo, certifi, os
from discord import app_commands
from discord.ext import commands

mongo = pymongo.MongoClient(os.getenv("DATABASE"), tlsCAFile=certifi.where())

polaris = mongo["823905036186419201"]
counts = polaris["counts"]
config = polaris["config"]

def format(number:int):
	"""Helper function to add commas to the parameter number."""
	return str('{:,}'.format(number))

class Counting(commands.Cog):
	def __init__(self, bot:commands.Bot) -> None:
		self.bot = bot
	
	@app_commands.command(name = "score")
	async def score(self, interaction:discord.Interaction, member:discord.Member=None):
		if not member:member=interaction.user
		await interaction.response.defer()
		count_entries = [count for count in counts.find().sort("counts", pymongo.DESCENDING)]
		user_count = counts.find_one({"userid":member.id})
		if not user_count: 
			await interaction.followup.send(f"{member.name}#{member.discriminator} has never counted in the server.")
			return
		embed = discord.Embed(color = 0x2f3136)
		embed.add_field(name="Score", value=format(user_count["score"]), inline=True)
		embed.add_field(name="Position", value=format(count_entries.index(user_count)))
		embed.set_author(name=f"{member.name}'s Counting Stats", icon_url=member.avatar.url)
		await interaction.followup.send(embed=embed)
	
	@app_commands.checks.has_role(860028025315131403)
	@app_commands.command(name="set-count", description= "Set a user's count.")
	async def set_count(self, interaction:discord.Interaction, member:discord.Member, new_score:int):
		await interaction.response.defer()
		counts.update_one({"userid":member.id}, {"$set":{"score":new_score}})
		await interaction.followup.send(f"Done! Successfully set {member.name}#{member.discriminator}'s counting score to {format(new_score)}")

	@app_commands.command(name="count", description="Get the last count and user who counted.")
	async def last_count(self, interaction:discord.Interaction):
		await interaction.response.defer()
		user = config.find_one({"config":"counting"})["last_user"]
		count = format(config.find_one({"config":"counting"})["last_count"])
		await interaction.followup.send(content = f"Last count is `{count}`, by <@!{user}>", ephemeral=True)


	@commands.Cog.listener("on_message")
	async def update_count(self, message:discord.Message):
		if message.channel.id!=config.find_one({"config":"counting"})["channel"]:return
		if message.author.bot:return
		if message.author.id == config.find_one({"config":"counting"})["last_user"]:
			await message.delete()
			return
		if not message.content.isnumeric():
			await message.delete()
			return
		counted = int(message.content)
		if counted!=config.find_one({"config":"counting"})["last_count"]+1:
			await message.delete()
			return
		
		config.update_one({"config":"counting"}, {"$set":{"last_count":counted, "last_user":message.author.id}})
		
		count_users = []
		for counter in counts.find():
			count_users.append(counter["userid"])
		
		if message.author.id in count_users:
			prev_score = counts.find_one({"userid":message.author.id})["score"]
			counts.update_one({"userid":message.author.id}, {"$set":{"score":prev_score+1}})
		else:counts.insert_one({"userid":message.author.id, "score":1})
		
		await message.add_reaction("<:tick:935530534950563950>")
		
		if counted%100==0:await message.pin(reason="Multiple of 100")

		if counted>=2500:await message.author.add_roles(message.guild.get_role(836572237196689448))
		elif counted>=1000:await message.author.add_roles(message.guild.get_role(836572185555894312))
		elif counted>=500:await message.author.add_roles(message.guild.get_role(836571895104143422))
		elif counted>=250:await message.author.add_roles(message.guild.get_role(836571816759787591))


async def setup(bot:commands.Bot):
    await bot.add_cog(Counting(bot), guilds=[discord.Object(979221209680068608),discord.Object(823905036186419201)])
