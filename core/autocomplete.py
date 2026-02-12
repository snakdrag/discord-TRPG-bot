#core.autocomplete.py
from . import constant as _const
from .check import *

def _filter_choices(
        current:str,
        data_list:list[dict],
        *,
        name_place:str=_const.NAME,
        value_place:str=_const.NAME,
        function_for_name=str,
        function_for_value=str,
    )->list[app_commands.Choice]:
    current_lower,choices,i=current.lower(),[],0
    if not data_list:return []
    for _d in data_list:
        name = str(function_for_name(_d.get(name_place,UNKNOWN)))
        value = function_for_value(_d.get(value_place,UNKNOWN))
        if current_lower in name.lower() or current_lower in str(value).lower():
            i+=1;choices.append(app_commands.Choice(name=name,value=value))
        if i >= 25:break
    return choices

class Autocomplete(Check):
    def __init__(self,bot:Bot):super().__init__(bot)
    async def _atc_trait_by_user(self,feature:str,interaction:discord.Interaction,current:str):
        docs = await self.db.find(feature,query_override={
            _const.GUILD_ID:interaction.guild_id,f"{_const.DATA}.{interaction.user.id}":{"$exists":True}})
        return _filter_choices(current,docs)
    def _get_guild_name(self,guild_id:int):
        guild = self.bot.get_guild(guild_id)
        return guild.name if guild else UNKNOWN
    async def atc_card_attribute_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,(await self.db.find_one(
        _const.CARD,guild_id=interaction.guild_id)).get(_const.ATTRIBUTE,[]))
    async def atc_card_guild_id(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:
        query = {_const.SHOW:True,_const.ID:{"$ne":interaction.guild_id}}
        if current:query["$or"] = [{_const.NAME:{"$regex":current,"$options":"i"}},{
            _const.ID:{"$regex":current,"$options":"i"}}]
        data = await self.db.card.find(
            query,{_const.ID:1,_const.NAME:1}).limit(25).to_list(length=25)
        if not data:return []
        return [app_commands.Choice(name=d[_const.NAME],value=str(d[_const.ID]))for d in data]
    async def atc_role_guild_id(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,
        await self.db.aggregate(_const.PLAYER,[{"$match":{_const.USER_ID:interaction.user.id}},{
        "$group":{_const.ID:f"${_const.GUILD_ID}"}}]),name_place=_const.ID,
        value_place=_const.ID,function_for_name=self._get_guild_name,function_for_value=str)
    async def atc_role_target(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:
        current_lower,choices,i = current.lower(),[],0
        for res in await self.db.aggregate(_const.PLAYER,[{"$match":{
            _const.GUILD_ID:interaction.guild_id}},{"$group":{_const.ID:{
                _const.GROUP:f"${_const.GROUP}",_const.USER_ID:f"${_const.USER_ID}",
                _const.NAME:f"${_const.NAME}"}}}]):
            res:dict[str,dict]
            group = res[_const.ID].get(_const.GROUP,UNKNOWN)
            role = res[_const.ID].get(_const.NAME,UNKNOWN)
            user_id = res[_const.ID].get(_const.USER_ID,UNKNOWN)
            name = f"{group}--{role}--{await self.bot.get_user_name(user_id)}"
            value = f"{group}--{role}--{user_id}"
            if current_lower in name.lower() or current_lower in value.lower():
                i+=1;choices.append(app_commands.Choice(name=name,value=value))
                if i>=25:break
        return choices
    async def atc_role_player(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:
        current_lower,choices,i = current.lower(),[],0
        for res in await self.db.aggregate(_const.PLAYER,[{"$match":{
            _const.GUILD_ID:interaction.guild_id}},{"$group":{_const.ID:{
                _const.USER_ID:f"${_const.USER_ID}",
                _const.NAME:f"${_const.NAME}"}}}]):
            res:dict[str,dict]
            role = res[_const.ID].get(_const.NAME,UNKNOWN)
            user_id = res[_const.ID].get(_const.USER_ID,UNKNOWN)
            name = f"{role}--{await self.bot.get_user_name(user_id)}"
            value = f"{role}--{user_id}"
            if current_lower in name.lower() or current_lower in value.lower():
                i+=1;choices.append(app_commands.Choice(name=name,value=value))
                if i>=25:break
        return choices
    async def atc_role_group(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,
        await self.db.aggregate(_const.PLAYER,[{"$match":{
            _const.GUILD_ID:interaction.guild_id}},{
                "$group":{_const.ID:f"${_const.GROUP}"}}]),
        name_place=_const.ID,value_place=_const.ID)
    async def atc_role_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,
        await self.db.find(_const.ROLE,user_id=interaction.user.id))
    async def atc_race_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,
        await self.db.find(_const.RACE,guild_id=interaction.guild_id))
    async def atc_item_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,
        await self.db.find(_const.ITEM,guild_id=interaction.guild_id))
    async def atc_skill_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,
        await self.db.find(_const.SKILL,guild_id=interaction.guild_id))
    async def atc_state_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return _filter_choices(current,
        await self.db.find(_const.STATE,guild_id=interaction.guild_id))
    async def atc_dice_mode(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return [choice for choice in [
        app_commands.Choice(name=Count_result.coc7e,value=Count_result.coc7e),
        app_commands.Choice(name=Count_result.coc6e,value=Count_result.coc6e),
        app_commands.Choice(name=Count_result.dnd,value=Count_result.dnd)]]
    async def atc_role_item_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return await self._atc_trait_by_user(_const.ITEM,interaction,current)
    async def atc_role_skill_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return await self._atc_trait_by_user(_const.SKILL,interaction,current)
    async def atc_role_state_name(self,interaction:discord.Interaction,current:str
    )->list[app_commands.Choice[str]]:return await self._atc_trait_by_user(_const.STATE,interaction,current)
