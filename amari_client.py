import amari as am

guildid = 823905036186419201

class Amari:

    def __init__(self, userid:int) -> None:
        self.userid = userid
   
    async def level(self):
        client = am.AmariClient("1e84260399e735f839571d2d.47fa83.8549a8f4393dd0270cba6df54d9")
        user:am.objects.User = await client.fetch_user(guildid, self.userid)
        return user.level      
    async def exp(self):
        client = am.AmariClient("1e84260399e735f839571d2d.47fa83.8549a8f4393dd0270cba6df54d9")        
        user:am.objects.User = await client.fetch_user(guildid, self.userid)        
        return user.exp
    async def weekly_exp(self):
        client = am.AmariClient("1e84260399e735f839571d2d.47fa83.8549a8f4393dd0270cba6df54d9")
        user:am.objects.User = await client.fetch_user(guildid, self.userid)        
        return user.weeklyexp
    async def close(self):
        client = am.AmariClient("1e84260399e735f839571d2d.47fa83.8549a8f4393dd0270cba6df54d9")
        await client.close()
        
          