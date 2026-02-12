#cogs.role_cmd.py
from core import *
from core import constant

class ROLE_CMD(Cog_Extension):

    def __init__(self,bot:Bot):
        super().__init__(bot)
        bot.add_commands(
        app_commands.ContextMenu(
            name=f"{constant.FIND}{constant.ROLE}{constant.USER}",
            callback=self._find_role_user),
        app_commands.ContextMenu(
            name=f"{constant.EDIT}{constant.ROLE}{constant.MESSAGE}",
            callback=self._edit_role_message),
        app_commands.ContextMenu(
            name=f"{constant.DELETE}{constant.ROLE}{constant.MESSAGE}",
            callback=self._delete_role_message))

    async def _find_role_user(
            self,
            interaction:discord.Interaction,
            message:discord.Message
        ):
        step = Interaction(interaction)
        await step.first_step(ephemeral=True)
        if not message.webhook_id:return await step.send(constant.NOT+constant.ROLE+constant.MESSAGE)
        message_data = await step.find_one(constant.MESSAGE,ID=message.id)
        if not message_data:return await step.send(constant.DATA+constant.NOT+constant.FIND)
        user_id = message_data[constant.USER_ID]
        user = await self.bot.get_target_user(user_id=user_id)
        if user:return await step.send(f"{user.mention}")
        else:return await step.send(f"{constant.USER+constant.NOT+constant.FIND} {constant.USER_ID}:{user_id}")
    async def _edit_role_message(
            self,
            interaction:discord.Interaction,
            message:discord.Message
        ):
        step = Interaction(interaction)
        step._send_function = interaction.response.send_message
        step.ephemeral = True
        if not message.webhook_id:return await step.send(constant.NOT+constant.ROLE+constant.MESSAGE)
        message_data = await step.find_one(constant.MESSAGE,ID=message.id)
        if not message_data:return await step.send(constant.DATA+constant.NOT+constant.FIND)
        if interaction.user.id != message_data[constant.USER_ID]:return await step.send("你不是使用者")
        return await interaction.response.send_modal(EditMessageModal(step.db,message))
    async def _delete_role_message(
            self,
            interaction:discord.Interaction,
            message:discord.Message
        ):
        step = Interaction(interaction)
        await step.first_step(ephemeral=True)
        if not message.webhook_id:return await step.send(constant.NOT+constant.ROLE+constant.MESSAGE)
        message_data = await step.find_one(constant.MESSAGE,ID=message.id)
        if not message_data:return await step.send(f"{constant.DATA}{constant.NOT}{constant.FIND}")
        if interaction.user.id != message_data[constant.USER_ID]:return await step.send("你不是使用者")
        try:
            await message.delete()
            await step.bulk_write(DeleteOne(constant.MESSAGE,ID=message.id))
            return await step.send(constant.MESSAGE+constant.DELETE+constant.SUCCESS)
        except discord.NotFound:
            await step.bulk_write(DeleteOne(constant.MESSAGE,ID=message.id))
            return await step.send(constant.MESSAGE+constant.NOT+constant.FIND)
        except discord.Forbidden:
            try:await Message(self,message).webhook_delete()
            except discord.Forbidden:return await step.send("機器人權限不足")
            except Exception as e:raise e

async def setup(bot:Bot):await bot.add_cog(ROLE_CMD(bot))