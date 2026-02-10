#core.command.py
from . import constant as _const
from .addon import *
from re import findall as _findall
from random import sample as _s

_BASIC = _const.BASIC
_MAX = _const.MAX
_NOW = _const.NOW
_MODE_MAP = {"B":_BASIC,"M":_MAX,"N":_NOW}

def _sample(population:list,k:int,):return _s(population,k)

def _smart_split(s:str)->list[str]:
    parts,current,bracket_level = [],[],0
    for char in s:
        if char == "(":bracket_level += 1
        elif char == ")":bracket_level -= 1
        if char == "," and bracket_level == 0:
            parts.append("".join(current));current = []
        elif char != " ":current.append(char)
    return parts + ["".join(current).strip()]
def _get_actions(s:str)->list[str]:
    parts,current,bracket_level = [],[],0
    for char in s:
        if char == "{":bracket_level += 1
        elif char == "}":
            bracket_level -= 1
            if bracket_level == 0:
                parts.append("".join(current));current = []
        elif bracket_level > 0 and char != " ":current.append(char)
    return parts
def _get_command(s:str)->dict[str,dict[str,str]]:
    command_dict = {}
    command_dict["u"],command_dict["e"] = {},{}
    for command in s.strip().split(";"):
        sidefile,cmd = command.split(":",1)if ":" in command else ("","")
        side,file = sidefile.split(".",1)if "." in sidefile else ("","")
        if not cmd or cmd[0] not in "+-*/":
            raise AppError(f"指令 {cmd} 應由 + 或 - 或 * 或 / 開頭")
        if side not in ["u","e"]:
            raise AppError(f"屬性欄位 {sidefile} 應由 e 或 u 開頭")
        doc:dict = command_dict.get(side,{})
        command_dict[side][file] = doc.get(file,"")+cmd
    return command_dict

def replace_tags(text:str,stats_map:dict):
    for tag in _findall(r"\[(.+?)\]",text):
        if tag in stats_map:text=text.replace(f"[{tag}]",str(stats_map[tag]))
        else:raise AppError(f"{tag}{_const.NOT}{_const.EXIST}")
    return text
def get_stats_map(base_field:list,player:dict):
    stats_map = {}
    for idx,field in enumerate(base_field):
        stats_map[f"B.{field}"]=player[_BASIC][idx]if idx<len(player[_BASIC])else 0
        stats_map[f"M.{field}"]=player[_MAX][idx]if idx<len(player[_MAX])else 0
        stats_map[f"N.{field}"]=player[_NOW][idx]if idx<len(player[_NOW])else 0
    return stats_map

class Command(Addon):
    def __init__(
            self, 
            db:DataBase,
            cmd:str,
            u_player:dict,
            t_players:list[dict] = None,
            save_data:bool=True,
            target_num:int=1,
    ):
        self.save_data = save_data
        self.u_player = u_player
        self.t_players = t_players
        self._player = {}
        self.target_num = target_num
        self.cmd = cmd
        self.stats_map = {}
        self.base_field = []
        super().__init__(
            db, 
            guild_id=u_player[_const.GUILD_ID], 
            user_id=u_player[_const.USER_ID], 
            send_function=None,
        )
    def _get_stats_map(self):
        for idx,field in enumerate(self.base_field):
            self.stats_map[f"u.B.{field}"]=self.u_player[
                _BASIC][idx]if idx<len(self.u_player[_BASIC])else 0
            self.stats_map[f"u.M.{field}"]=self.u_player[
                _MAX][idx]if idx<len(self.u_player[_MAX])else 0
            self.stats_map[f"u.N.{field}"]=self.u_player[
                _NOW][idx]if idx<len(self.u_player[_NOW])else 0
            self.stats_map[f"e.B.{field}"]=self._player[
                _BASIC][idx]if idx<len(self._player[_BASIC])else 0
            self.stats_map[f"e.M.{field}"]=self._player[
                _MAX][idx]if idx<len(self._player[_MAX])else 0
            self.stats_map[f"e.N.{field}"]=self._player[
                _NOW][idx]if idx<len(self._player[_NOW])else 0
        return self.stats_map
    async def execute(self):
        try:
            attributes = (await self.find_one(_const.CARD,guild_id=self.guild_id)).get(_const.ATTRIBUTE,[])
            self.base_field:list[str] = [arr.get(_const.NAME) for arr in attributes]
            self.f_idx = {name:i for i,name in enumerate(self.base_field)}
            targets = await self.db.find(
                _const.PLAYER,group=self.u_player.get(_const.GROUP),guild_id=self.guild_id) or []
            if self.t_players:
                for t in self.t_players:
                    targets.append(t)
            self.return_text = []
            cmd_doc = _get_command(self.cmd)
            queue = [("u",self.u_player)] + [("e",p) for p in (
                _sample(targets,self.target_num)if len(targets)>self.target_num else targets)]
            for side,p in queue:
                self._player = p
                for file_key,raw_cmd in cmd_doc.get(side,{}).items():
                    await self._apply_stat_change(file_key,raw_cmd)
            if self.save_data:await self.bulk_write(*[
                UpdateOne(_const.PLAYER,{"$set":p},ID=p[_const.ID])for _,p in queue])
            return str("\n".join(self.return_text))
        except AppError as e:return str(e)
        except Exception as e:raise e
    async def _apply_stat_change(self,file_key:str,raw_cmd:str):
        mode,attr = file_key.split(".",1)
        if attr not in self.f_idx:raise AppError(f"{attr} {_const.NOT} {_const.EXIST}")
        _idx,_key = self.f_idx[attr],_MODE_MAP[mode]
        old_val = self._player[_key][_idx]
        new_val = int(Count_result.dnd_result(str(
            self._player[_BASIC][_idx]if _key == _MAX else old_val)+await self._process_actions(raw_cmd))[1])
        if _key == _NOW:
            limit = self._player[_MAX][_idx]
            new_val = max(min(new_val,limit),-limit)
        self._player[_key][_idx] = new_val
        if self.save_data:self.return_text.append(
            f"{self._player[_const.NAME]}.{file_key}: {old_val} -> {new_val}")
    async def _process_actions(self,raw_cmd:str):
        cmd_str = replace_tags(raw_cmd,self._get_stats_map())
        for action_content in _get_actions(cmd_str):
            parts = _smart_split(action_content)
            self._dice_expr = parts[0]
            self._roll_val = Count_result.dnd_result(self._dice_expr)[1]
            result = Count_result.evaluate(f"{self._roll_val}{parts[1]}")
            for act in parts[2:]:await self._handle_side_effect(act)
        return cmd_str.replace("{"+str(action_content)+"}",str(result))
    async def _handle_side_effect(self,act:str):
        func_name,body = act.split("(", 1)
        args = _smart_split(body[:-1])
        if func_name == _const.RETURN:
            for c in args:
                if Count_result.dnd_result(f"{self._roll_val}{c}")[1] and self.save_data:
                    self.return_text.append(f"{self._dice_expr}->{self._roll_val}{c}")
            return
        if not Count_result.dnd_result(f"{self._roll_val}{args[0]}")[1]:return
        if len(args) > 3:thing = str(args[3])
        else:
            feature_list = (await self.get(
                args[1],self._player[_const.NAME],self._player[_const.USER_ID])
                if func_name == _const.REMOVE
                else await self.find(args[1]))
            target_idx = int(Count_result.dnd_result(f"1d{len(
                feature_list)}-1")[1]) if feature_list else None
            if target_idx is None:raise AppError(f"{_const.DATA}{_const.NOT}{_const.EXIST}")
            thing = feature_list[target_idx].get(_const.NAME,None)
        if not thing:raise AppError(f"{_const.DATA}{_const.NOT}{_const.EXIST}")
        await (self.give if func_name == _const.GIVE else self.remove)(
            args[1],self._player[_const.NAME],thing,
            Count_result.dnd_result(args[2])[1],self._player[_const.USER_ID])
