#core.plugin.py
from . import constant as _const
from .command import *
from itertools import chain as _chain

class Message(Addon):
    def __init__(
            self, 
            db:DataBase, 
            message:discord.Message,
    ):
        self.message = message
        self.message_id = message.id
        self.thread,self.webhook_channel = (
            (message.channel,message.channel.parent)
            if isinstance(message.channel,discord.Thread) and message.channel.parent
            else (MISSING,message.channel))
        self.webhook = None
        super().__init__(
            db=db, 
            guild_id=message.guild.id if message.guild else None, 
            user_id=message.author.id, 
            send_function=message.channel.send,
        )
    def check_is_bot(self):return self.message.author.bot
    def check_in_guild(self):return self.message.guild
    async def webhook_get(self):
        me_id = self.message.guild.me.id
        webhooks:list[discord.Webhook] = await self.webhook_channel.webhooks()
        for webhook in webhooks:
            if webhook.user.id == me_id:return webhook
        self.webhook:discord.Webhook = await self.webhook_channel.create_webhook(name=WEBHOOK)
        return self.webhook
    async def webhook_send(self,content:str,call:str):
        role:dict = await self.db.role.find_one({_const.CALL:call,_const.USER_ID:self.user_id})
        if not role:return False
        self.webhook = self.webhook or await self.webhook_get()
        message:discord.WebhookMessage = await self.webhook.send(
            content=content,thread=self.thread,wait=True,
            username=role.get(_const.NAME,UNKNOWN),avatar_url=role.get(_const.URL,MISSING))
        await self.message.delete()
        await self.bulk_write(UpdateOne(_const.MESSAGE,{"$set":{
            _const.USER_ID:self.user_id}},upsert=True,ID=message.id,user_id=self.user_id))
        return True
    async def webhook_edit(self,content:str):
        self.webhook = self.webhook or await self.webhook_get()
        await self.webhook.edit_message(
            thread=self.thread,message_id=self.message_id,content=content)
    async def webhook_delete(self):
        self.webhook = self.webhook or await self.webhook_get()
        await self.webhook.delete_message(self.message_id,thread=self.thread)
        await self.bulk_write(DeleteOne(_const.MESSAGE,ID=self.message_id))

class Interaction(Addon):
    def __init__(
            self, 
            interaction:discord.Interaction
    ):
        self.interaction = interaction
        self.bot:Bot = interaction.client
        super().__init__(
            db=self.bot.db, 
            guild_id=interaction.guild_id, 
            user_id=interaction.user.id, 
            send_function=interaction.followup.send,
        )
    async def first_step(
            self,
            *,
            ephemeral:bool=False,
            thinking:bool=False
    ):
        self.ephemeral = ephemeral
        await self.interaction.response.defer(ephemeral=self.ephemeral,thinking=thinking)
        return self.guild_id,self.user_id
    async def player_save(
            self,
            role:str,
            race:str,
    ):
        if race is None:
            docs = await self.find(_const.RACE,guild_id=self.guild_id)
            if docs:doc = docs[int(Count_result.rand_result(0,len(docs)-1,_const.INT)[1])]
            else:doc = {}
            race:str = doc.get(_const.NAME,UNKNOWN)
            attributes:list[dict] = doc.get(_const.ATTRIBUTE,[])
        else:attributes = (await self.find_one(
            _const.RACE,guild_id=self.guild_id,name=race)).get(_const.ATTRIBUTE,[])
        base_value = [Count_result.dnd_result(attr.get(_const.VALUE,"0"))[1] for attr in attributes]
        return (await self.bulk_write(UpdateOne(_const.PLAYER,{"$set":{
            _const.RACE:race,_const.IS_TURN:False,_const.NOW:list(base_value),
            _const.CAN_REACT:False,_const.GROUP:None,_const.MAX:list(base_value),
            _const.BASIC:list(base_value)}},upsert=True,name=role,
            guild_id=self.guild_id,user_id=self.user_id)))[_const.PLAYER]
    async def player_change(
            self,
            role:str,
            name:str,
            ID = None,
    ):
        return (await self.bulk_write(UpdateOne(_const.PLAYER,{"$set":{
            _const.NAME:name}},ID=ID,name=role,guild_id=self.guild_id,user_id=self.user_id),
            *[UpdateMany(feature,{"$set":{
                f"{_const.DATA}.$[elem].{_const.NAME}":name}},
                query_override={f"{_const.DATA}":{"$elemMatch":{_const.USER_ID:self.user_id,_const.NAME:role}}},
                array_filters=[{f"elem.{_const.USER_ID}":self.user_id,f"elem.{_const.NAME}":role}],
                guild_id=self.guild_id)
                for feature in [_const.SKILL,_const.STATE,_const.ITEM]]))[_const.PLAYER]
    async def player_delete(
            self,
            role:str,
    ):
        return (await self.bulk_write(DeleteOne(
            _const.PLAYER,name=role,guild_id=self.guild_id,user_id=self.user_id),*[
                UpdateMany(feature,{"$pull":{_const.DATA:{_const.NAME:role,_const.USER_ID:self.user_id}}})
                for feature in [_const.SKILL,_const.STATE,_const.ITEM]]))[_const.PLAYER]
    async def player_update(
            self,
            role:str,
            ID = None,
    ):
        return await Command(self.db,";".join(
            i.get(_const.PASSIVE_EFFECT,"") for i in _chain.from_iterable(
                await asyncio.gather(*[self.get(f,role) for f in [_const.SKILL,_const.STATE,_const.ITEM]]))
                if i.get(_const.ON,False)),await self.find_one(
                    _const.PLAYER,ID=ID,name=role)).execute()
    async def player_show(
            self,
            role:str,
            ID = None,
            user_id = None,
            guild_id = None,
    ):
        player = await self.find_one(_const.PLAYER,ID=ID,name=role,user_id=user_id,guild_id=guild_id)
        if not player:return MISSING
        skills,states,items = await asyncio.gather(
            self.get(_const.SKILL,role=role),
            self.get(_const.STATE,role=role),
            self.get(_const.ITEM,role=role))
        attributes = await self.find_one(_const.CARD)
        base_field = [attr[_const.NAME] for attr in attributes.get(_const.ATTRIBUTE,[])]
        def _get_stats(key):return to_see_dict(to_dict(player.get(key,[]),base_field))
        def _resolve(lis:list[dict]):
            if isinstance(lis,Exception):return f"[Error: {type(lis).__name__}]"
            if not isinstance(lis,list):return "[]"
            return f"[{", ".join([i[_const.NAME] for i in lis])}]"
        return discord.Embed(
            title=await self.bot.get_guild_name(guild_id),
            description="\n".join([
                f"**{_const.NAME}**: {role}",
                f"**{_const.RACE}**: {player.get(_const.RACE,UNKNOWN)}",
                f"**{_const.BASIC}**: {_get_stats(_const.BASIC)}",
                f"**{_const.MAX}**: {_get_stats(_const.MAX)}",
                f"**{_const.NOW}**: {_get_stats(_const.NOW)}",
                f"**{_const.STATE}**: {_resolve(states)}",
                f"**{_const.SKILL}**: {_resolve(skills)}",
                f"**{_const.ITEM}**: {_resolve(items)}"]),
            color=discord.Color.gold())
    async def show(
            self,
            feature:str,
            thing:str,
            ID:Any=None,
    ):
        doc = await self.find_one(feature,ID=ID,name=thing,guild_id=self.guild_id)
        if not doc:return MISSING
        return discord.Embed(
            title=await self.bot.get_guild_name(self.guild_id),
            description="\n".join([
                f"**{_const.NAME}**: {thing}",
                f"**{_const.DESCRIPTION}**: {doc.get(_const.DESCRIPTION,UNKNOWN)}",
                f"**{_const.PROACTIVE_EFFECT}**: {doc.get(_const.PROACTIVE_EFFECT,None)}",
                f"**{_const.PASSIVE_EFFECT}**: {doc.get(_const.PASSIVE_EFFECT,None)}",
                f"**{_const.TIME}**: {doc.get(_const.TIME,UNKNOWN)}",
                f"**{_const.COST_TURN}**: {doc.get(_const.COST_TURN,UNKNOWN)}",
                f"**{_const.CAN_REACT}**: {doc.get(_const.CAN_REACT,UNKNOWN)}",
                f"**{_const.TARGET_NUM}**: {doc.get(_const.TARGET_NUM,UNKNOWN)}"]),
            color=discord.Color.gold())
    async def card_show(self,guild_id:int=None):
        guild_id = guild_id or self.guild_id
        doc = await self.find_one(_const.CARD,guild_id=guild_id)
        if not doc:return MISSING
        attributes:list[dict[str,str]] = doc.get(_const.ATTRIBUTE,[])
        return discord.Embed(
            title=await self.bot.get_guild_name(guild_id),
            description="\n".join([
                f"**{_const.USING}**: `{await self.bot.get_guild_name(
                    doc.get(_const.GUILD_ID,guild_id))}`",
                "\n".join([f"• **{a[_const.NAME]}**: `{a[_const.VALUE]}`"
                    for a in attributes]) if attributes else None,
                f"**{_const.DESCRIPTION}**: `{doc.get(_const.DESCRIPTION,UNKNOWN)}`"]),
            color=discord.Color.gold())
    async def race_show(self,race:str):
        doc = await self.find_one(_const.RACE,name=race,guild_id=self.guild_id)
        if not doc:return MISSING
        def _easy_to_see(key):return f"**{key}**: `{doc.get(key,UNKNOWN)}`"
        attributes = doc.get(_const.ATTRIBUTE,[])
        base_field = [attr[_const.NAME] for attr in attributes]
        base_value = [attr[_const.VALUE] for attr in attributes]
        return discord.Embed(
            title=await self.bot.get_guild_name(self.guild_id),
            description="\n".join([
                _easy_to_see(_const.NAME),
                _easy_to_see(_const.DESCRIPTION),
                to_see_dict(to_dict(base_value,base_field))]),
            color=discord.Color.gold())
    async def race_save(
            self,
            name:str,
            description:str,
            attributes:list = None,
            old_name:str = None,
        ):
        doc = await self.find_one(_const.CARD,guild_id=self.guild_id)
        if not doc:raise AppError(f"{_const.DATA}{_const.NOT}{_const.EXIST}")
        if doc.get(_const.GUILD_ID,self.guild_id) != self.guild_id:raise AppError(f"Now importing")
        if old_name is None:old_name=name
        elif name is None:name=old_name
        quary = {}
        def _quick_quary(key,value):
            if value is not None:quary[key] = value
        _quick_quary(_const.NAME,name)
        _quick_quary(_const.DESCRIPTION,description)
        _quick_quary(_const.ATTRIBUTE,attributes or doc.get(_const.ATTRIBUTE,[]))
        if not quary:raise AppError(f"{_const.DATA} {_const.NOT} {_const.ENOUGH}")
        return (await self.bulk_write(UpdateOne(_const.RACE,{"$set":quary},
            upsert=True,name=old_name,guild_id=self.guild_id)))[_const.RACE]
    async def update_all_time(
            self,
            role:str,
            reduce_val:int = 1,
            user_id:int = None,
        ):
        user_id = user_id or self.user_id
        return await self.bulk_write(*[UpdateMany(feature,{"$set":{
            f"{_const.DATA}.$[elem].{_const.TIME}":{
                "$max":[0,{"$subtract":[f"$$elem.{_const.TIME}",reduce_val]}]}}},
            query_override={f"{_const.DATA}.{_const.NAME}":role},
            guild_id=self.guild_id,
            array_filters=[{f"elem.{_const.USER_ID}":user_id,f"elem.{_const.NAME}":role}])
            for feature in [_const.SKILL,_const.STATE]],UpdateOne(
                _const.STATE,{"$pull":{_const.DATA:{
                    _const.USER_ID:user_id,_const.NAME:role,_const.TIME:{"$lte":0}}}},
                    guild_id=self.guild_id))
    async def update_single_time(
            self,
            feature:str,
            role:str,
            thing:str,
            value:int,
            user_id:int = None
        ):
        user_id = user_id or self.user_id
        result = await self.bulk_write(UpdateOne(
            feature,{"$set":{f"{_const.DATA}.$[elem].{_const.TIME}":{
                "$max":[0,{"$add":[f"$$elem.{_const.TIME}",value]}]}}},
            query_override={f"{_const.DATA}":{"$elemMatch":{_const.USER_ID:user_id,_const.NAME:role}}},
            array_filters=[{f"elem.{_const.USER_ID}":user_id,f"elem.{_const.NAME}":role}],
            name=thing,guild_id=self.guild_id))
        if feature == _const.ITEM:return (await self.bulk_write(UpdateOne(
            feature,{"$pull":{_const.DATA:{
                _const.USER_ID:user_id,_const.NAME:role,_const.NAME:thing,
                _const.TIME:{"$lte":0}}}},guild_id=self.guild_id)))[feature]
        return result[feature]
    