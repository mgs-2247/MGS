import discord, pagination

class Leaderboard(discord.ui.View):
    right_disabled = False
    
    def __init__(self, pagination:pagination.Paginate, interaction:discord.Interaction):
        super().__init__(timeout=10)
        self.pagination = pagination
        self.page:int    = 1
        self.right_disabled = True if pagination.page_count() == 1 else False
        self.inter = interaction

    #left arrow last
    @discord.ui.button(style = discord.ButtonStyle.blurple, emoji="<:left_arrow_last:973401063753400380>", disabled=True, custom_id="LEFT_LAST")
    async def left_last(self, interaction:discord.Interaction, button:discord.ui.Button):
        if self.inter.user.id != interaction.user.id: 
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        self.page = 1
        for item in self.children:
            item:discord.ui.Button
            if item.custom_id in ["LEFT", "LEFT_LAST"]: item.disabled=True
            if item.custom_id in ["RIGHT", "RIGHT_LAST"] and not self.right_disabled: item.disabled = False
        await interaction.response.edit_message(embed = discord.Embed(color=0x2f3136, description=self.pagination.get_page(self.page)).set_footer(text=f"Page {self.page}/{self.pagination.page_count()}"), view=self)

    #left arrow
    @discord.ui.button(style = discord.ButtonStyle.blurple, emoji="<:left_arrow:973255980064313384>", disabled=True, custom_id="LEFT")        
    async def left(self, interaction:discord.Interaction, button:discord.ui.Button):
        if self.inter.user.id != interaction.user.id: 
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        self.page-=1
        for item in self.children:
            item:discord.ui.Button
            if item.custom_id in ["LEFT", "LEFT_LAST"] and self.page == 1: item.disabled = True
            if item.custom_id in ["RIGHT", "RIGHT_LAST"] and not self.right_disabled: item.disabled = False
        await interaction.response.edit_message(embed = discord.Embed(color=0x2f3136, description=self.pagination.get_page(self.page)).set_footer(text=f"Page {self.page}/{self.pagination.page_count()}"), view=self)

    
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji="❌")
    async def close(self, interaction:discord.Interaction, button:discord.ui.Button):
        if self.inter.user.id != interaction.user.id: 
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        for item in self.children:
            item:discord.ui.Button
            item.disabled = True
            item.style = discord.ButtonStyle.gray
        await interaction.response.edit_message(view=self)


    #right arrow
    @discord.ui.button(style = discord.ButtonStyle.blurple, emoji="<:right_arrow:973396293076520970>", disabled=right_disabled, custom_id="RIGHT")        
    async def right(self, interaction:discord.Interaction, button:discord.ui.Button):
        if self.inter.user.id != interaction.user.id: 
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        self.page+=1
        for item in self.children:
            item:discord.ui.Button
            if item.custom_id in ["LEFT", "LEFT_LAST"] and self.page>1: item.disabled = False
            if item.custom_id in ["RIGHT", "RIGHT_LAST"] and self.page == self.pagination.page_count(): item.disabled = True
        await interaction.response.edit_message(embed = discord.Embed(color=0x2f3136, description=self.pagination.get_page(self.page)).set_footer(text=f"Page {self.page}/{self.pagination.page_count()}"), view=self)    
    
    #right last
    @discord.ui.button(style = discord.ButtonStyle.blurple, emoji="<:right_arrow_last:973401112310853642>", disabled = right_disabled, custom_id="RIGHT_LAST")
    async def right_last(self, interaction:discord.Interaction, button:discord.ui.Button):
        if self.inter.user.id != interaction.user.id: 
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        self.page = self.pagination.page_count()
        for item in self.children:
            item:discord.ui.Button
            if item.custom_id in ["LEFT", "LEFT_LAST"] and self.page>1:item.disabled = False
            if item.custom_id in ["RIGHT", "RIGHT_LAST"]: item.disabled = True
        await interaction.response.edit_message(embed = discord.Embed(color=0x2f3136, description=self.pagination.get_page(self.page)).set_footer(text=f"Page {self.page}/{self.pagination.page_count()}"), view=self)
    
    async def disable_right(self):
        if self.pagination.page_count() == 1:
            for item in self.children:
                item:discord.ui.Button
                if item.custom_id in ["RIGHT", "RIGHT_LAST"]:
                    item.disabled = True
        return
    async def on_timeout(self):
        for item in self.children:
            item:discord.ui.Button
            item.disabled = True
            item.style = discord.ButtonStyle.gray
        await self.inter.edit_original_message(view=self)
            
