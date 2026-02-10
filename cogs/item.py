#cogs.item.py
from core import *
from core import constant

_FEATURE = constant.ITEM
_FEATURE_AUTOCOMPLETE = Autocomplete.atc_item_name

class ITEM_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(name=constant.ADD,description=constant.ADD+_FEATURE)
    @Check.is_gm()
    @app_commands.describe(
        name = constant.NAME,
        description = constant.DESCRIPTION,
        proactive_effect = constant.PROACTIVE_EFFECT,
        passive_effect = constant.PASSIVE_EFFECT,
        time = constant.TRAITS_NUM[_FEATURE],
        cost_turn = constant.COST_TURN,
        can_react = constant.CAN_REACT,
        target_num = constant.TARGET_NUM,
    )
    async def _add(
        self,
        interaction:discord.Interaction,
        name:str,
        description:str,
        proactive_effect:str = None,
        passive_effect:str = None,
        time:str = None,
        cost_turn:bool = True,
        can_react:bool = True,
        target_num:str = "1",
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            if time is not None:Count_result.dnd_result(time)
            docs = await step.db.find(constant.PLAYER,guild_id=step.guild_id)
            idx = int(Count_result.rand_result(0,len(
                docs)-1,constant.INT)[1]) if docs else None
            if idx is None:raise AppError(
                f"{constant.ALL} {constant.PLAYER} {constant.NOT} {constant.EXIST}")
            await step.save(feature=_FEATURE,name=name,description=description,
                proactive_effect=proactive_effect,passive_effect=passive_effect,
                time=time,cost_turn=cost_turn,can_react=can_react,target_num=target_num)
            return await step.send(await Command(
                step.db,(proactive_effect or "")+";"+(passive_effect or ""),docs[idx],None,
                False,Count_result.dnd_result(target_num)[1]).execute(),
                embed=await step.show(_FEATURE,name))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.CHANGE,description=f"{constant.CHANGE+_FEATURE}")
    @Check.is_gm()
    @app_commands.describe(
        target = _FEATURE,
        name = constant.NAME,
        description = constant.DESCRIPTION,
        proactive_effect = constant.PROACTIVE_EFFECT,
        passive_effect = constant.PASSIVE_EFFECT,
        time = constant.TRAITS_NUM[_FEATURE],
        cost_turn = constant.COST_TURN,
        can_react = constant.CAN_REACT,
        target_num = constant.TARGET_NUM,
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
        proactive_effect:str = None,
        passive_effect:str = None,
        time:str = None,
        cost_turn:bool = None,
        can_react:bool = None,
        target_num:str = None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            if time is not None:Count_result.dnd_result(time)
            docs = await step.db.find(constant.PLAYER,guild_id=step.guild_id)
            idx = int(Count_result.rand_result(0,len(docs)-1,constant.INT)[1]) if docs else None
            if idx is None:raise AppError(
                f"{constant.ALL} {constant.PLAYER} {constant.NOT} {constant.EXIST}")
            await step.save(feature=_FEATURE,name=name,description=description,
                proactive_effect=proactive_effect,passive_effect=passive_effect,time=time,
                cost_turn=cost_turn,can_react=can_react,target_num=target_num,old_name=target)
            return await step.send(await Command(
                step.db,(proactive_effect or "")+";"+(passive_effect or ""),docs[idx],None,
                False,Count_result.dnd_result(target_num)[1]).execute(),
                embed=await step.show(_FEATURE,name))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.DELETE,description=f"{constant.DELETE+_FEATURE}")
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
            if result.deleted_count:
                return await step.send(constant.DELETE+constant.SUCCESS)
            else:return await step.send(constant.DELETE+constant.FAILED)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.SHOW,description=f"{constant.SHOW+_FEATURE}")
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
        try:return await step.send(embed=await step.show(_FEATURE,target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.GIVE,description=f"{constant.GIVE+_FEATURE}")
    @app_commands.describe(
        target = _FEATURE,
        role = constant.ROLE,
        num = constant.NUM,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
        role = Autocomplete.atc_role_player,
    )
    async def _give(
        self,
        interaction:discord.Interaction,
        target:str,
        role:str,
        num:int,
    ):
        step = Interaction(interaction)
        await step.first_step()
        player,user_id = role.split("--",1)
        try:
            await step.give(_FEATURE,player,target,num,user_id)
            return await step.send(embed=await step.show(_FEATURE,target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.REMOVE,description=f"{constant.REMOVE+_FEATURE}")
    @app_commands.describe(
        target = _FEATURE,
        role = constant.ROLE,
        num = constant.NUM,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
        role = Autocomplete.atc_role_player,
    )
    async def _remove(
        self,
        interaction:discord.Interaction,
        target:str,
        role:str,
        num:int,
    ):
        step = Interaction(interaction)
        await step.first_step()
        player,user_id = role.split("--",1)
        try:
            await step.remove(_FEATURE,player,target,num,user_id)
            return await step.send(embed=await step.show(_FEATURE,target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.MIX,description=f"{constant.MIX+_FEATURE}")
    @app_commands.describe(
        target_a = f"{_FEATURE}_a",
        target_b = f"{_FEATURE}_b",
        name = constant.NAME,
        description = constant.DESCRIPTION,
    )
    @app_commands.autocomplete(
        target_a = _FEATURE_AUTOCOMPLETE,
        target_b = _FEATURE_AUTOCOMPLETE,
    )
    async def _mix(
        self,
        interaction:discord.Interaction,
        target_a:str,
        target_b:str,
        name:str,
        description:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            target_A = await step.find_one(_FEATURE,name=target_a)
            target_B = await step.find_one(_FEATURE,name=target_b)
            proactive_effect=f"{target_A.get(
                constant.PROACTIVE_EFFECT,"")};{target_B.get(constant.PROACTIVE_EFFECT,"")}"
            passive_effect=f"{target_A.get(
                constant.PASSIVE_EFFECT,"")};{target_B.get(constant.PASSIVE_EFFECT,"")}"
            await step.save(feature=_FEATURE,name=name,description=description,
                proactive_effect=proactive_effect if proactive_effect != ";" else None,
                passive_effect=passive_effect if passive_effect != ";" else None,
                time=f"{target_A.get(constant.TIME,"0")}+{target_B.get(constant.TIME,"0")}",
                cost_turn=target_A.get(constant.COST_TURN) or target_B.get(constant.COST_TURN),
                can_react=target_A.get(constant.CAN_REACT) or target_B.get(constant.CAN_REACT),
                target_num=f"({target_A.get(
                    constant.TARGET_NUM,"1")}+{target_B.get(constant.TARGET_NUM,"1")})/2")
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

async def setup(bot:Bot):await bot.add_cog(ITEM_MAIN(bot))