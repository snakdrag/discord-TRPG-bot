#core.model.py
from .plugin import *

class EditMessageModal(discord.ui.Modal,title="編輯訊息"):
    def __init__(
            self,
            db:DataBase,
            message:discord.Message
        ):
        super().__init__()
        self.new_content = discord.ui.TextInput(
            label="編輯訊息",
            style=discord.TextStyle.paragraph,
            default=message.content or "",
            max_length=2000,
            required=True)
        self.step = Message(db,message)
        self.add_item(self.new_content)
    async def on_submit(self,interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:await self.step.webhook_edit(self.new_content.value)
        except discord.NotFound:await interaction.followup.send("查無訊息.",ephemeral=True)
        except discord.Forbidden:await interaction.followup.send("機器人權限不足",ephemeral=True)
        except Exception as e:raise e
