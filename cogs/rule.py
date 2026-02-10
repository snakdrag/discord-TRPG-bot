#cogs.rule.py
from core import *
from core import constant

_FEATURE = constant.RULE

class RULE_MAIN(Cog_Extension):

    _group = app_commands.Group(name=_FEATURE,description=constant.ABOUT+_FEATURE)

    @_group.command(
        name=constant.SET+constant.GM,
        description=constant.SET+constant.GM,
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        gm = constant.GM,
    )
    async def _set_gm(
        self,
        interaction:discord.Interaction,
        gm:discord.Role
    ):
        step = Interaction(interaction)
        await step.first_step()
        result = (await step.bulk_write(UpdateOne(_FEATURE,{
            "$set":{constant.GM:gm.id}},upsert=True,guild_id=step.guild_id)))[_FEATURE]
        if not result.acknowledged:
            return await step.send(f"{constant.GM}{constant.SET}{constant.FAILED}")
        return await step.send(f"{constant.GM}{constant.SET}{constant.SUCCESS}")

async def setup(bot:Bot):await bot.add_cog(RULE_MAIN(bot))