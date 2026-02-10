#cogs.battle.py
from core import *
from core import constant
import datetime

_FEATURE = constant.BATTLE

class BATTLE_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(name=constant.JOIN,description=constant.JOIN+_FEATURE)
    @app_commands.describe(
        role = constant.ROLE,
        group = constant.GROUP,
    )
    @app_commands.autocomplete(
        role = Autocomplete.atc_role_name,
        group = Autocomplete.atc_role_group,
    )
    async def _join(
        self,
        interaction:discord.Interaction,
        role:str,
        group:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            player = await step.find_one(constant.PLAYER,name=role,user_id=step.user_id,guild_id=step.guild_id)
            if player.get(constant.GROUP) is not None:raise AppError(
                f"{role} {constant.GROUP}{constant.EXIST}:{player[constant.GROUP]}")
            result = (await step.bulk_write(UpdateOne(constant.PLAYER,{"$set":{
                constant.GROUP:group}},ID=player[constant.ID])))[constant.PLAYER]
            if result.modified_count:return await step.send(constant.JOIN+group+constant.SUCCESS)
            else:raise AppError(constant.JOIN+group+constant.FAILED)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.KICK,description=constant.KICK+constant.PLAYER)
    @Check.is_gm()
    @app_commands.describe(
        role = constant.ROLE,
    )
    @app_commands.autocomplete(
        role = Autocomplete.atc_role_target,
    )
    async def _kick(
        self,
        interaction:discord.Interaction,
        role:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            _,player_name,user_id = role.split("--",2)
            player = await step.find_one(constant.PLAYER,name=player_name,user_id=user_id,guild_id=step.guild_id)
            if player.get(constant.GROUP) is None:
                raise AppError(f"{player_name} {constant.GROUP+constant.NOT+constant.EXIST}")
            if player.get(constant.IS_TURN):await self.next_turn(player.get(constant.GROUP),step.guild_id,player)
            result = (await step.bulk_write(UpdateOne(constant.PLAYER,{"$set":{
                constant.GROUP:None,constant.IS_TURN:False,constant.CAN_REACT:False}},
                ID=player[constant.ID])))[constant.PLAYER]
            if result.modified_count:return await step.send(constant.KICK+constant.SUCCESS)
            else:raise AppError(constant.KICK+constant.FAILED)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.LEAVE,description=f"{constant.LEAVE+_FEATURE}")
    @app_commands.describe(
        role = constant.ROLE,
    )
    @app_commands.autocomplete(
        role = Autocomplete.atc_role_name,
    )
    async def _leave(
        self,
        interaction:discord.Interaction,
        role:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            player = await step.find_one(constant.PLAYER,name=role,user_id=step.user_id,guild_id=step.guild_id)
            if player.get(constant.GROUP) is None:
                raise AppError(f"{role} {constant.GROUP+constant.NOT+constant.EXIST}")
            if player.get(constant.IS_TURN):await self.next_turn(player.get(constant.GROUP),step.guild_id,player)
            result = (await step.bulk_write(UpdateOne(constant.PLAYER,{"$set":{
                constant.GROUP:None,constant.IS_TURN:False,constant.CAN_REACT:False}},
                ID=player[constant.ID])))[constant.PLAYER]
            if result.modified_count:return await step.send(constant.LEAVE+constant.SUCCESS)
            else:raise AppError(constant.LEAVE+constant.FAILED)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(
        name=constant.SET,
        description=constant.SET+_FEATURE+constant.ATTRIBUTE,
    )
    @app_commands.describe(
        attribute = constant.ATTRIBUTE,
    )
    @app_commands.autocomplete(
        attribute = Autocomplete.atc_card_attribute_name,
    )
    async def _set(
        self,
        interaction:discord.Interaction,
        attribute:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            doc = await step.find_one(constant.CARD,guild_id=step.guild_id)
            attributes = doc.get(constant.ATTRIBUTE,[])
            base_field = [attr[constant.NAME] for attr in attributes]
            if attribute not in base_field:raise AppError(f"{attribute} {constant.NOT+constant.EXIST}")
            result = (await step.bulk_write(UpdateOne(constant.CARD,{
                constant.BATTLE_ATTRIBUTE:attribute},ID=doc[constant.ID])))[constant.CARD]
            if result.modified_count:return await step.send(constant.ATTRIBUTE+constant.SET+constant.SUCCESS)
            raise AppError(constant.ATTRIBUTE+constant.SET+constant.FAILED)
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.START,description=constant.START+_FEATURE)
    @app_commands.describe(
        group = constant.GROUP,
    )
    @app_commands.autocomplete(
        group = Autocomplete.atc_role_group,
    )
    async def _start(
        self,
        interaction:discord.Interaction,
        group:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            turn = await self.next_turn(group,guild_id=step.guild_id)
            return await step.send(
                f"<@{turn[0][constant.USER_ID]}>:**{turn[0][constant.NAME]}**",
                embed=discord.Embed(title=constant.TURN,
                    description="\n".join(
                    [f"{i+1}. **{p[constant.NAME]}**" for i,p in enumerate(turn)]
                ),color=discord.Color.dark_gold()))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.REACT,description=constant.REACT)
    @app_commands.describe(
        role = constant.ROLE,
        item = constant.ITEM,
        skill = constant.SKILL,
    )
    @app_commands.autocomplete(
        role = Autocomplete.atc_role_name,
        item = Autocomplete.atc_role_item_name,
        skill = Autocomplete.atc_role_skill_name,
    )
    async def _react(
        self,
        interaction:discord.Interaction,
        role:str,
        item:str = None,
        skill:str = None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            player = await step.find_one(constant.PLAYER,name=role)
            if not player.get(constant.CAN_REACT):
                raise AppError(f"{role} {constant.NOT+constant.CAN_REACT}")
            await step.player_update(role,ID=player[constant.ID])
            items,skills = await asyncio.gather(
                step.get(constant.ITEM,role),
                step.get(constant.SKILL,role))
            items_name = [it[constant.NAME] for it in items]
            skills_name = [sk[constant.NAME] for sk in skills]
            if item and item not in items_name:
                raise AppError(f"{role}:{item} {constant.NOT+constant.EXIST}")
            if skill and skill not in skills_name:
                raise AppError(f"{role}:{skill} {constant.NOT+constant.EXIST}")
            t_item:dict = items[items_name.index(item)].get(constant.TARGET) if item else {}
            t_skill:dict = skills[skills_name.index(skill)].get(constant.TARGET) if skill else {}
            if t_item.get(constant.COST_TURN) and t_skill.get(constant.COST_TURN):
                raise AppError(
                    f"無法使用兩個{constant.COST_TURN+constant.REACT}在同個時間")
            group = player.get(constant.GROUP)
            battle_data = await step.find_one(_FEATURE,group=group)
            attacker_id = battle_data.get(constant.USER_ID)
            attacker_name = battle_data.get(constant.NAME)
            attacker = await step.find_one(
                constant.PLAYER,name=attacker_name,user_id=attacker_id)
            if not attacker:raise AppError(f"攻擊者 {constant.NOT} {constant.FIND}")
            cmd = f"{t_item.get(constant.PROACTIVE_EFFECT,"")};{t_skill.get(
                constant.PROACTIVE_EFFECT,"")}"
            await Command(step.db,cmd,player,[attacker]).execute()
            await step.bulk_write(UpdateOne(constant.PLAYER,{
                constant.CAN_REACT:False},ID=player[constant.ID]))
            if not await step.db.find(constant.PLAYER,{
                constant.CAN_REACT:True},guild_id=step.guild_id,group=group):
                return await self._process_resolved(battle_data)
            else:return await step.send(embed=discord.Embed(title=f"{role} {constant.REACT}",
                description=f"{constant.USE}:{skill},{item}",
                color=discord.Color.blue()))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.ACT,description=constant.ACT)
    @app_commands.describe(
        role = constant.ROLE,
        target = constant.TARGET,
        item = constant.ITEM,
        skill = constant.SKILL,
    )
    @app_commands.autocomplete(
        role = Autocomplete.atc_role_name,
        target = Autocomplete.atc_role_target,
        item = Autocomplete.atc_role_item_name,
        skill = Autocomplete.atc_role_skill_name,
    )
    async def _act(
        self,
        interaction:discord.Interaction,
        role:str,
        target:str = None,
        item:str = None,
        skill:str = None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            player = await step.find_one(constant.PLAYER,name=role)
            if not player.get(constant.IS_TURN):
                raise AppError(f"{role} {constant.NOT+constant.CAN_REACT}")
            items,skills = await asyncio.gather(
                step.get(constant.ITEM,role),
                step.get(constant.SKILL,role))
            items_name = [it[constant.NAME] for it in items]
            skills_name = [sk[constant.NAME] for sk in skills]
            if item and item not in items_name:
                raise AppError(f"{role}:{item} {constant.NOT+constant.EXIST}")
            if skill and skill not in skills_name:
                raise AppError(f"{role}:{skill} {constant.NOT+constant.EXIST}")
            t_item:dict = items[items_name.index(item)].get(constant.TARGET) if item else {}
            t_skill:dict = skills[skills_name.index(skill)].get(constant.TARGET) if skill else {}
            if t_item.get(constant.COST_TURN) and t_skill.get(constant.COST_TURN):
                raise AppError(f"無法使用兩個{constant.COST_TURN+constant.REACT}在同個時間")
            cost_turn = True
            if not t_item.get(constant.COST_TURN) and not t_skill.get(constant.COST_TURN):
                cost_turn = False
            group = player.get(constant.GROUP)
            cmd = f"{t_item.get(constant.PROACTIVE_EFFECT,"")};{t_skill.get(
                constant.PROACTIVE_EFFECT,"")}"
            _,target_name,target_id = target.split("--",2)
            if t_item.get(constant.CAN_REACT) or t_skill.get(constant.CAN_REACT):
                await step.bulk_write(UpdateMany(constant.PLAYER,{
                    constant.CAN_REACT:True},ID=player[constant.ID]))
            resolve_time = datetime.datetime.now(
                datetime.timezone.utc)+datetime.timedelta(hours=0.5)
            battle_data = {
                constant.GUILD_ID:step.guild_id,
                constant.USER_ID:step.user_id,
                constant.NAME:role,
                constant.CMD:cmd,
                constant.TARGET:{constant.NAME:target_name,constant.USER_ID:target_id},
                constant.TIME:resolve_time,
                constant.COST_TURN:cost_turn,
                constant.CHANNEL_ID:interaction.channel_id,
                constant.GROUP:group}
            await step.update_all_time(role,1)
            if skill:await step.update_single_time(constant.SKILL,role,skill,t_skill.get(constant.TIME))
            if item:await step.update_single_time(constant.ITEM,role,item,-1)
            if t_item.get(constant.CAN_REACT) or t_skill.get(constant.CAN_REACT):
                return await self._process_resolved(battle_data)
            else:return await step.send(f"等待至 {resolve_time.astimezone().strftime("%Y-%m-%d %H:%M:%S")}")
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

    @_group.command(name=constant.SKIP,description=f"{constant.SKIP+_FEATURE}")
    @app_commands.describe(
        role = constant.ROLE,
    )
    @app_commands.autocomplete(
        role = Autocomplete.atc_role_name,
    )
    async def _skip(
        self,
        interaction:discord.Interaction,
        role:str,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            turn = await self.next_turn((await step.find_one(
                constant.PLAYER,name=role)).get(constant.GROUP),
                step.user_id,step.guild_id,role)
            return await step.send(
                f"<@{turn[0][constant.USER_ID]}>:**{turn[0][constant.NAME]}**",
                embed=discord.Embed(title=constant.TURN,
                    description="\n".join(
                    [f"{i+1}. **{p[constant.NAME]}**" for i,p in enumerate(turn)]
                ),color=discord.Color.dark_gold()))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

async def setup(bot:Bot):await bot.add_cog(BATTLE_MAIN(bot))