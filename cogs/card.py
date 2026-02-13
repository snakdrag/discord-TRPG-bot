#cogs.card.py
from core import *
from core import constant

_FEATURE = constant.CARD

class CARD_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(name=constant.SET,description=constant.SET+_FEATURE)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        description=constant.DESCRIPTION,
        show=constant.SHOW,
        include=constant.INCLUDE,
    )
    @app_commands.autocomplete(
        include=Autocomplete.atc_card_guild_id,
    )
    async def _set(
        self,
        interaction:discord.Interaction,
        description:str,
        show:bool=False,
        include:str=None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            await step.bulk_write(UpdateOne(_FEATURE,{"$set":{
                constant.DESCRIPTION:description,
                constant.SHOW:show if include is not None else False,
                constant.INCLUDE:int(include) if include.isdigit() else step.guild_id, 
            }},upsert=True,guild_id=step.guild_id))
            return await step.send(f"{constant.DESCRIPTION}:\n{description}")
        except AppError as e:await step.send(e)
        except Exception as e:raise e

    @_group.command(
        name=constant.ATTRIBUTE+constant.ADD,
        description=_FEATURE+constant.ATTRIBUTE+constant.ADD,
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        name=constant.NAME,
        value=constant.VALUE,
        description=constant.DESCRIPTION,
    )
    async def _attribute_add(
        self,
        interaction:discord.Interaction,
        name:str,
        value:str,
        description:str=None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            num = Count_result.dnd_result(value)[1]
            doc = await step.find_one(_FEATURE,guild_id=step.guild_id)
            if doc and doc.get(constant.GUILD_ID,step.guild_id)!=step.guild_id:
                return await step.send(f"資料引入中，禁止使用")
            result = (await step.bulk_write(UpdateOne(_FEATURE,{"$push":{constant.ATTRIBUTE:{
                constant.NAME:name,constant.VALUE:value,
                constant.DESCRIPTION:description}}},upsert=True,guild_id=step.guild_id,
                query_override={f"{constant.ATTRIBUTE}.{constant.NAME}":{"$ne":name}})))[_FEATURE]
            if not result.upserted_count:return await step.send(f"{name} {constant.EXIST}")
            await step.bulk_write(UpdateMany(constant.RACE,{"$push":{constant.ATTRIBUTE:{
                constant.NAME:name,constant.VALUE:value,
                constant.DESCRIPTION:description}}},upsert=True,guild_id=step.guild_id,
                query_override={f"{constant.ATTRIBUTE}.{constant.NAME}":{"$ne":name}}))
            guilds = await step.db.find(_FEATURE,{constant.INCLUDE:step.guild_id})
            guilds_ids = [guild[constant.GUILD_ID] for guild in guilds]
            guilds_ids.append(step.guild_id)
            await step.db.bulk_write(*[UpdateMany(constant.PLAYER,{
                "$push":{constant.BASIC:num,constant.MAX:num,constant.NOW:num}},
                guild_id=guild_id)for guild_id in guilds_ids])
            return await step.send(
                f"{name}:{value} {constant.ADD}{constant.SUCCESS}\n{constant.DESCRIPTION}:\n{description}")
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(
        name=constant.ATTRIBUTE+constant.CHANGE,
        description=_FEATURE+constant.ATTRIBUTE+constant.CHANGE,
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        target=constant.ATTRIBUTE,
        name=constant.NAME,
        value=constant.VALUE,
        description=constant.DESCRIPTION,
    )
    @app_commands.autocomplete(
        target=Autocomplete.atc_card_attribute_name,
    )
    async def _attribute_change(
        self,
        interaction:discord.Interaction,
        target:str,
        name:str=None,
        value:str=None,
        description:str=None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            Count_result.dnd_result(value)[1]
            doc = await step.find_one(_FEATURE,guild_id=step.guild_id)
            if doc and doc.get(constant.GUILD_ID,step.guild_id)!=step.guild_id:
                return await step.send(f"資料引入中，禁止使用")
            _query = {}
            def _quick_query(key_,value_):
                if value_:_query[f"{constant.ATTRIBUTE}.$.{key_}"]=value_
            _quick_query(constant.NAME,name)
            _quick_query(constant.VALUE,value)
            _quick_query(constant.DESCRIPTION,description)
            if not _query:return await step.send("你想改什麼？")
            result = (await step.bulk_write(UpdateOne(_FEATURE,{"$set":_query},query_override={
                f"{constant.ATTRIBUTE}.{constant.NAME}":target},guild_id=step.guild_id)))[_FEATURE]
            if result.modified_count == 0:return await step.send(f"{target} {constant.NOT}{constant.EXIST}")
            await step.bulk_write(UpdateMany(constant.RACE,{"$set":_query},query_override={
                f"{constant.ATTRIBUTE}.{constant.NAME}":target},guild_id=step.guild_id))
            return await step.send(f"{name or target} {constant.CHANGE}{constant.SUCCESS}")
        except AppError as e:return await step.send(e)
        except Exception as e:raise e
    
    @_group.command(
        name=constant.ATTRIBUTE+constant.DELETE,
        description=_FEATURE+constant.ATTRIBUTE+constant.DELETE,
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        target=constant.ATTRIBUTE,
    )
    @app_commands.autocomplete(
        target=Autocomplete.atc_card_attribute_name,
    )
    async def _attribute_delete(
        self,
        interaction:discord.Interaction,
        target:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            doc = await step.find_one(_FEATURE,guild_id=step.guild_id)
            if doc and doc.get(constant.GUILD_ID,step.guild_id)!=step.guild_id:
                return await step.send(f"資料引入中，禁止使用")
            attributes:list[dict] = (await step.find_one(_FEATURE)).get(constant.ATTRIBUTE,[])
            idx = next((i for i,a in enumerate(attributes) if a[constant.NAME] == target),None)
            if idx is None:return await step.send(f"{target} {constant.NOT}{constant.EXIST}")
            await step.bulk_write(
                UpdateOne(_FEATURE,{"$pull":{constant.ATTRIBUTE:{
                    constant.NAME:target}}},guild_id=step.guild_id),
                UpdateMany(constant.RACE,{"$pull":{constant.ATTRIBUTE:{
                    constant.NAME:target}}},guild_id=step.guild_id))
            guilds = await step.db.find(_FEATURE,{constant.INCLUDE:step.guild_id})
            guilds_ids = [guild[constant.GUILD_ID] for guild in guilds]
            guilds_ids.append(step.guild_id)
            await step.db.bulk_write(
                *[UpdateMany(constant.PLAYER,{"$unset":{
                    f"{constant.BASIC}.{idx}":1,f"{constant.MAX}.{idx}":1,f"{constant.NOW}.{idx}":1}},
                    guild_id=guild_id) for guild_id in guilds_ids],
                *[UpdateMany(constant.PLAYER,{"$pull":{
                    constant.BASIC:None,constant.MAX:None,constant.NOW:None}},
                    guild_id=guild_id) for guild_id in guilds_ids])
            return await step.send(f"{constant.DELETE} {constant.SUCCESS}")
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(
        name=constant.ATTRIBUTE+constant.SHOW,
        description=constant.ATTRIBUTE+constant.SHOW,
    )
    @app_commands.describe(
        target=constant.ATTRIBUTE,
    )
    @app_commands.autocomplete(
        target=Autocomplete.atc_card_attribute_name,
    )
    async def _attribute_show(
        self,
        interaction:discord.Interaction,
        target:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        doc = await step.find_one(_FEATURE,guild_id=step.guild_id)
        attributes:list[dict] = doc.get(constant.ATTRIBUTE,[])
        if not attributes:return await step.send(f"{target} {constant.NOT}{constant.EXIST}")
        attribute = next((attr for attr in attributes if attr.get(constant.NAME)==target),{})
        name = attribute.get(constant.NAME,UNKNOWN)
        value = attribute.get(constant.VALUE,UNKNOWN)
        description = attribute.get(constant.DESCRIPTION,UNKNOWN)
        return await step.send(f"{name}:{value}\n{constant.DESCRIPTION}:\n{description}")

    @_group.command(name=constant.SHOW,description=constant.SHOW+_FEATURE)
    @app_commands.describe(
        guild=constant.GUILD,
    )
    @app_commands.autocomplete(
        guild=Autocomplete.atc_card_guild_id,
    )
    async def _show(
        self,
        interaction:discord.Interaction,
        guild:str=None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        embed = await step.card_show(guild_id=int(guild) if guild and guild.isdigit() else step.guild_id)
        return await step.send(embed=embed)

async def setup(bot:Bot):await bot.add_cogs(CARD_MAIN)