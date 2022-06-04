import random, os
import pagination, leaderboard
import discord, pymongo, certifi
from fuzzywuzzy import process
from discord.ext import commands
from discord import app_commands

mongo = pymongo.MongoClient(os.getenv("DATABASE"), tlsCAFile=certifi.where())
polaris = mongo["823905036186419201"]
dono = polaris["donations"]
items = polaris["items"]
config = polaris["config"]

donation_quotes = [""]

"""class Dono:
    def __init__(self, user:discord.User) -> None:
        donations = dono.find_one({"userid":user.id})
        if not donations:donations = 0
"""
def donations(user:discord.User):
    """Helper Function to get the donations of a usef from the database."""
    try:donations = dono.find_one({"userid":str(user.id)})["donated"]
    except:donations = 0
    return donations

def err_msg(parameter:str):
    """Helper Function for the error messages."""
    return f"<:error:877514903890575390> `{parameter}` is invalid." 

def format(number:int):
    """Helper function to add commas to the parameter number."""
    return str('{:,}'.format(number))

def number_parse(number:str):
    """Helper Function to convert shorthands like 2k, 3m, 5b to proper integers."""
    num = number.lower()
    multiply_with = 1
    replaced_num = num.replace("k","").replace("m","").replace("b","")
    if   "k" in num:multiply_with = 1000
    elif "m" in num:multiply_with = 1000000
    elif "b" in num:multiply_with = 1000000000
    try: parsed = float(replaced_num)*multiply_with
    except ValueError: parsed = 0
    return int(parsed)

def add_dono_role(dono:int):
    """Helper Function to return which donation role is to be added for a given donation."""
    amounts:list = polaris["config"].find_one({"config":"donoroles"})["amounts"]
    roles:list[int] = polaris["config"].find_one({"config":"donoroles"})["roles"]
    amounts_lessthan_dono = [0,0]
    for amount in amounts:
        if amount<=dono: amounts_lessthan_dono.append(amount)
    max_amount = max(*amounts_lessthan_dono)
    role = roles[amounts.index(max_amount)]
    return role

class Item:
    """Creates an Item class from the user inputted query"""
    def __init__(self, query:str) -> None:
        itemids = []
        for document in items.find(): itemids.append(document["itemid"])
        matched_itemid = process.extractOne(query=query, choices = itemids)[0]
        info = items.find_one({"itemid":matched_itemid})
        self.id:    str = info["itemid"]
        self.name:  str = info["name"]
        self.emote: str = info["emote"]
        self.price: int = info["price"]
        self.image: str = info["url"]





def parse(input:str):
    input_split = input.split()
    possible_items = []
    total_amount = 0
    conversion_string = ""
    for x in range(len(input_split)):
        if number_parse(input_split[x])<=0:possible_items.append(x)
    input_split_without_items = [] #initializing a variable from which the items and item quantities will be popped later on
    for item_index in possible_items:
        if number_parse(input_split[item_index-1])<=0: 
            raise 
        item = Item(input_split[item_index])                #basically creating an item class, and adding the value of the item to the 
        quantity = number_parse(input_split[item_index-1])  #total_amount variable
        price_of_1 = item.price
        value = quantity*price_of_1
        total_amount+=value #at this point all the items have been added to the total_amount. so we can get rid of them from the input_split
        conversion_string = conversion_string+f"`{format(quantity)}×` {item.emote} {item.name} is worth `⏣ {format(value)}`\n"
    for x in range(len(input_split)):
        if x not in possible_items and x+1 not in possible_items:
            input_split_without_items.append(input_split[x])
    for amount in input_split_without_items:
        conversion_string = f"`⏣ {format(number_parse(amount))}`\n"+conversion_string
        if number_parse(amount)<=0:raise
        total_amount+=number_parse(amount)

    return {"amount":total_amount, "conversion":conversion_string}


class Dono:
    def __init__(self, input:str, donor:discord.Member, interaction:discord.Interaction) -> None:
        self.amount      = parse(input)["amount"]
        self.conversion  = parse(input)["conversion"]
        self.interaction = interaction
        self.donor       = donor
    def setnote(self):
        donor   = self.donor
        amount  = self.amount
        inter   = self.interaction
        donors  = [document["userid"] for document in dono.find()]
        if str(donor.id) not in donors: dono.insert_one({"userid":str(donor.id), "donated":amount})
        else: dono.update_one({"userid":str(donor.id)}, {"$set":{"donated":donations(donor)+amount}})
    def removenote(self):
        donor   = self.donor
        amount  = self.amount if self.amount<donations(donor) else donations(donor)
        inter   = self.interaction
        donors  = [document["userid"] for document in dono.find()]
        if str(donor.id) not in donors: dono.insert_one({"userid":str(donor.id), "donated":amount})
        else: dono.update_one({"userid":str(donor.id)}, {"$set":{"donated":donations(donor)+amount}})      
    async def update_roles(self):
        user = self.donor
        guild = self.interaction.guild
        role_to_be_added = add_dono_role(donations(self.donor))
        roles_to_be_removed = []
        donor_roles:list = polaris["config"].find_one({"config":"donoroles"})["roles"]
        user_roles = user.roles
        for role in user_roles:
            if role:
                if role.id in donor_roles and role.id!=role_to_be_added:
                    roles_to_be_removed.append(role.id)
        try: await user.remove_roles(*(discord.Object(id=id) for id in roles_to_be_removed))
        except: pass
        role = guild.get_role(role_to_be_added)
        if role not in user_roles: 
            try:await user.add_roles(role) 
            except:pass
            return f"Added <@&{role_to_be_added}>!"
        return None
    

    async def leaderboard(self, per_page=10):
        if per_page<1:per_page=10
        entries = []
        for donation in dono.find().sort("donated", pymongo.DESCENDING):
            donated = f"`⏣ {format(donation['donated'])}`"
            userid = donation["userid"]
            #donor = await self.interaction.client.fetch_user(userid)
            entries.append(f"<@!{userid}>: {donated}")
        paginate = pagination.Paginate(entries, 10, True)
        await self.interaction.response.send_message(embed=discord.Embed(color=0x2f3136, description=paginate.get_page(1)), view=leaderboard.Leaderboard(paginate))
        
  
class Donation(commands.Cog):
    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(name = "value", description=".")
    async def value(self, interaction:discord.Interaction, input:str):
        await interaction.response.defer()
        if number_parse(input)<=0 and len(input.split())==1:input="1 "+input
        try:amount = parse(input)["amount"]
        except:
            await interaction.followup.send("Invalid input!")
            return
        conv_str = parse(input)["conversion"]
        if len(conv_str)>1024:
            conv_str = conv_str[0:1020]+"..."
        embed = discord.Embed(color = discord.Color.random(), title="Donation Value")
        embed.add_field(name="Conversion", value = conv_str, inline = False)
        embed.add_field(name="Total Value", value = f"`⏣ {format(amount)}`")
        embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url)
        await interaction.followup.send(embed = embed)
    
    @app_commands.command(name="notes", description = ".")
    async def notes(self, interaction:discord.Interaction, member:discord.Member=None):
        await interaction.response.defer()
        if not member: member = interaction.user
        donated = donations(member)
        embed = discord.Embed(color=discord.Color.random(), title=f"{member.name}#{member.discriminator}'s Donation Notes", description=f"{member.name} has donated `⏣ {format(donated)}` worth of items and coins to Polaris.")
        embed.set_footer(text="Go donate to get more perks!")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description=".")
    async def dono_lb(self, interaction:discord.Interaction):
        await interaction.response.defer()
        entries = []
        for donation in dono.find().sort("donated", pymongo.DESCENDING):
            donated = donation['donated']
            userid = donation["userid"]
            entries.append(f"<@!{userid}>: `⏣ {format(donated)}`")
        paginate = pagination.Paginate(entries, 10, True)
        view=leaderboard.Leaderboard(paginate, interaction)
        await view.disable_right()  
        await interaction.followup.send(embed=discord.Embed(color=0x2f3136, description=paginate.get_page(1)), view=view)

    @app_commands.command(name = "setnote", description=".")
    async def setnote(self, interaction:discord.Interaction, donor:discord.Member, input:str):
        await interaction.response.defer()
        if number_parse(input)<=0 and len(input.split())==1:input="1 "+input
        try:donation = Dono(input, donor, interaction)
        except:
            await interaction.followup.send("Invalid input!")
            return
        donation.setnote()
        role_update = await donation.update_roles()
        conv_str = donation.conversion
        if len(conv_str)>1024:conv_str=conv_str[0:1021]+"..."
        sn_embed = discord.Embed(color=discord.Color.random(), description=f"Thanks for the amazing donation {donor.mention}")
        sn_embed.set_author(name=f"{donor.name}#{donor.discriminator}'s Donation!", icon_url=donor.avatar.url)
        sn_embed.add_field(name="Conversion", value=conv_str, inline=False).add_field(name="Added Amount", value=f"Added: `⏣ {format(donation.amount)}`\nDonations: `⏣ {format(donations(donor))}`",inline=False)
        if role_update:sn_embed.add_field(name="Role up!", value=role_update, inline=False)
        sn_embed.set_footer(text=f"Note set by {interaction.user.id} \n\n{random.choice(donation_quotes)}")
        msg = await interaction.followup.send(embed = sn_embed)
        emt_1 = "<:div_replycontblue:910527294240587836>"
        emt_2 = "<:div_replyblue:910527342806450197>"
        msg_link = f"{emt_1} Message Link: [Click me](https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}/{msg.id})"
        desc = f"""
        {emt_1} Value:  `⏣ {str("{:,}".format(donation.amount))}`
        {msg_link}
        {emt_1} Added to: {donor.mention}
        {emt_2} Channel: {interaction.channel.mention} """
        log_embed = discord.Embed(color=discord.Color.random(), title="Note Set", description=desc)
        try:
            log_channel = await interaction.guild.fetch_channel(config.find_one({"config":"donologchannel"})["channel"])
            await log_channel.send(embed=log_embed)
        except:await interaction.channel.send("There is an error logging this note!")
    
    @app_commands.command(name = "removenote", description=".")
    async def removenote(self, interaction:discord.Interaction, donor:discord.Member, input:str):
        if number_parse(input)<=0 and len(input.split())==1:input="1 "+input
        await interaction.response.defer()
        try:donation = Dono(input, donor, interaction)
        except:
            await interaction.followup.send("Invalid input!")
            return
        donation.removenote()
        conv_str = donation.conversion
        if len(conv_str)>1024:conv_str=conv_str[0:1021]+"..."
        rn_embed = discord.Embed(color=discord.Color.random(), description=f"Looks like someone did a mistake!")
        rn_embed.set_author(name=f"{donor.name}#{donor.discriminator}'s Donation", icon_url=donor.avatar.url)
        rn_embed.add_field(name="Conversion", value=conv_str, inline=False).add_field(name="Removed Amount", value=f"Removed: `⏣ {format(donation.amount)}`\nDonations: `⏣ {format(donations(donor))}`",inline=False)
        rn_embed.set_footer(text=f"Note removed by {interaction.user.id} \n\n{random.choice(donation_quotes)}")
        msg = await interaction.followup.send(embed = rn_embed)
        emt_1 = "<:div_replycontblue:910527294240587836>"
        emt_2 = "<:div_replyblue:910527342806450197>"
        msg_link = f"{emt_1} Message Link: [Click me](https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}/{msg.id})"
        desc = f"""
        {emt_1} Value:  `⏣ {str("{:,}".format(donation.amount))}`
        {msg_link}
        {emt_1} Added to: {donor.mention}
        {emt_2} Channel: {interaction.channel.mention} """
        log_embed = discord.Embed(color=discord.Color.random(), title="Note Removed", description=desc)
        try:
            log_channel = await interaction.guild.fetch_channel(config.find_one({"config":"donologchannel"})["channel"])
            await log_channel.send(embed=log_embed)
        except:await interaction.channel.send("There is an error logging this note!")

    @app_commands.command(name="add-item", description=".")
    async def add_item(self, interaction:discord.Interaction, item_name:str, price:str, emoji:str, itemid:str):
        await interaction.response.defer()
        price_parsed = number_parse(price)
        img_url = f"https://cdn.discordapp.com/emojis/{emoji.split(':')[2].rstrip('>')}"
        itemid = itemid.lower()
        items.insert_one({
            "itemid":itemid,
            "name":item_name,
            "emote":emoji,
            "price":price_parsed,
            "url":img_url
        })

        amount = parse("1 "+itemid)["amount"]
        conv_str = parse("1 "+itemid)["conversion"]
        if len(conv_str)>1024:
            conv_str = conv_str[0:1020]+"..."
        embed = discord.Embed(color = discord.Color.random(), title="Donation Value")
        embed.set_thumbnail(url=img_url)
        embed.add_field(name="Conversion", value = conv_str, inline = False)
        embed.add_field(name="Total Value", value = f"`⏣ {format(amount)}`")
        embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url)
        await interaction.followup.send(embed=embed)


async def setup(bot:commands.Bot):
    await bot.add_cog(Donation(bot), guilds=[discord.Object(979221209680068608),discord.Object(823905036186419201)])