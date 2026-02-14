#core.bot.py
from .database import *
import traceback as _traceback

class Bot(commands.Bot):
    def __init__(
            self, 
            command_prefix:str,
            intents:discord.Intents,
            folder:str,
            folder_path:str,
            url:str,
        ):
        super().__init__(
            command_prefix=command_prefix, 
            intents=intents,
        )
        self._folder = folder
        self._folder_path = folder_path
        self.db = DataBase(url=url)
    async def setup_hook(self):
        app_info:discord.AppInfo = await self.application_info()
        self.managers = list(app_info.team.members) if app_info.team else [app_info.owner]
        print(await load_folder(self._folder,self._folder_path,self.load_extension))
        try:print(f"app_command.len:{len(await self.tree.sync())}")
        except Exception as e:print(f"app_command failed: {e}")
        @self.tree.error
        async def on_app_command_error(
            interaction:discord.Interaction,
            error:app_commands.AppCommandError,
        ):
            original_error = getattr(error,"original",error)
            if isinstance(original_error,discord.errors.NotFound) and original_error.code == 10062:return
            if isinstance(error,app_commands.MissingPermissions)\
                or isinstance(error,app_commands.CheckFailure):
                msg = "權限不足"
                try:
                    if interaction.response.is_done():return await interaction.followup.send(msg,ephemeral=True)
                    else:return await interaction.response.send_message(msg,ephemeral=True)
                except:return
            guild = interaction.guild
            if guild:
                try:guild_info = f"[{guild.name}]({(await interaction.channel.create_invite(
                    max_age=86400,max_uses=1,reason="Error reporting")).url})"
                except:guild_info = guild.name
            else:guild_info = "私訊"
            command_name = interaction.command.name if interaction.command else UNKNOWN
            await self.notify_managers((
                f"**app_command_error**\n"
                f"**command**: /{command_name}\n"
                f"**user**: {interaction.user.mention}\n"
                f"**guild**: {guild_info}"
                f"```python\n{"".join(_traceback.format_exception(
                    type(error),error,error.__traceback__))}\n```"))
            try:
                msg = "非預期錯誤發生，已通知開發者"
                if interaction.response.is_done():return await interaction.followup.send(msg,ephemeral=True)
                else:return await interaction.response.send_message(msg,ephemeral=True)
            except:...
    async def on_error(
            self,
            event_method:str,
            *args:discord.Message|commands.Context,
            **kwargs:Any,
        ):
        guild_info = UNKNOWN
        for arg in args:
            if arg.guild:
                try:
                    guild_info = f"[{arg.guild.name}]({(await arg.channel.create_invite(
                        max_age=86400,max_uses=1)).url})"
                    break
                except:guild_info = arg.guild.name
                break
        return await self.notify_managers((
            f"**on_message_error**: {event_method}\n"
            f"**location**: {guild_info}\n"
            f"**args**: {args}\n"
            f"```python\n{_traceback.format_exc()}\n```"))
    async def notify_managers(self,content:str):
        contents = [content[i:i+2000] for i in range(0,len(content),2000)]
        for cont in contents:
            await asyncio.gather(*[user.send(cont) for user in self.managers],return_exceptions=True)
            await asyncio.sleep(0.5)
    async def get_guild_name(self,guild_id:int):
        if not isinstance(guild_id,int):return UNKNOWN
        guild = self.get_guild(guild_id) or await self.fetch_guild(guild_id)
        return guild.name if guild else UNKNOWN
    async def get_user_name(self,user_id:int):
        if not isinstance(user_id,int):return UNKNOWN
        user = await self.get_target_user(user_id=user_id)
        return user.name if user else UNKNOWN
    async def get_target_user(self,user_id:int):
        return self.get_user(user_id) or await self.fetch_user(user_id)
    async def add_cogs(self,*cogs:commands.Cog):
        for cog in cogs:await self.add_cog(cog(self))
    def add_commands(self,*commands:app_commands.Command|app_commands.ContextMenu|app_commands.Group):
        for command in commands:self.tree.add_command(command)
    async def load(self,name:str,*,package:str|None = None):
        try:await self.load_extension(name,package=package)
        except commands.ExtensionAlreadyLoaded:await self.reload_extension(name,package=package)
        except Exception as e:raise e
