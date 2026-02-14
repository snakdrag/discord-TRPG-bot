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
            if player.get(constant.GROUP):
                raise AppError(f"{role} {constant.GROUP+constant.EXIST}:{player[constant.GROUP]}")
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
            group,player_name,user_id = role.split("--",2)
            player = await step.find_one(
                constant.PLAYER,name=player_name,user_id=int(user_id),guild_id=step.guild_id)
            if not player:raise AppError(constant.PLAYER+constant.NOT+constant.EXIST)
            if not group:raise AppError(f"{player_name} {constant.GROUP+constant.NOT+constant.EXIST}")
            if player.get(constant.IS_TURN,0):await self.next_turn(group,step.guild_id,player)
            result = (await step.bulk_write(UpdateOne(constant.PLAYER,{"$set":{
                constant.GROUP:None,constant.IS_TURN:0,constant.CAN_REACT:0}},
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
            if not player.get(constant.GROUP):
                raise AppError(f"{role} {constant.GROUP+constant.NOT+constant.EXIST}")
            if player.get(constant.IS_TURN,0):
                await self.next_turn(player.get(constant.GROUP),step.guild_id,player)
            result = (await step.bulk_write(UpdateOne(constant.PLAYER,{"$set":{
                constant.GROUP:None,constant.IS_TURN:0,constant.CAN_REACT:0}},
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
            result = (await step.bulk_write(UpdateOne(constant.CARD,{"$set":{
                constant.BATTLE_ATTRIBUTE:attribute}},ID=doc[constant.ID])))[constant.CARD]
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
            if item is None and skill is None:raise AppError(f"{constant.NOT+constant.ITEM}/{constant.SKILL}")
            player = await step.find_one(constant.PLAYER,name=role)
            if not player.get(constant.CAN_REACT,0):raise AppError(f"{role} {constant.NOT+constant.CAN_REACT}")
            await step.player_update(role,ID=player[constant.ID])
            items,skills = await asyncio.gather(step.get(constant.ITEM,role),step.get(constant.SKILL,role))
            items_name = [it[constant.NAME] for it in items]
            skills_name = [sk[constant.NAME] for sk in skills]
            if item and item not in items_name:raise AppError(f"{role}:{item} {constant.NOT+constant.EXIST}")
            if skill and skill not in skills_name:raise AppError(f"{role}:{skill} {constant.NOT+constant.EXIST}")
            t_item:dict = items[items_name.index(item)].get(constant.TARGET) if item else {}
            t_skill:dict = skills[skills_name.index(skill)].get(constant.TARGET) if skill else {}
            t_item,t_skill = t_item or {},t_skill or {}
            if int(t_item.get(constant.COST_TURN,0)) * int(t_skill.get(constant.COST_TURN,0)):
                raise AppError(f"無法使用兩個{constant.COST_TURN+constant.REACT}在同個時間")
            group = player.get(constant.GROUP)
            battle_data = await step.find_one(_FEATURE,group=group)
            attacker_id = battle_data.get(constant.USER_ID)
            attacker_name = battle_data.get(constant.NAME)
            attacker = await step.find_one(constant.PLAYER,name=attacker_name,user_id=attacker_id)
            if not attacker:raise AppError(f"攻擊者 {constant.NOT} {constant.FIND}")
            cmd = f"{t_item.get(constant.PROACTIVE_EFFECT,"")};{t_skill.get(constant.PROACTIVE_EFFECT,"")}"
            await Command(step.db,cmd,player,[attacker]).execute()
            await step.bulk_write(UpdateOne(constant.PLAYER,{constant.CAN_REACT:0},ID=player[constant.ID]))
            await step.send("立即結算")
            if item:await step.send(embed=await step.show(constant.ITEM,item))
            if skill:await step.send(embed=await step.show(constant.SKILL,skill))
            return await self._process_resolved(battle_data)
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
        target:str,
        item:str = None,
        skill:str = None,
    ):
        step = Interaction(interaction)
        await step.first_step()
        try:
            if item is None and skill is None:raise AppError(f"{constant.NOT+constant.ITEM}/{constant.SKILL}")
            player = await step.find_one(constant.PLAYER,name=role)
            if not player.get(constant.IS_TURN,0):raise AppError(f"{role} {constant.NOT+constant.CAN_REACT}")
            items,skills = await asyncio.gather(step.get(constant.ITEM,role),step.get(constant.SKILL,role))
            items_name = [it[constant.NAME] for it in items]
            skills_name = [sk[constant.NAME] for sk in skills]
            if item and item not in items_name:raise AppError(f"{role}:{item} {constant.NOT+constant.EXIST}")
            if skill and skill not in skills_name:raise AppError(f"{role}:{skill} {constant.NOT+constant.EXIST}")
            t_item:dict = items[items_name.index(item)].get(constant.TARGET) if item else {}
            t_skill:dict = skills[skills_name.index(skill)].get(constant.TARGET) if skill else {}
            t_item,t_skill = t_item or {},t_skill or {}
            if int(t_item.get(constant.COST_TURN,0)) * int(t_skill.get(constant.COST_TURN,0)):
                raise AppError(f"無法使用兩個{constant.COST_TURN+constant.REACT}在同個時間")
            cost_turn = int(t_item.get(constant.COST_TURN,1))+int(t_skill.get(constant.COST_TURN,1))
            group = player.get(constant.GROUP)
            cmd = f"{t_item.get(constant.PROACTIVE_EFFECT,"")};{t_skill.get(constant.PROACTIVE_EFFECT,"")}"
            target_group,target_name,target_id = target.split("--",2)
            if target_group!=group:raise AppError("不在同一場戰鬥")
            if t_item.get(constant.CAN_REACT) or t_skill.get(constant.CAN_REACT):
                await step.bulk_write(UpdateMany(constant.PLAYER,{
                    constant.CAN_REACT:True},ID=player[constant.ID]))
            resolve_time = datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=0.5)
            battle_data = {
                constant.GUILD_ID:step.guild_id,
                constant.USER_ID:step.user_id,
                constant.NAME:role,
                constant.CMD:cmd,
                constant.TARGET:{constant.NAME:target_name,constant.USER_ID:int(target_id)},
                constant.TIME:resolve_time,
                constant.COST_TURN:cost_turn,
                constant.CHANNEL_ID:interaction.channel_id,
                constant.GROUP:group}
            await step.update_all_time(role,1)
            if skill:await step.update_single_time(constant.SKILL,role,skill,t_skill.get(constant.TIME))
            if item:await step.update_single_time(constant.ITEM,role,item,-1)
            if item:await step.send(embed=await step.show(constant.ITEM,item))
            if skill:await step.send(embed=await step.show(constant.SKILL,skill))
            if (int(t_item.get(constant.CAN_REACT,1))-1) * (int(t_skill.get(constant.CAN_REACT,1))-1):
                await step.send("立刻結算")
                return await self._process_resolved(battle_data)
            else:
                await step.bulk_write(UpdateOne(constant.PLAYER,{"$set":{
                    constant.CAN_REACT:1}},name=target_name,group=target_group,
                    guild_id=step.guild_id,user_id=target_id),UpdateOne(_FEATURE,{
                        "$set":battle_data},upsert=True,guild_id=step.guild_id,
                        user_id=step.user_id,name=role,group=group))
                return await step.send(
                    f"<@{target_id}>:{target_name} {constant.CAN_REACT}\n"
                    f"等待至 {resolve_time.astimezone().strftime("%Y-%m-%d %H:%M:%S")}"
                )
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
            player = await step.find_one(constant.PLAYER,name=role)
            can_react = int(player.get(constant.CAN_REACT,0))
            is_turn = int(player.get(constant.IS_TURN,0))
            if can_react + is_turn:
                raise AppError(f"{constant.NOT+constant.IS_TURN}/{constant.CAN_REACT}")
            if can_react:
                await step.send("立刻結算")
                return await self._process_resolved(await self.db.find_one(
                    _FEATURE,group=player.get(constant.GROUP),guild_id=step.guild_id))
            turn = await self.next_turn(player.get(constant.GROUP),step.guild_id,player)
            return await step.send(
                f"<@{turn[0][constant.USER_ID]}>:**{turn[0][constant.NAME]}**",
                embed=discord.Embed(title=constant.TURN,
                    description="\n".join(
                    [f"{i+1}. **{p[constant.NAME]}**" for i,p in enumerate(turn)]
                ),color=discord.Color.dark_gold()))
        except AppError as e:return await step.send(e)
        except Exception as e:raise e

async def setup(bot:Bot):await bot.add_cogs(BATTLE_MAIN)