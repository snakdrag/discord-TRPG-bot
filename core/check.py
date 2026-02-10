#core.check.py
from . import constant as _const
from .task import *

class Check(Task):
    def __init__(self,bot:Bot):super().__init__(bot)
    @staticmethod
    def is_gm():
        async def predicate(interaction:discord.Interaction)->bool:
            if interaction.user.guild_permissions.manage_guild:return True
            bot:Bot = interaction.client
            rule_data = await bot.db.find_one(_const.RULE,guild_id=interaction.guild_id)
            gm_role_id = rule_data.get(_const.GM,UNKNOWN)
            if not gm_role_id:return False
            return any(role.id == gm_role_id for role in interaction.user.roles)
        return app_commands.check(predicate)
