#main.py
from core import discord,commands,Bot,constant
from core.system import load_folder,get_folder_path
from dotenv import load_dotenv as _load_dotenv;_load_dotenv()
from os import getenv as _getenv

folder = "cogs"
folder_path = get_folder_path(folder=folder,file=__file__)

intents = discord.Intents.default()
intents.message_content = True
intents.webhooks = True
intents.members = True
intents.guilds = True

bot = Bot(
    command_prefix="|",
    intents=intents,
    folder=folder,
    folder_path=folder_path,
    url=_getenv("MONGO_URI"),
)

@bot.command(name="restart")
@commands.is_owner()
async def _restart(ctx:commands.Context):
    msg = await load_folder(folder,folder_path,bot.reload_extension)
    return await ctx.send(msg)
@bot.command(name="load")
@commands.is_owner()
async def _load(ctx:commands.Context,*extensions:str):
    for extension in extensions:
        try:
            await bot.load_extension(f"{folder}.{extension}")
            await ctx.send(f"Loaded **{extension}** {constant.SUCCESS}")
        except commands.ExtensionNotFound:await ctx.send(f"**{extension}**{constant.NOT}{constant.FIND}")
        except commands.ExtensionAlreadyLoaded:await ctx.send(f"**{extension}** had loaded.")
        except Exception as e:await ctx.send(f"Load **{extension}** {constant.FAILED}: ```{e}```")
@bot.command(name="unload")
@commands.is_owner()
async def _unload(ctx:commands.Context,*extensions:str):
    for extension in extensions:
        try:
            await bot.unload_extension(f"{folder}.{extension}")
            await ctx.send(f"Unloaded **{extension}** {constant.SUCCESS}")
        except commands.ExtensionNotFound:await ctx.send(f"**{extension}**{constant.NOT}{constant.FIND}")
        except Exception as e:await ctx.send(f"Unload **{extension}** {constant.FAILED}: ```{e}```")
@bot.command(name="reload")
@commands.is_owner()
async def _reload(ctx:commands.Context,*extensions:str):
    for extension in extensions:
        try:
            await bot.reload_extension(f"{folder}.{extension}")
            await ctx.send(f"Loaded **{extension}** {constant.SUCCESS}")
        except commands.ExtensionNotFound:await ctx.send(f"**{extension}**{constant.NOT}{constant.FIND}")
        except Exception as e:await ctx.send(f"Reload **{extension}** {constant.FAILED}: ```{e}```")
@bot.event
async def on_ready():
    if not await bot.db.ping():print("Failed to connect MongoDB")
    print(">>Bot is online<<")

def main():
    try:bot.run(_getenv("token"))
    except Exception as e:print(e)
    finally:bot.db.close()
if __name__ == "__main__":main()
