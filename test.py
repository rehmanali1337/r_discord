import discord
import config


user = discord.Client()


@user.event
async def on_ready():
    print('Ready now')
    await user.scrape_members(str(user.guilds[0]), str(user.guilds[0].channels[0]))

user.run(config.token, bot=False)
