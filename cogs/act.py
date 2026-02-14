#cogs.act.py
from core import *
from core import constant

_FEATURE = constant.ACT

class ACT_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(name=constant.DICE,description=constant.DICE)
    @app_commands.describe(
        role=constant.ROLE,
        mode=constant.MODE,
        value=constant.VALUE,
    )
    @app_commands.autocomplete(
        role=Autocomplete.atc_role_name,
        mode=Autocomplete.atc_dice_mode,
    )
    async def _dice(
        self,
        interaction:discord.Interaction,
        role:str,
        mode:str,
        value:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            player = await step.find_one(role)
            if not player:return await step.send(constant.ROLE+constant.NOT+constant.EXIST)
            attributes = (await step.find_one(
                constant.CARD,guild_id=step.guild_id) or {}).get(constant.ATTRIBUTE,[])
            base_field = [attr[constant.NAME] for attr in attributes]
            processed_count=replace_tags(value,get_stats_map(base_field,player))
            display_text,final_result = Count_result.dnd_result(processed_count)
            if mode.startswith(Count_result.coc7e[:3]):
                try:value=Count_result.dnd_result(value)[1]
                except:return await step.send(constant.NOT+constant.NUM)
                version = 6 if mode == Count_result.coc6e else 7
                output = f"\n`1D100 ≦ {final_result}：`\n`{Count_result.coc_result(final_result,version)[0]}`"
            elif mode=="D&D":output = f"\n`{processed_count}：`\n`{display_text}`"
            return await step.send(f"@{role} {output}")
        except AppError as e:return await step.send(e)

    @_group.command(
        name=constant.SET,
        description=constant.SET+constant.RACE+constant.ATTRIBUTE,
    )
    @Check.is_gm()
    @app_commands.describe(
        role=constant.ROLE,
        mode=constant.MODE,
        attribute=constant.ATTRIBUTE,
        value=constant.VALUE,
    )
    @app_commands.autocomplete(
        role = Autocomplete.atc_role_player,
        attribute = Autocomplete.atc_card_attribute_name,
    )
    async def _set(
        self,
        interaction:discord.Interaction,
        role:str,
        mode:str,
        attribute:str,
        value:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        player_name,user_id = role.split("--",1)
        try:
            player = await step.find_one(
                constant.PLAYER,name=player_name,user_id=int(user_id),guild_id=step.guild_id)
            command = f"u.{mode}.{attribute}:*0+{value}"
            await Command(step.db,command,player).execute()
            return await step.send(embed=await step.player_show(player_name,ID=player[constant.ID]))
        except AppError as e:return await step.send(e)
    @_set.autocomplete("mode")
    async def _set_autocomplete_mode(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return [
        app_commands.Choice(name=constant.BASIC,value="B"),
        app_commands.Choice(name=constant.MAX,value="M"),
        app_commands.Choice(name=constant.NOW,value="N")]

async def setup(bot:Bot):await bot.add_cogs(ACT_MAIN)