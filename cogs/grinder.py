import discord, pymongo, certifi, pagination, leaderboard, os
from discord import app_commands
from discord.ext import commands
from cogs.donation import Dono
from cogs.settings import Confirmation


mongo = pymongo.MongoClient(os.getenv("DATABASE"), tlsCAFile=certifi.where())

polaris = mongo["823905036186419201"]
counts = polaris["counts"]
config = polaris["config"]
grinder = polaris["grinder"]

def format(number:int):
	"""Helper function to add commas to the parameter number."""
	return str('{:,}'.format(number))

class Grinder(commands.Cog, app_commands.Group, name="grinder"):
	def __init__(self, bot:commands.Bot) -> None:
		super().__init__()
		self.bot = bot
	
	@app_commands.command(name="add-user", description=".")
	async def add_user(self, interaction:discord.Interaction, member:discord.Member):
		await interaction.response.defer()
		if str(member.id) in config.find_one({"config":"grinder"})["users"]:
			view = Confirmation(interaction, f"{member.mention} is already a part of the grinder team. Do you want to remove them?")
			await interaction.followup.send(embed=discord.Embed(color=0x2f3136, title="Waiting for confirmation", description=f"{member.mention} is already a part of the grinder team. Do you want to remove them?"), view=view)
			await view.wait()
			if view.value==True:
				try:await member.remove_roles(interaction.guild.get_role(885484251091435602))
				except:pass
				config.update_one({"config":"grinder"}, {"$pull":{"users":str(member.id)}})
				grinder.delete_one({"userid":str(member.id)})
				await interaction.followup.send(f"Done. {member.name} is no longer a part of the grinder team :(")
		else:
			view = Confirmation(interaction, f"Are you sure you want to add {member.mention} to the grinder team?")
			await interaction.followup.send(embed=discord.Embed(color=0x2f3136, title="Waiting for confirmation", description=f"Are you sure you want to add {member.mention} to the grinder team?"), view=view)			
			await view.wait()		
			if view.value==True:
				try:await member.add_roles(interaction.guild.get_role(885484251091435602))
				except:pass
				config.update_one({"config":"grinder"}, {"$push":{"users":str(member.id)}})
				grinder.insert_one({"userid":str(member.id), "donated":0})
				await interaction.followup.send(f"Welcome to the grinder team {member.mention}")

	@app_commands.command(name="setnote", description=".")				
	async def setnote(self, interaction:discord.Interaction, user:discord.Member, input:str):
		if str(user.id) not in config.find_one({"config":"grinder"})["users"]:
			await interaction.response.send_message(f"{user.mention} is not a part of the grinder team!", ephemeral=True)
			return
		await interaction.response.defer()
		donated = Dono(input, user, interaction)
		amt = donated.amount
		grinder.update_one({"userid":str(user.id)}, {"$inc":{"donated":amt}})
		donated.setnote()
		embed=discord.Embed(color=discord.Color.random(), title="Grinder Setnote", description=f"Added `⏣ {format(amt)}`.\nThey now have donated `⏣ {format(grinder.find_one({'userid':str(user.id)})['donated'])}`.")
		await interaction.followup.send(embed=embed)

	@app_commands.command(name="removenote", description=".")				
	async def removenote(self, interaction:discord.Interaction, user:discord.Member, input:str):
		if str(user.id) not in config.find_one({"config":"grinder"})["users"]:
			await interaction.response.send_message(f"{user.mention} is not a part of the grinder team!", ephemeral=True)
			return
		await interaction.response.defer()
		donated = Dono(input, user, interaction)
		amt = donated.amount
		grinder.update_one({"userid":str(user.id)}, {"$inc":{"donated":-amt}})
		donated.removenote()
		embed=discord.Embed(color=discord.Color.random(), title="Grinder Removenote", description=f"Removed `⏣ {format(amt)}`.\nThey now have donated `⏣ {format(grinder.find_one({'userid':str(user.id)})['donated'])}`.")
		await interaction.followup.send(embed=embed)
	
	@app_commands.command(name="notify", description=".")
	async def notify(self, interaction:discord.Interaction):
		await interaction.response.defer()
		to_be_notified = []
		for entry in grinder.find():
			if entry['donated']<config.find_one({"config":"grinder"})["goal"]:
				to_be_notified.append(int(entry["userid"]))
		desc = "Do you want to notify the following users via DM?"
		for user in to_be_notified:desc=desc+f"\n<@!{user}>"
		view = Confirmation(interaction,desc)
		await interaction.followup.send(embed=discord.Embed(title="Waiting for confirmation", description=desc),view=view)
		await view.wait()
		if view.value==True:
			for user in to_be_notified:
				try:
					user_obj = interaction.guild.get_member(user)
				except:pass
				try: await user_obj.send(embed=discord.Embed(title="Reminder", description="A gentle reminder to finish your grinder donations.\n").set_footer(text="Sent from Polaris 823905036186419201"))
				except:await interaction.channel.send(f"Not able to DM <@!{user}>")

	@app_commands.command(name="reset", description=".")
	async def reset(self, interaction:discord.Interaction):
		await interaction.response.defer()
		for entry in grinder.find():
			grinder.update_one({"userid":entry["userid"]}, {"$set":{"donated":0}})
		await interaction.followup.send("Successfully reset the grinder donations. Happy Grinding :) ")


	@app_commands.command(name="leaderboard", description=".")
	async def grinder_lb(self, interaction:discord.Interaction):
		await interaction.response.defer()
		entries = []
		goal = config.find_one({"config":"grinder"})["goal"]
		for entry in grinder.find().sort('donated', pymongo.DESCENDING):
			entries.append(f"<@!{entry['userid']}>: `⏣ {format(entry['donated'])}/ ⏣ {format(goal)}`")
		paginate = pagination.Paginate(entries, 10, True)
		view=leaderboard.Leaderboard(paginate, interaction)
		await view.disable_right()  
		await interaction.followup.send(embed=discord.Embed(color=0x2f3136, description=paginate.get_page(1)), view=view)



async def setup(bot:commands.Bot):
	await bot.add_cog(Grinder(bot), guilds=[discord.Object(979221209680068608),discord.Object(823905036186419201)])