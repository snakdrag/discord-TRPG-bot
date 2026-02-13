#cogs.trait.py
from core import *
from core import constant

_DOC = {
    constant.SKILL:Autocomplete.atc_skill_name,
    constant.STATE:Autocomplete.atc_state_name,
    constant.ITEM:Autocomplete.atc_item_name,
}

class TRAIT_BASE(Cog_Extension):

    def __init_subclass__(cls,feature:str):

        cls._FEATURE = feature
        feature_autocomplete = _DOC.get(feature)
        cls._group = app_commands.Group(name=feature,description=constant.ABOUT+feature)
        _add = app_commands.Command(
            name=constant.ADD,
            description=constant.ADD+feature,
            callback=cls._add,
        )
        _add = app_commands.describe(
            name = constant.NAME,
            description = constant.DESCRIPTION,
            proactive_effect = constant.PROACTIVE_EFFECT,
            passive_effect = constant.PASSIVE_EFFECT,
            time = constant.TRAITS_NUM[feature],
            cost_turn = constant.COST_TURN,
            can_react = constant.CAN_REACT,
            target_num = constant.TARGET_NUM,
        )(_add)
        
        _change = app_commands.Command(
            name=constant.CHANGE,
            description=constant.CHANGE+feature,
            callback=cls._change,
        )
        _change = app_commands.describe(
            target = feature,
            name = constant.NAME,
            description = constant.DESCRIPTION,
            proactive_effect = constant.PROACTIVE_EFFECT,
            passive_effect = constant.PASSIVE_EFFECT,
            time = constant.TRAITS_NUM[feature],
            cost_turn = constant.COST_TURN,
            can_react = constant.CAN_REACT,
            target_num = constant.TARGET_NUM,
        )(_change)
        _change = app_commands.autocomplete(
            target = feature_autocomplete,
        )(_change)

        _delete = app_commands.Command(
            name=constant.DELETE,
            description=constant.DELETE+feature,
            callback=cls._delete,
        )
        _delete = app_commands.describe(
            target = feature,
        )(_delete)
        _delete = app_commands.autocomplete(
            target = feature_autocomplete,
        )(_delete)

        _show = app_commands.Command(
            name=constant.SHOW,
            description=constant.SHOW+feature,
            callback=cls._show,
        )
        _show = app_commands.describe(
            target = feature,
        )(_show)
        _show = app_commands.autocomplete(
            target = feature_autocomplete,
        )(_show)
        
        _give = app_commands.Command(
            name=constant.GIVE,
            description=constant.GIVE+feature,
            callback=cls._give,
        )
        _give = app_commands.describe(
            target = feature,
            role = constant.ROLE,
            num = constant.NUM,
        )(_give)
        _give = app_commands.autocomplete(
            target = feature_autocomplete,
            role = Autocomplete.atc_role_player,
        )(_give)
        
        _remove = app_commands.Command(
            name=constant.REMOVE,
            description=constant.REMOVE+feature,
            callback=cls._remove,
        )
        _remove = app_commands.describe(
            target = feature,
            role = constant.ROLE,
            num = constant.NUM,
        )(_remove)
        _remove = app_commands.autocomplete(
            target = feature_autocomplete,
            role = Autocomplete.atc_role_player,
        )(_remove)

        _mix = app_commands.Command(
            name=constant.MIX,
            description=constant.MIX+feature,
            callback=cls._mix,
        )
        _mix = app_commands.describe(
            target_a = f"{feature}_a",
            target_b = f"{feature}_b",
            name = constant.NAME,
            description = constant.DESCRIPTION,
        )(_mix)
        _mix = app_commands.autocomplete(
            target_a = feature_autocomplete,
            target_b = feature_autocomplete,
        )(_mix)

        cls._group.add_command(_add)
        cls._group.add_command(_change)
        cls._group.add_command(_delete)
        cls._group.add_command(_give)
        cls._group.add_command(_remove)
        cls._group.add_command(_show)
        cls._group.add_command(_mix)

    @Check.is_gm()
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
            idx = int(Count_result.rand_result(0,len(docs)-1,constant.INT)[1]) if docs else None
            if idx is None:raise AppError(constant.ALL+constant.PLAYER+constant.NOT+constant.EXIST)
            await step.save(feature=self._FEATURE,name=name,description=description,
                proactive_effect=proactive_effect,passive_effect=passive_effect,
                time=time,cost_turn=cost_turn,can_react=can_react,target_num=target_num)
            return await step.send(await Command(
                step.db,(proactive_effect or "")+";"+(passive_effect or ""),docs[idx],None,
                False,Count_result.dnd_result(target_num)[1]).execute(),
                embed=await step.show(self._FEATURE,name))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e
    @Check.is_gm()
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
            if idx is None:raise AppError(constant.ALL+constant.PLAYER+constant.NOT+constant.EXIST)
            await step.save(feature=self._FEATURE,name=name,description=description,
                proactive_effect=proactive_effect,passive_effect=passive_effect,time=time,
                cost_turn=cost_turn,can_react=can_react,target_num=target_num,old_name=target)
            return await step.send(await Command(
                step.db,(proactive_effect or "")+";"+(passive_effect or ""),docs[idx],None,
                False,Count_result.dnd_result(target_num or "1")[1]).execute(),
                embed=await step.show(self._FEATURE,name))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e
    @Check.is_gm()
    async def _delete(
        self,
        interaction:discord.Interaction,
        target:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            result = await step.delete(feature=self._FEATURE,name=target)
            if result.deleted_count:return await step.send(constant.DELETE+constant.SUCCESS)
            else:return await step.send(constant.DELETE+constant.FAILED)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e
    @Check.is_gm()
    async def _give(
        self,
        interaction:discord.Interaction,
        target:str,
        role:str,
        num:int = 1,
    ):
        step = Interaction(interaction)
        await step.first_step()
        player,user_id = role.split("--",1)
        try:
            await step.give(self._FEATURE,player,target,num,user_id)
            return await step.send(embed=await step.show(self._FEATURE,target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e
    @Check.is_gm()
    async def _remove(
        self,
        interaction:discord.Interaction,
        target:str,
        role:str,
        num:int = 1,
    ):
        step = Interaction(interaction)
        await step.first_step()
        player,user_id = role.split("--",1)
        try:
            await step.remove(self._FEATURE,player,target,num,user_id)
            return await step.send(embed=await step.show(self._FEATURE,target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e
    async def _show(
        self,
        interaction:discord.Interaction,
        target:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:return await step.send(embed=await step.show(self._FEATURE,target))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e
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
            target_A = await step.find_one(self._FEATURE,name=target_a)
            target_B = await step.find_one(self._FEATURE,name=target_b)
            proactive_effect=f"{target_A.get(constant.PROACTIVE_EFFECT,"")};{target_B.get(constant.PROACTIVE_EFFECT,"")}"
            passive_effect=f"{target_A.get(constant.PASSIVE_EFFECT,"")};{target_B.get(constant.PASSIVE_EFFECT,"")}"
            await step.save(feature=self._FEATURE,name=name,description=description,
                proactive_effect=proactive_effect if proactive_effect != ";" else None,
                passive_effect=passive_effect if passive_effect != ";" else None,
                time=f"{target_A.get(constant.TIME,"0")}+{target_B.get(constant.TIME,"0")}",
                cost_turn=target_A.get(constant.COST_TURN) or target_B.get(constant.COST_TURN),
                can_react=target_A.get(constant.CAN_REACT) or target_B.get(constant.CAN_REACT),
                target_num=f"({target_A.get(
                    constant.TARGET_NUM,"1")}+{target_B.get(constant.TARGET_NUM,"1")})/2")
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

class STATE_MAIN(TRAIT_BASE,feature=constant.STATE):...
class SKILL_MAIN(TRAIT_BASE,feature=constant.SKILL):...
class ITEM_MAIN(TRAIT_BASE,feature=constant.ITEM):...

async def setup(bot:Bot):await bot.add_cogs(STATE_MAIN,SKILL_MAIN,ITEM_MAIN)