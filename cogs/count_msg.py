#cogs.count_msg.py
from core import *
from core import constant

class COUNT_MSG(Cog_Extension):
    
    async def _message(self,message:discord.Message):
        parts = message.content.split(maxsplit=4)
        if len(parts) > 0:command = parts[0].lower()
        else:return
        try:
            if command == r"\ca":
                if len(parts) < 2:return await message.channel.send(
                    f"{message.author.mention} : `{command} <{constant.COUNT}>`")
                text = parts[1]
                return await message.channel.send(
                    f"{message.author.mention}\n`{text.strip()} → "
                    f"{Count_result.evaluate(text)}`")
            if command.startswith("coc"):
                if len(parts) < 2:return await message.channel.send(
                    f"{message.author.mention} : "
                    f"`{command} <{constant.COUNT}> [{constant.DESCRIPTION}] [{constant.TIME}]`")
                try:
                    value = int(parts[1])
                    text = parts[2] if len(parts) > 2 else None
                    time = int(parts[3]) if len(parts) > 3 else 1
                except ValueError:
                    return await message.channel.send(f"{constant.NOT} {constant.NUM}")
                time = min(max(time,1),100)
                version = 6 if command[3:].startswith("6") else 7
                output = f"\n`1D100 ≦ {value}：`\n{"\n".join([
                    f"`{i+1}. {Count_result.coc_result(value,version)[0]}`"for i in range(time)])
                    if time>1 else f"`{Count_result.coc_result(value,version=version)[0]}`"}"
                return await message.channel.send(
                    f"{message.author.mention} {text.strip()if text else""}{output}")
            if command == "dnd":
                if len(parts) < 2:return await message.channel.send(
                    f"{message.author.mention} : "
                    f"`{command} <{constant.COUNT}> [{constant.DESCRIPTION}] [{constant.TIME}]`")
                text = parts[2] if len(parts) > 2 else None
                try:time = int(parts[3]) if len(parts) > 3 else 1
                except ValueError:return await message.channel.send(
                    f"{constant.NOT} {constant.INT} {constant.NUM}")
                time = min(max(time, 1), 100)
                results = [Count_result.dnd_result(parts[1])[0] for _ in range(time)]
                if time>1:output=f"`{parts[1]}：`\n{"\n".join(
                    [f"`{i+1}. {res}`"for i,res in enumerate(results)])}"
                else:output = f"\n`{parts[1]}：`\n`{results[0]}`"
                return await message.channel.send(
                    f"{message.author.mention} {text.strip()if text else""}{output}")
            if command == r"\cut":
                if len(parts) < 3:return await message.channel.send(
                    f"{message.author.mention} : `{command} <{constant.NUM}> <{constant.COUNT}>`")
                try:sum_val,num = int(parts[1]),int(parts[2])
                except ValueError:
                    return await message.channel.send(f"{constant.NOT} {constant.INT} {constant.NUM}")
                if sum_val <= 0 or num <= 0:return await message.channel.send(
                    f"must > 0")
                if num == 1:output = str(sum_val)
                else:output = "+".join(map(str,Count_result.cut_result(sum_val,num)))
                return await message.channel.send(
                    f"{message.author.mention}\n`{sum_val} → {output}`")
            if command == r"\int" or command == r"\float":
                if len(parts) < 3:return await message.channel.send(
                    f"{message.author.mention} : `{command} <num a> <num b>`")
                try:num_a,num_b = float(parts[1]),float(parts[2])
                except ValueError:return await message.channel.send(f"{constant.NOT} {constant.NUM}")
                mode = constant.INT if command == r"\int" else constant.FLOAT
                return await message.channel.send(
                    f"{message.author.mention}\n"
                    f"`{Count_result.rand_result(num_a,num_b,mode)[0]}`")
            if command == constant.CHOOSE or command == constant.RESORT:
                if len(parts) < 2:return await message.channel.send(
                    f"{message.author.mention} : `{command} <thing a> <thing b>...`")
                return await message.channel.send(
                    f"{message.author.mention}\n"
                    f"`[{" ".join(message.content[len(command)+1:].strip().split())}] → "
                    f"{Count_result.list_result(
                        message.content[len(command)+1:].strip().split(),command)}`")
        except AppError as e:return await message.channel.send(e)
        except Exception as e:raise e

    @commands.Cog.listener()
    async def on_message(self,message:discord.Message):return await self._message(message)
    @commands.Cog.listener()
    async def on_message_edit(self,before:discord.Message,after:discord.Message):
        return await self._message(after) if before.content != after.content else None

async def setup(bot:Bot):await bot.add_cogs(COUNT_MSG)