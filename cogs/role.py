#cogs.role.py
from core import *
from core import constant

_FEATURE = constant.ROLE
_FEATURE_AUTOCOMPLETE = Autocomplete.atc_role_name

class ROLE_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(name=constant.ADD,description=constant.ADD+_FEATURE)
    @app_commands.describe(
        name = constant.NAME,
        call = constant.CALL,
        img = constant.IMG,
        img_url = constant.URL,
        race = constant.RACE,
    )
    @app_commands.autocomplete(
        race = Autocomplete.atc_race_name,
    )
    async def _add(
        self,
        interaction:discord.Interaction,
        name:str,
        call:str,
        img:discord.Attachment = None,
        img_url:str = None,
        race:str = None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        roles =  await step.find(_FEATURE,user_id=step.user_id)
        if name in [r[constant.NAME] for r in roles]:
            return await step.send(f"{name} {constant.EXIST}")
        if call in [r[constant.CALL] for r in roles]:
            return await step.send(f"{call} {constant.EXIST}")
        if img is not None:url=img.url
        elif img_url is not None:url=img_url
        else:url=str(interaction.user.display_avatar.url)
        await self.db.bulk_write(UpdateOne(_FEATURE,{"$set":{
            constant.NAME:name,constant.CALL:call,constant.URL:url}},
            upsert=True,name=name,user_id=step.user_id))
        await step.player_save(role=name,race=race)
        return await step.send(f"{interaction.user.mention} {name}:{call}")

    @_group.command(name=constant.CHANGE,description=constant.CHANGE+_FEATURE)
    @app_commands.describe(
        target = _FEATURE,
        name = constant.NAME,
        call = constant.CALL,
        img = constant.IMG,
        img_url = constant.URL,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
    )
    async def _change(
        self,
        interaction:discord.Interaction,
        target:str,
        name:str = None,
        call:str = None,
        img:discord.Attachment = None,
        img_url:str = None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        role = await step.find_one(_FEATURE,name=target)
        role_ID = role[constant.ID]
        roles =  await step.find(_FEATURE)
        used_names = {r[constant.NAME] for r in roles if r[constant.ID]!=role_ID}
        used_calls = {r[constant.CALL] for r in roles if r[constant.ID]!=role_ID}
        if name in used_names:return await step.send(f"{name} {constant.EXIST}")
        if call in used_calls:return await step.send(f"{call} {constant.EXIST}")
        if img is not None:url=img.url
        elif img_url is not None:url=img_url
        else:url=role[constant.URL]
        await step.bulk_write(UpdateOne(_FEATURE,{"$set":{
            constant.NAME:name or target,
            constant.CALL:call or role[constant.CALL],
            constant.URL:url}},upsert=True,ID=role_ID,
            name=target,user_id=step.user_id))
        player = await step.find_one(constant.PLAYER,name=target,user_id=step.user_id,guild_id=step.guild_id)
        if name is not None and name != target and player:
            await step.player_change(role=target,name=name,ID=player[constant.ID])
        return await step.send(f"{interaction.user.mention} {name}:{call}")

    @_group.command(name=constant.DELETE,description=constant.DELETE+_FEATURE)
    @app_commands.describe(
        target = _FEATURE
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
        await step.bulk_write(DeleteOne(_FEATURE,name=target,user_id=step.user_id))
        await step.player_delete(role=target)
        return await step.send(constant.DELETE+constant.SUCCESS)

    @_group.command(name=constant.LIST,description=constant.SHOW+_FEATURE+constant.LIST)
    async def _list(
        self,
        interaction:discord.Interaction,
    ):
        step = Interaction(interaction)
        await step.first_step()
        roles = await step.find(_FEATURE,user_id=step.user_id)
        roles_len = len(roles)
        if roles_len == 0:return await step.send(
            f"{interaction.user.mention} {_FEATURE+constant.NOT+constant.EXIST}")
        return await step.send(f"{interaction.user.mention}: {roles_len}\n{"\n".join([
            f"{i}. {_r[constant.NAME]}:{_r[constant.CALL]}"for i,_r in enumerate(roles,1)])}")

    @_group.command(
        name=constant.CARD+constant.SHOW,
        description=constant.SHOW+_FEATURE+constant.CARD,
    )
    @app_commands.describe(
        target = _FEATURE,
        guild = constant.GUILD,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
        guild = Autocomplete.atc_role_guild_id,
    )
    async def _card_show(
        self,
        interaction:discord.Interaction,
        target:str,
        guild:str = None,
    ):
        step = Interaction(interaction)
        guild_id,_ = await step.first_step()
        guild_id = int(guild) if guild is not None and guild.isdigit() else guild_id
        embed = await step.player_show(role=target,guild_id=guild_id)
        return await step.send(embed=embed)
    
    @_group.command(
        name=constant.CARD+constant.RESET,
        description=constant.RESET+_FEATURE+constant.CARD,
    )
    @app_commands.describe(
        target = _FEATURE,
        race = constant.RACE,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
        race = Autocomplete.atc_race_name,
    )
    async def _card_reset(
        self,
        interaction:discord.Interaction,
        target:str,
        race:str = None,
    ):
        step = Interaction(self.db,interaction)
        await step.first_step()
        await step.player_save(role=target,race=race)
        embed = await step.player_show(role=target,user_id=step.user_id,guild_id=step.guild_id)
        return await step.send(embed=embed)

    @_group.command(
        name=constant.CARD+constant.INCLUDE,
        description=constant.INCLUDE+_FEATURE+constant.CARD,
    )
    @app_commands.describe(
        target = _FEATURE,
        guild = constant.GUILD,
    )
    @app_commands.autocomplete(
        target = _FEATURE_AUTOCOMPLETE,
        guild = Autocomplete.atc_role_guild_id,
    )
    async def _card_include(
        self,
        interaction:discord.Interaction,
        target:str,
        guild:str,
    ):
        step = Interaction(self.db,interaction)
        guild_id,_ = await step.first_step()
        guild_id = int(guild) if guild.isdigit() else guild_id
        player = await step.find_one(constant.PLAYER,name=target,guild_id=guild_id)
        await step.player_save(role=target,race=player[constant.RACE])
        embed = await step.player_show(role=target,guild_id=guild_id)
        return await step.send(embed=embed)

async def setup(bot:Bot):await bot.add_cog(ROLE_MAIN(bot))