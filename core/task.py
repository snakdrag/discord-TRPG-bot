#core.task.py
from . import constant as _const
from .model import *
import datetime as _datetime

class Task(Engine):
    def __init__(self,bot:Bot):
        super().__init__(bot)
        self._loop_resolver.start()
    def cog_unload(self):self._loop_resolver.cancel()
    @tasks.loop(minutes=1)
    async def _loop_resolver(self):
        for task in await self.db.find(_const.BATTLE,query_override={
            _const.TIME:{"$lte":_datetime.datetime.now(_datetime.timezone.utc)}}):
            try:await self._process_resolved(task)
            except Exception as e:print(e)
    async def _process_resolved(self,task):
        task_id = task[_const.ID]
        task = await self.db.find_one(_const.BATTLE,ID=task_id)
        if not task: return
        guild_id = task.get(_const.GUILD_ID)
        group = task.get(_const.GROUP)
        attacker_id = task.get(_const.USER_ID)
        attacker_name = task.get(_const.NAME)
        channel_id = task.get(_const.CHANNEL_ID)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:channel = await self.bot.fetch_channel(channel_id)
            except discord.NotFound:return print(f"Channel {channel_id} not found.")
        attacker = await self.db.find_one(
            _const.PLAYER,user_id=attacker_id,
            name=attacker_name,guild_id=guild_id,group=group)
        target_data = task[_const.TARGET]
        target = await self.db.find_one(
            _const.PLAYER,group=group,guild_id=guild_id,
            user_id=target_data[_const.USER_ID],name=target_data[_const.NAME])
        return_text = await Command(self.db,task.get(_const.CMD),attacker,[target]).execute()
        await self.db.bulk_write(DeleteOne(_const.BATTLE,ID=task_id))
        if task.get(_const.COST_TURN):
            turn = await self.next_turn(
                group=group,user_id=attacker_id,
                guild_id=guild_id,role=attacker_name)
            return await channel.send(
                f"{return_text}\n<@{turn[0][_const.USER_ID]}>:**{turn[0][_const.NAME]}**",
                embed=discord.Embed(title=_const.TURN,
                    description="\n".join(
                    [f"{i+1}. **{p[_const.NAME]}**" for i,p in enumerate(turn)]
                ),color=discord.Color.dark_gold()))
        else:return await channel.send(f"{return_text}\n<@{attacker_id}>:**{attacker_name}**")
