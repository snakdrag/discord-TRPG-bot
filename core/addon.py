#core.addon.py
from . import constant as _const
from .engine import *

class Addon:
    def __init__(
            self,
            db:DataBase,
            guild_id:int = None,
            user_id:int = None,
            send_function = None
    ):
        self.db = db
        self.guild_id = guild_id
        self.user_id = user_id
        self._send_function = send_function
        self.ephemeral = MISSING
    async def send(
            self,
            content:str=MISSING,
            *,
            ephemeral:bool = MISSING,
            embed:discord.Embed = MISSING,
    ):
        if self._send_function:
            if embed is MISSING and content is MISSING:content = _const.NOT+_const.DATA
            return await self._send_function(
                content=content,
                ephemeral=ephemeral if ephemeral is not MISSING else self.ephemeral,
                embed=embed,
            )
        else:return
    async def find_one(
            self,
            feature:str,
            query_override:dict = {},
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            default:Any = {},
        )->dict:
        doc = await self.db.find_one(
            feature=feature,
            query_override=query_override,
            ID=ID,
            name=name,
            group=group,
            user_id=user_id or self.user_id,
            guild_id=guild_id or self.guild_id,
            default=default,
        )
        #if not doc:await self.send(f"{_const.DATA}{_const.NOT}{_const.EXIST}")
        return doc
    async def find(
            self,
            feature:str,
            query_override:dict = {},
            *,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            length:int = None,
            sort:list = None,
        ) -> list[dict]:
        docs = await self.db.find(
            feature=feature,
            query_override=query_override,
            name=name,
            group=group,
            user_id=user_id or self.user_id,
            guild_id=guild_id or self.guild_id,
            length=length,
            sort=sort,
        )
        #if not data:await self.send(f"{_const.DATA} {_const.NOT} {_const.EXIST}")
        return docs
    async def bulk_write(
            self,
            *requests:UpdateOne|DeleteOne|UpdateMany|DeleteMany,
    ):
        for r in requests:
            if r.filter_params.get(_const.GUILD_ID) is None:r.filter_params[_const.GUILD_ID] = self.guild_id
            if r.filter_params.get(_const.USER_ID) is None:r.filter_params[_const.USER_ID] = self.user_id
        return await self.db.bulk_write(*requests)
    async def get(
            self,
            feature:str,
            role:str,
            user_id:int = None,
            guild_id:int = None,
    ):
        user_id = user_id or self.user_id
        docs:list[dict] = await self.db.aggregate(feature,[{"$match":{
            _const.GUILD_ID:guild_id or self.guild_id,
            f"{_const.DATA}.{_const.USER_ID}":user_id,
            f"{_const.DATA}.{_const.NAME}":role}},
            {"$project":{_const.NAME:1,_const.DATA:{"$filter":{
                "input":f"${_const.DATA}","as":"item",
                "cond":{"$and":[{"$eq": [f"$$item.{_const.USER_ID}",user_id]},{
                    "$eq":[f"$$item.{_const.NAME}",role]}]}}}}}])
        return [{_const.NAME:doc[_const.NAME],_const.TARGET:doc,
            _const.DATA:doc[_const.DATA][0]}for doc in docs if doc.get(_const.DATA)]
    async def save(
            self,
            feature:str,
            name:str,
            description:str,
            proactive_effect:str,
            passive_effect:str,
            time:str,
            cost_turn:bool,
            can_react:bool,
            target_num:int,
            old_name:str=None,
    ):
        data = await self.find(feature,guild_id=self.guild_id)
        if data and data[0][_const.GUILD_ID] != self.guild_id:raise AppError(f"資料引入中，禁止使用")
        if name is not None:
            if await self.find(_const.PLAYER,name=name,guild_id=self.guild_id):
                raise AppError(_const.NAME+_const.EXIST)
        if old_name is None:old_name=name
        elif name is None:name = old_name
        quary = {_const.GUILD_ID:self.guild_id}
        def _quick_quary(key,value):
            if value is not None:quary[key] = value
        _quick_quary(_const.NAME,name)
        _quick_quary(_const.DESCRIPTION,description)
        _quick_quary(_const.PROACTIVE_EFFECT,proactive_effect)
        _quick_quary(_const.PASSIVE_EFFECT,passive_effect)
        _quick_quary(_const.TIME,time)
        _quick_quary(_const.COST_TURN,cost_turn)
        _quick_quary(_const.CAN_REACT,can_react)
        _quick_quary(_const.TARGET_NUM,target_num)
        if not quary:raise AppError(_const.DATA+_const.NOT+_const.ENOUGH)
        return await self.bulk_write(UpdateOne(feature,{
            "$set":quary},upsert=True,name=old_name,guild_id=self.guild_id))
    async def give(
            self,
            feature:str,
            role:str,
            thing:str,
            about_num:int=1,
            user_id:int=None,
    ):
        user_id = user_id or self.user_id
        doc = await self.find_one(feature=feature,name=thing,guild_id=self.guild_id)
        if not doc:raise AppError(f"{thing}{_const.NOT}{_const.EXIST}")
        about_time = doc.get(_const.TIME,0)
        on = True if feature == _const.STATE else False
        result = await self.bulk_write(UpdateOne(feature,{"$inc":{
            f"{_const.DATA}.$.{_const.NUM}":about_num}},query_override={
                f"{_const.DATA}":{"$elemMatch":{_const.USER_ID:user_id,_const.NAME:role}}},
                name=thing,guild_id=self.guild_id))
        if not result[feature].modified_count:return (await self.bulk_write(UpdateOne(feature,{
            "$push":{_const.DATA:{
                _const.USER_ID:user_id,_const.NAME:role,_const.NUM:about_num,
                _const.TIME:Count_result.dnd_result(about_time)[1],_const.ON:on}}},
                name=thing,guild_id=self.guild_id)))[feature]
        return result[feature]
    async def remove(
            self,
            feature:str,
            role:str,
            thing:str,
            about_num:int=1,
            user_id:int=None,
    ):
        user_id = user_id or self.user_id
        return (await self.bulk_write(
            UpdateOne(feature,{"$inc":{f"{_const.DATA}.$.{_const.NUM}":-about_num}},query_override={
                f"{_const.DATA}":{"$elemMatch":{_const.USER_ID:user_id,_const.NAME:role}}},
                name=thing,guild_id=self.guild_id),
            UpdateOne(feature,{"$pull":{_const.DATA:{
                _const.USER_ID:user_id,_const.NAME:role,_const.NUM:{"$lte":0}}}},
                name=thing,guild_id=self.guild_id)))[feature]
    async def delete(
            self,
            feature:str,
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id: int = None,
            guild_id: int = None,    
    ):
        doc = await self.find_one(
            feature,ID=ID,name=name,group=group,user_id=user_id,guild_id=guild_id)
        if not doc:raise AppError(f"{_const.DATA} {_const.NOT} {_const.EXIST}")
        if doc[_const.GUILD_ID] != self.guild_id:raise AppError(f"資料引入中，禁止使用")
        return (await self.bulk_write(DeleteOne(feature,ID=doc[_const.ID])))[feature]
