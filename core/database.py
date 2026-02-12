#core.database.py
from . import constant as _const
from .system import *
from pymongo.results import BulkWriteResult as _BWR
from motor.motor_asyncio import AsyncIOMotorCollection as _DB
from motor.motor_asyncio import AsyncIOMotorClient as _Motor

_MODE = _const.MODE
_DATA = _const.DATA

class DataBase:
    def __init__(self,url:str):
        try:
            self.client = _Motor(host=url)
            self.db = self.client[BOTNAME]
            self.message:_DB = self.db.message
            self.battle:_DB = self.db.battle
            self.player:_DB = self.db.player
            self.skill:_DB = self.db.skill
            self.state:_DB = self.db.state
            self.item:_DB = self.db.item
            self.card:_DB = self.db.card
            self.race:_DB = self.db.race
            self.role:_DB = self.db.role
            self.rule:_DB = self.db.rule
            self._registry:dict[str,dict[str,_DB|list[str]]] = {
                _const.MESSAGE:{_DATA:self.message,_MODE:[_const.USER_ID]},
                _const.BATTLE:{_DATA:self.battle,_MODE:[_const.GUILD_ID,_const.GROUP]},
                _const.PLAYER:{_DATA:self.player,_MODE:[
                    _const.GUILD_ID,_const.USER_ID,_const.NAME,_const.GROUP]},
                _const.SKILL:{_DATA:self.skill,_MODE:[_const.USING_ID,_const.NAME]},
                _const.STATE:{_DATA:self.state,_MODE:[_const.USING_ID,_const.NAME]},
                _const.ITEM:{_DATA:self.item,_MODE:[_const.USING_ID,_const.NAME]},
                _const.CARD:{_DATA:self.card,_MODE:[_const.USING_ID]},
                _const.RACE:{_DATA:self.race,_MODE:[_const.USING_ID,_const.NAME]},
                _const.ROLE:{_DATA:self.role,_MODE:[_const.USER_ID,_const.NAME]},
                _const.RULE:{_DATA:self.rule,_MODE:[_const.GUILD_ID]},
            }
            self._allow_db:list = list(self._registry.keys())
        except Exception as e:print(f"{_const.DB}{_const.FAILED}:{e}")
    def close(self):
        if self.client:self.client.close();print(f"{_const.DB}{_const.CLOSE}")
    async def ping(self):
        if not self.client:return False
        try:await self.client.admin.command(command="ping");return True
        except Exception as e:print(e);return False
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
        if feature not in self._allow_db:raise AppError(f"{feature}{_const.NOT}{_const.ALLOW}")
        target_info:dict = self._registry[feature]
        collection:_DB = target_info[_DATA]
        if ID is not None:return await collection.find_one({_const.ID:ID}) or default
        query:dict = {}
        mapping:dict = {
            _const.NAME:name,
            _const.GROUP:group,
            _const.GUILD_ID:guild_id,
            _const.USING_ID:guild_id,
            _const.USER_ID:user_id,
        }
        using_id = (await self.card.find_one({_const.GUILD_ID:guild_id}) or {}).get(_const.USING_ID,guild_id)
        for field in target_info[_MODE]:
            val:Any = mapping.get(field)
            if val is not None:
                if field == _const.USING_ID:query[_const.GUILD_ID] = using_id
                else:query[field] = val
        if query_override:query.update(query_override)
        doc:dict = await collection.find_one(query)
        return doc or default
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
        if feature not in self._allow_db:raise AppError(f"{feature}{_const.NOT}{_const.ALLOW}")
        target_info:dict = self._registry[feature]
        collection:_DB = target_info[_DATA]
        query:dict = {}
        mapping:dict = {
            _const.NAME:name,
            _const.GROUP:group,
            _const.GUILD_ID:guild_id,
            _const.USING_ID:guild_id,
            _const.USER_ID:user_id,
        }
        using_id = (await self.card.find_one({_const.GUILD_ID:guild_id}) or {}).get(_const.USING_ID,guild_id)
        for field in target_info[_MODE]:
            val = mapping.get(field)
            if val is not None:
                if field == _const.USING_ID:query[_const.GUILD_ID] = using_id
                else:query[field] = val
        if query_override:query.update(query_override)
        cursor = collection.find(query)
        if sort:cursor = cursor.sort(sort)
        return await cursor.to_list(length=length)
    async def aggregate(
            self,
            feature:str,
            pipeline:Any,
    ):
        if feature not in self._allow_db:raise AppError(f"{feature}{_const.NOT}{_const.ALLOW}")
        target_info = self._registry[feature]
        collection:_DB = target_info[_DATA]
        return await collection.aggregate(pipeline=pipeline).to_list(length=None)
    async def bulk_write(
            self,
            *requests:UpdateOne|DeleteOne|UpdateMany|DeleteMany,
    ):
        if not requests:return {}
        groups:dict[str,list] = {}
        for req in requests:
            feature = req.feature
            if feature not in self._allow_db:raise AppError(f"{feature}{_const.NOT}{_const.ALLOW}")
            if feature not in groups:groups[feature] = []
            params = req.filter_params
            target_id = params.get(_const.ID)
            if target_id is not None:req.filter = {_const.ID:target_id}
            else:
                guild_id = params.get(_const.GUILD_ID)
                using_id = (await self.card.find_one({
                    _const.GUILD_ID:guild_id}) or {}).get(_const.USING_ID,guild_id)
                params.update(req.query_override)
                for field in self._registry[feature][_MODE]:
                    val = params.get(field)
                    if val is not None:
                        if field == _const.USING_ID:req.filter[_const.GUILD_ID] = using_id
                        else:req.filter[field] = val
            groups[feature].append(req.init())
        features_list = list(groups.keys())
        tasks = []
        for feature in features_list:
            collection:_DB = self._registry[feature][_DATA]
            tasks.append(collection.bulk_write(groups[feature]))
        write_results:list[_BWR] = await asyncio.gather(*tasks)
        return dict(zip(features_list,write_results))
