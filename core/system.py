#core.system.py
from . import constant as _const
from typing import Any
import discord,asyncio
from discord.ext import tasks
from discord.ext import commands
from discord import app_commands
from discord.utils import MISSING
from pymongo import UpdateMany as _UM,UpdateOne as _UO
from pymongo import DeleteMany as _DM,DeleteOne as _DO
from os.path import join as _join
from os.path import exists as _exists
from os.path import dirname as _dirname
from os.path import abspath as _abspath
from os import listdir as _listdir

BOTNAME = "RC_TRPG"
WEBHOOK = "RC_HOOK"
UNKNOWN = "未知"

class AppError(Exception):pass

def get_folder_path(folder:str,file:str):return _join(_dirname(_abspath(file)),folder.replace(".","/"))

async def load_folder(folder:str,folder_path:str,load_function):
    if _exists(folder_path):
        success,fail = [],[]
        for file_name in _listdir(folder_path):
            if file_name.endswith(".py") and not file_name.startswith("__"):
                extension = file_name[:-3]
                try:
                    await load_function(f"{folder}.{extension}")
                    success.append(extension)
                except Exception as e:fail.append(f"{extension}:{e}")
        msg = f"{_const.SUCCESS}{_const.LOAD}:\n{"\n".join(success)}"
        if fail:msg += f"\n{_const.FAILED}{_const.LOAD}:\n{"\n".join(fail)}"
    else:msg = f"{_const.FOLDER}:{folder_path}{_const.NOT}{_const.FIND}"
    return msg

class _UB:
    def __init__(
            self,
            many:bool,
            feature:str,
            update:dict[str,Any],
            upsert:bool = None,
            query_override:dict = {},
            array_filters:list[dict[str,Any]] = None,
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            **kwargs,
        ):
        self.many = many
        self.query_override = query_override
        self.feature = feature
        self.filter = {}
        self.filter_params = {
            _const.ID:ID,
            _const.NAME:name,
            _const.GROUP:group,
            _const.USER_ID:user_id,
            _const.GUILD_ID:guild_id,
        }
        self.update = update
        self.upsert = upsert
        self.array_filters = array_filters
        self.kwargs = kwargs
    def init(self):
        Update = _UM if self.many else _UO
        return Update(
            filter=self.filter,
            update=self.update,
            upsert=self.upsert,
            array_filters=self.array_filters,
            **self.kwargs
        )
class _DB:
    def __init__(
            self,
            many:bool,
            feature:str,
            query_override:dict = {},
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            **kwargs,
        ):
        self.many = many
        self.query_override = query_override
        self.feature = feature
        self.filter = {}
        self.filter_params = {
            _const.ID:ID,
            _const.NAME:name,
            _const.GROUP:group,
            _const.USER_ID:user_id,
            _const.GUILD_ID:guild_id,
        }
        self.kwargs = kwargs
    def init(self):
        Delete = _DM if self.many else _DO
        return Delete(
            filter=self.filter,
            **self.kwargs
        )

class UpdateOne(_UB):
    def __init__(
            self, 
            feature:str,
            update:dict[str,Any],
            upsert:bool = None,
            query_override:dict = {},
            array_filters:list[dict[str,Any]] = None,
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            **kwargs,
        ):
        super().__init__(
            many=False, 
            feature=feature, 
            update=update, 
            upsert=upsert, 
            query_override=query_override, 
            array_filters=array_filters, 
            ID=ID, 
            name=name, 
            group=group, 
            user_id=user_id, 
            guild_id=guild_id, 
            **kwargs
        )
class UpdateMany(_UB):
    def __init__(
            self, 
            feature:str,
            update:dict[str,Any],
            upsert:bool = None,
            query_override:dict = {},
            array_filters:list[dict[str,Any]] = None,
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            **kwargs,
        ):
        super().__init__(
            many=True, 
            feature=feature, 
            update=update, 
            upsert=upsert, 
            query_override=query_override, 
            array_filters=array_filters, 
            ID=ID, 
            name=name, 
            group=group, 
            user_id=user_id, 
            guild_id=guild_id, 
            **kwargs
        )
class DeleteOne(_DB):
    def __init__(
            self, 
            feature:str,
            query_override:dict = {},
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            **kwargs,
        ):
        super().__init__(
            many=False, 
            feature=feature,
            query_override=query_override,
            ID=ID, 
            name=name, 
            group=group, 
            user_id=user_id, 
            guild_id=guild_id, 
            **kwargs
        )
class DeleteMany(_DB):
    def __init__(
            self, 
            feature:str,
            query_override:dict = {},
            *,
            ID:Any = None,
            name:str = None,
            group:str = None,
            user_id:int = None,
            guild_id:int = None,
            **kwargs,
        ):
        super().__init__(
            many=True, 
            feature=feature,
            query_override=query_override,
            ID=ID, 
            name=name, 
            group=group, 
            user_id=user_id, 
            guild_id=guild_id, 
            **kwargs
        )
