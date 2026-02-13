#cogs.role_msg.py
from core import *
from core import constant

class ROLE_MSG(Cog_Extension):

    async def _message(self,message:discord.Message):
        step = Message(self.db,message)
        if step.check_is_bot():return
        parts = message.content.split(maxsplit=1)
        if len(parts) != 2:return
        if message.reference and message.reference.message_id:
            try:
                ref_msg = (message.reference.cached_message or 
                    await message.channel.fetch_message(message.reference.message_id))
                reply_prefix = (f"-# > {ref_msg.author.mention} [{(
                    ref_msg.content[:30]+"…"
                    if len(ref_msg.content)>30 
                    else ref_msg.content)}](<{ref_msg.jump_url}>)\n")
            except Exception:reply_prefix = f"-# > {UNKNOWN}\n"
        else:reply_prefix = ""
        await step.webhook_send(f"{reply_prefix}{parts[1]}",parts[0])

    @commands.Cog.listener()
    async def on_message(self,message:discord.Message):return await self._message(message)
    @commands.Cog.listener()
    async def on_message_edit(self,before:discord.Message,after:discord.Message):
        return await self._message(after) if before.content != after.content else None
    @commands.Cog.listener()
    async def on_message_delete(self,message:discord.Message):
        step = Message(self.db,message)
        if not message.webhook_id:return
        return await step.bulk_write(DeleteOne(constant.MESSAGE,ID=step.message_id))

async def setup(bot:Bot):await bot.add_cogs(ROLE_MSG)