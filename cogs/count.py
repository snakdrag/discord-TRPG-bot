#cogs.count.py
from core import *
from core import constant

_FEATURE = constant.COUNT

class COUNT_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(name=constant.CACULATOR,description=constant.CACULATOR)
    @app_commands.describe(
        text = constant.COUNT
    )
    async def _calculator(
        self,
        interaction:discord.Interaction,
        text:str,
    ):
        return await interaction.response.send_message(
            f"{interaction.user.mention}\n`{text.strip()} → {Count_result.evaluate(text)}`")

    @_group.command(name=constant.DICE,description=constant.DICE)
    @app_commands.describe(
        mode = constant.MODE,
        value = constant.VALUE,
        description = constant.DESCRIPTION,
        time = constant.TIME,
    )
    @app_commands.autocomplete(
        mode=Autocomplete.atc_dice_mode,
    )
    async def _dice(
        self,
        interaction:discord.Interaction,
        mode:str,
        value:str,
        description:str=None,
        time:int=1
    ):
        time=min(max(time,1),100)
        if mode.startswith(Count_result.coc7e[:3]):
            try:value=Count_result.dnd_result(value)[1]
            except:return await interaction.response.send_message(f"{constant.NOT} {constant.NUM}")
            version = 6 if mode == Count_result.coc6e else 7
            output = f"\n`1D100 ≦ {value}：`\n{"\n".join([
                f"`{i+1}. {Count_result.coc_result(value,version)[0]}`"for i in range(time)])
                if time>1 else f"`{Count_result.coc_result(value,version=version)[0]}`"}"
        elif mode==Count_result.dnd:output = f"\n`{value}：`\n{"\n".join([
            f"`{i+1}. {Count_result.dnd_result(value)[0]}`"for i in range(time)])
            if time>1 else f"`{Count_result.dnd_result(value)[0]}`"}"
        return await interaction.response.send_message(
            f"{interaction.user.mention} {description.strip()if description else""}{output}")

    @_group.command(name=constant.LIST,description=f"{constant.CHOOSE}/{constant.RESORT}")
    @app_commands.describe(
        mode=constant.MODE,
        list="使用空格分隔不同東西",
    )
    async def _list(
        self,
        interaction:discord.Interaction,
        mode:str,
        list:str,
    ):
        return await interaction.response.send_message(f"{interaction.user.mention}\n`[{" ".join(
            list.strip().split())}] → {Count_result.list_result(list.strip().split(),mode)}`")
    @_list.autocomplete("mode")
    async def _list_autocomplete_mode(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return [choice for choice in [
        app_commands.Choice(name=constant.CHOOSE,value=constant.CHOOSE),
        app_commands.Choice(name=constant.RESORT,value=constant.RESORT)]]

    @_group.command(name=constant.CUT,description=constant.CUT+constant.NUM)
    @app_commands.describe(
        num=constant.NUM,
        count=constant.COUNT,
    )
    async def _cuts(
        self,
        interaction:discord.Interaction,
        num:int,
        count:int,
    ):
        return await interaction.response.send_message(
            f"""{interaction.user.mention}\n`{num} → {"+".join(map(str,Count_result.cut_result(num,count)))}`""")

    @_group.command(
        name=constant.RANDOM,
        description=f"{constant.RETURN}{constant.NUM}在兩數之間",
    )
    @app_commands.describe(
        mode = constant.MODE,
        num_a = "num_a",
        num_b = "num_b"
    )
    async def _random(
        self,
        interaction:discord.Interaction,
        mode:str,
        num_a:float,
        num_b:float
    ):return await interaction.response.send_message(
        f"{interaction.user.mention}\n`{Count_result.rand_result(num_a,num_b,mode)[0]}`")
    @_random.autocomplete("mode")
    async def _rand_autocomplete_mode(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return [choice for choice in [
        app_commands.Choice(name=constant.INT,value=constant.INT),
        app_commands.Choice(name=constant.FLOAT,value=constant.FLOAT)]]

async def setup(bot:Bot):await bot.add_cog(COUNT_MAIN(bot))