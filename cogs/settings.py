import discord, pymongo, certifi, os
from discord import AllowedMentions, app_commands
from discord.ext import commands

from cogs.donation import Item, parse

mongo = pymongo.MongoClient(os.getenv("DATABASE"), tlsCAFile=certifi.where())

polaris = mongo["823905036186419201"]
counts = polaris["counts"]
dono = polaris["donations"]
config = polaris["config"]

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
		

class Confirmation(discord.ui.View):
	def __init__(self, interaction:discord.Interaction, description:str):
		super().__init__(timeout = 15)
		self.inter = interaction
		self.desc = description
		self.value = None
	
	@discord.ui.button(label = "Nevermind", style=discord.ButtonStyle.red, custom_id="CANCEL")
	async def cancel(self, inter:discord.Interaction, button:discord.Button):
		self.value = False
		for item in self.children:
			item:discord.Button
			if item.custom_id == "CONFIRM":item.style = discord.ButtonStyle.gray
			item.disabled = True
		embed = discord.Embed(color=discord.Color.red(), title = "Action Cancelled", description=self.desc)
		await inter.response.edit_message(embed = embed, view = self)
		self.stop()
	
	@discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="CONFIRM")
	async def confirm(self, inter:discord.Interaction, button:discord.Button):
		self.value = True
		for item in self.children:
			item:discord.Button
			if item.custom_id == "CANCEL":item.style = discord.ButtonStyle.gray
			item.disabled = True
		embed = discord.Embed(color=discord.Color.green(), title = "Action Confirmed", description=self.desc)
		await inter.response.edit_message(embed = embed, view = self)
		self.stop()
	
	
	async def on_timeout(self) -> None:
		for item in self.children:
			item.disabled = True
			await self.inter.edit_original_message(embed = discord.Embed(title="Timed Out", description=self.desc), view = self)


class Settings(commands.Cog, app_commands.Group, name = "set"):
	def __init__(self, bot:commands.Bot):
		super().__init__()
		self.bot = bot
	


	@app_commands.command(name="value", description=".")
	async def set_value(self, interaction:discord.Interaction, item:str, price:str, emoji:str=None):
		await interaction.response.defer()
		itemid = Item(item).id
		if not emoji: emoji = Item(item).emote
		img_url = f"https://cdn.discordapp.com/emojis/{emoji.split(':')[2].rstrip('>')}"
		amt = number_parse(price)
		dono.update_one({"itemid":itemid}, {"$set":{"price":amt}})
		dono.update_one({"itemid":itemid}, {"$set":{"emote":emoji}})
		dono.update_one({"itemid":itemid}, {"$set":{"url":img_url}})
		amount = parse("1 "+itemid)["amount"]
		conv_str = parse("1 "+itemid)["conversion"]
		if len(conv_str)>1024:
			conv_str = conv_str[0:1020]+"..."
		embed = discord.Embed(color = discord.Color.random(), title="Donation Value")
		embed.set_thumbnail(url=img_url)
		embed.add_field(name="Conversion", value = conv_str, inline = False)
		embed.add_field(name="Total Value", value = f"`⏣ {format(amount)}`")
		embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url)
		await interaction.followup.send(content ="Successfully Updated!", embed=embed)



	@app_commands.command(name = "giveaway-manager", description = ".")
	async def set_gman(self, interaction:discord.Interaction, role:discord.Role):
		await interaction.response.defer()
		current_gman_roles = config.find_one({"config":"gman"})["roles"]
		if role.id in current_gman_roles:
			desc = f"{role.mention} is already a Giveaway Manager role. Do you want to remove it?"
		else: desc = f"Are you sure that you want to add {role.mention} as a Giveaway Manager role?"
		embed = discord.Embed(color=0x2f3136, title = "Pending Confirmation", description=desc)
		view = Confirmation(interaction, desc)
		await interaction.followup.send(embed = embed, view = view)
		await view.wait()
		if view.value == True:
			if role.id in current_gman_roles:
				config.update_one({"config":"gman"}, {"$pull":{"roles":role.id}})
				await interaction.channel.send(content = f"{role.mention} removed from the list of giveaway managers.", allowed_mentions=AllowedMentions(roles = False))
			else:
				config.update_one({"config":"gman"}, {"$push":{"roles":role.id}})
				await interaction.channel.send(content = f"{role.mention} added to the list of giveaway managers.", allowed_mentions=AllowedMentions(roles = False))

	@app_commands.command(name = "dono-roles", description=".")
	async def set_dono_roles(self, interaction:discord.Interaction, role:discord.Role, amount:str):
		await interaction.response.defer()
		amt_parsed = number_parse(amount)
		current_roles = config.find_one({"config":"donoroles"})["roles"]
		current_amts = config.find_one({"config":"donoroles"})["amounts"]
		if amt_parsed in current_amts and role.id in current_roles:
			desc = f"{role.mention} is already assigned at {format(amt_parsed)}. Should I stop doing it?"
			view = Confirmation(interaction, desc)
			await interaction.followup.send(embed = discord.Embed(color=0x2f3136, description = desc), view=view)
			await view.wait()
			if view.value == True:
				await interaction.followup.send(f"Done! {role.mention} will not be assigned on donating {format(amt_parsed)}.")
				config.update_one({"config":"donoroles"}, {"$pull":{"roles":role.id}})
				config.update_one({"config":"donoroles"}, {"$pull":{"amounts":amt_parsed}})
		elif amt_parsed in current_amts:
			current_role = current_roles[current_amts.index(amt_parsed)]
			desc = f"<@&{current_role}> is being assigned on {format(amt_parsed)}. Do you want {role.mention} to be assigned instead?"
			view = Confirmation(interaction,desc)
			await interaction.followup.send(embed = discord.Embed(color=0x2f3136, description = desc), view=view)
			await view.wait()
			if view.value == True:
				await interaction.followup.send(f"Done! {role.mention} will be assigned on donating {format(amt_parsed)} instead of <@&{current_role}>.")
				config.update_one({"config":"donoroles"}, {"$pull":{"roles":current_role}})
				config.update_one({"config":"donoroles"}, {"$pull":{"amounts":amt_parsed}})
				config.update_one({"config":"donoroles"}, {"$push":{"roles":role.id}})
				config.update_one({"config":"donoroles"}, {"$push":{"amounts":amt_parsed}})
		elif role.id in current_roles:
			current_amt = current_amts[current_roles.index(role.id)]
			desc = f"{role.mention} is being assigned on {format(current_amt)}. Do you want it to be assigned on {format(amt_parsed)} instead?"
			view = Confirmation(interaction,desc)
			await interaction.followup.send(embed = discord.Embed(color=0x2f3136, description = desc), view=view)
			await view.wait()
			if view.value == True:
				await interaction.followup.send(f"Done! {role.mention} will be assigned on donating {format(amt_parsed)} instead of {current_amt}.")
				config.update_one({"config":"donoroles"}, {"$pull":{"roles":role.id}})
				config.update_one({"config":"donoroles"}, {"$pull":{"amounts":current_amt}})
				config.update_one({"config":"donoroles"}, {"$push":{"roles":role.id}})
				config.update_one({"config":"donoroles"}, {"$push":{"amounts":amt_parsed}})
		else:
			await interaction.followup.send(f"Done! {role.mention} will be assigned on donating {amt_parsed}")
			config.update_one({"config":"donoroles"}, {"$push":{"roles":role.id}})
			config.update_one({"config":"donoroles"}, {"$push":{"amounts":amt_parsed}})

	@app_commands.command(name="dono-log-channel", description=".")
	async def set_dono_log_channel(self, interaction:discord.Interaction, channel:discord.TextChannel):
		await interaction.response.defer()
		current_channel = config.find_one({"config":"donologchannel"})["channel"]
		if current_channel!=0:
			embed = discord.Embed(color=0x2f3136,title="Waiting for confirmation", description=f"Do you want to change the donation logging channel from <#{current_channel}> to <#{channel.id}>")
			view = Confirmation(interaction, f"Do you want to change the donation logging channel from <#{current_channel}> to <#{channel.id}>")			
			await interaction.followup.send(embed=embed, view=view)
			await view.wait()
			if view.value == True:
				config.update_one({"config":"donologchannel"},{"$set":{"channel":channel.id}})
				await interaction.followup.send(content=f"Done! Updated the donation logging channel from <#{current_channel}> to <#{channel.id}>")
		else:
			config.update_one({"config":"donologchannel"},{"$set":{"channel":channel.id}})
			await interaction.followup.send(content=f"Done! Set the donation logging channel to <#{channel.id}>.")

	@app_commands.command(name="last-count", description=".")			
	async def set_last_count(self, interaction:discord.Interaction, count:int):
		await interaction.response.defer()
		config.update_one({"config":"counting"}, {"$set":{"last_count":count}})
		await interaction.followup.send(f"Done! Set the last count to {count}")
	
	@app_commands.command(name="count-channel", description=".")
	async def set_count_channel(self, interaction:discord.Interaction, channel:discord.TextChannel):
		await interaction.defer()
		current_channel = config.find_one({"config":"counting"})["channel"]
		if current_channel!=0:
			embed = discord.Embed(color = 0x2f3136,title="Waiting for confirmation", description=f"Do you want to change the counting channel from <#{current_channel}> to <#{channel.id}>")
			view = Confirmation(interaction, f"Do you want to change the counting channel from <#{current_channel}> to <#{channel.id}>")			
			await interaction.followup.send(embed=embed, view=view)
			await view.wait()
			if view.value == True:
				config.update_one({"config":"counting"},{"$set":{"channel":channel.id}})
				await interaction.followup.send(content=f"Done! Updated the counting channel from <#{current_channel}> to <#{channel.id}>")
		else:
			config.update_one({"config":"counting"},{"$set":{"channel":channel.id}})
			await interaction.followup.send(content=f"Done! Set the counting channel to <#{channel.id}>.")
			


async def setup(bot:commands.Bot):
	await bot.add_cog(Settings(bot), guilds=[discord.Object(979221209680068608),discord.Object(823905036186419201)])