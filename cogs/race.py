#cogs.race.py
from core import *
from core import constant

_FEATURE = constant.RACE
_FEATURE_AUTOCOMPLETE = Autocomplete.atc_race_name

class RACE_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(name=constant.ADD,description=constant.ADD+_FEATURE)
    @Check.is_gm()
    @app_commands.describe(
        name=constant.NAME,
        description=constant.DESCRIPTION,
    )
    async def _add(
        self,
        interaction:discord.Interaction,
        name:str,
        description:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            if await step.find_one(_FEATURE,name=name,guild_id=step.guild_id):
                raise AppError(f"{name} {constant.EXIST}")
            await step.race_save(name,description)
            embed = await step.race_show(name)
            return await step.send(embed=embed)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(
        name=constant.ATTRIBUTE+constant.CHANGE,
        description=_FEATURE+constant.ATTRIBUTE+constant.CHANGE,
    )
    @Check.is_gm()
    @app_commands.describe(
        target = _FEATURE,
        attribute = constant.ATTRIBUTE,
        value = constant.VALUE,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
        attribute = Autocomplete.atc_card_attribute_name,
    )
    async def _attribute_change(
        self,
        interaction:discord.Interaction,
        target:str,
        attribute:str,
        value:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            Count_result.dnd_result(value)
            attributes = (await step.find_one(
                constant.RACE,guild_id=step.guild_id,name=target)).get(constant.ATTRIBUTE,[])
            base_field = [attr[constant.NAME] for attr in attributes]
            if attribute not in base_field:
                raise AppError(f"{attribute} {constant.NOT}{constant.EXIST}")
            attributes[base_field.index(attribute)][constant.VALUE] = value
            await step.race_save(None,None,attributes,target)
            return await step.send(embed=await step.race_show(target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.CHANGE,description=constant.CHANGE+_FEATURE)
    @Check.is_gm()
    @app_commands.describe(
        target = _FEATURE,
        name = constant.NAME,
        description = constant.DESCRIPTION,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
    )
    async def _change(
        self,
        interaction:discord.Interaction,
        target:str,
        name:str = None,
        description:str = None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            await step.race_save(name,description,None,target)
            return await step.send(embed=await step.race_show(target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.DELETE,description=constant.DELETE+_FEATURE)
    @Check.is_gm()
    @app_commands.describe(
        target = _FEATURE,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
    )
    async def _delete(
        self,
        interaction:discord.Interaction,
        target:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            result = await step.delete(feature=_FEATURE,name=target)
            if result.deleted_count:return await step.send(constant.DELETE+constant.SUCCESS)
            else:return await step.send(constant.DELETE+constant.FAILED)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.SHOW,description=constant.SHOW+_FEATURE)
    @app_commands.describe(
        target = _FEATURE,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
    )
    async def _show(
        self,
        interaction:discord.Interaction,
        target:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:return await step.send(embed=await step.race_show(target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

async def setup(bot:Bot):await bot.add_cog(RACE_MAIN(bot))