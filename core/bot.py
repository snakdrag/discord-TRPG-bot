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
            if (isinstance(error,app_commands.MissingPermissions) or 
                isinstance(error,app_commands.CheckFailure)):
                msg = "權限不足"
                if interaction.response.is_done():return await interaction.followup.send(msg,ephemeral=True)
                else:return await interaction.response.send_message(msg,ephemeral=True)
            command_name = interaction.command.name if interaction.command else UNKNOWN
            await self.notify_managers((
                f"""**app_command_error**
                - **command**: `/{command_name}`
                - **user**: {interaction.user.mention}
                ```python\n{"".join(_traceback.format_exception(
                    type(error),error,error.__traceback__))}\n```"""))
            try:
                msg = "非預期錯誤發生，已通知開發者"
                if interaction.response.is_done():return await interaction.followup.send(msg,ephemeral=True)
                else:return await interaction.response.send_message(msg,ephemeral=True)
            except Exception as e:print(f"can't reply error to user: {e}")
    async def on_error(
            self,
            event_method:str,
            *args:Any,
            **kwargs:Any,
        ):return await self.notify_managers((
        f"""**on_message_error**: `{event_method}`
        - **args**: `{args}`
        ```python\n{_traceback.format_exc()}\n```"""))
    async def notify_managers(self,content:str):
        contents = [content[:1999]]
        content = content[1999:]
        while len(content)>2000:
            contents.append(content[:1999])
            content = content[1999:]
        for user in self.managers:
            await asyncio.gather(*[user.send(cont) for cont in contents],return_exceptions=True)
    async def get_guild_name(self,guild_id:int):
        if not isinstance(guild_id,int):return UNKNOWN
        guild = self.get_guild(guild_id) or await self.fetch_guild(guild_id)
        return guild.name if guild else UNKNOWN
    async def get_user_name(self,user_id:int):
        if not isinstance(user_id,int):return UNKNOWN
        user = await self.get_target_user(user_id=user_id)
        return user.name if user else UNKNOWN
    async def get_target_user(self,user_id):
        return self.get_user(user_id) or await self.fetch_user(user_id)
    def add_commands(self,*commands):
        for command in commands:self.tree.add_command(command)
