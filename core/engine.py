#core.engine.py
from . import constant as _const
from .bot import *
from re import finditer as _finditer
import operator as _operator
import random as _random
import numpy as _np
import ast as _ast

_DICE_RESULTS = (
    "恭喜！大成功！",
    "極限成功",
    "困難成功",
    "通常成功",
    "成功",
    "失敗",
    "啊！大失敗！")
_ALLOWED_OPERATORS = {
    _ast.Gt:_operator.gt,
    _ast.Lt:_operator.lt,
    _ast.Eq:_operator.eq,
    _ast.GtE:_operator.ge,
    _ast.LtE:_operator.le,
    _ast.Add:_operator.add,
    _ast.Sub:_operator.sub,
    _ast.Pow:_operator.pow,
    _ast.Mod:_operator.mod,
    _ast.Mult:_operator.mul,
    _ast.USub:_operator.neg,
    _ast.UAdd:_operator.pos,
    _ast.NotEq:_operator.ne,
    _ast.Div:_operator.truediv,
    _ast.FloorDiv:_operator.floordiv}

def _safe_eval_expr(node)->int|float:
    if isinstance(node,_ast.Constant):return node.value
    if isinstance(node,_ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:raise AppError(f"不允許的運算符: {op_type.__name__}")
        return _ALLOWED_OPERATORS[op_type](_safe_eval_expr(node.operand))
    if isinstance(node,_ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:raise AppError(f"不允許的運算符: {op_type.__name__}")
        right = _safe_eval_expr(node.right)
        if isinstance(node.op,_ast.Div) and right == 0:raise AppError("不可除以零")
        return _ALLOWED_OPERATORS[op_type](_safe_eval_expr(node.left),right)
    if isinstance(node,_ast.Compare):
        left = _safe_eval_expr(node.left)
        for op_tree,comp_node in zip(node.ops,node.comparators):
            op_type = type(op_tree)
            if op_type not in _ALLOWED_OPERATORS:raise AppError(f"不允許的運算符: {op_type.__name__}")
            right = _safe_eval_expr(comp_node)
            if not _ALLOWED_OPERATORS[op_type](left,right):return 0.0
            left = right
        return 1.0
    raise AppError(f"不允許的運算符: {type(node).__name__}")
def to_dict(data:dict|list,fields:list|None=[]):
    if isinstance(data,dict):return data
    if isinstance(data,list):
        if data and isinstance(data[0],dict):
            res = {}
            for d in data:res.update(d)
            return res
        if fields and len(data)==len(fields):return dict(zip(fields,data))
    return {}
def to_see_dict(data:dict):return ", ".join(f"{k}: {v}"for k,v in data.items())

class Count_result:
    coc7e = "CoC7e"
    coc6e = "CoC6e"
    dnd = "D&D"
    def evaluate(expression:str):return round(_safe_eval_expr(_ast.parse(
        expression.strip().replace("^","**"),mode="eval").body),2)
    def coc_result(difficulty:int,version:int=7):
        roll_value = _random.randint(1,100)
        if roll_value == 100:result = 6
        elif roll_value == 1:result = 0
        elif roll_value <= difficulty and version == 6:result = 4
        elif roll_value>95 and difficulty<50:result = 6 if version == 6 else 5
        elif roll_value <= difficulty/5:result = 1
        elif roll_value <= difficulty/2:result = 2
        elif roll_value <= difficulty:result = 3
        else:result = 4
        return f"{roll_value} → {_DICE_RESULTS[result]}",result
    def dnd_result(value:str|int|float):
        value = str(value)
        final_text = value
        expression = value
        if value is None:return f"{_const.NOT} {_const.VALUE}",1
        for m in reversed(list(_finditer(r"(\d+)[Dd](\d+)",value))):
            num,sides = int(m.group(1)),int(m.group(2))
            if num > 1000 or num < 0:raise AppError(f"不支援超過 1000 與低於 0")
            if sides > 90000000 or sides < 0:raise AppError(f"不支援超過 90000000 與低於 0")
            rolls = _np.random.randint(1,sides+1,num)
            r_sum = int(rolls.sum())
            final_text = f"{final_text[:m.start()]}{f"{r_sum}[{'+'.join(map(str,rolls))}]" 
                if num <= 50 else "[...]"}{final_text[m.end():]}"
            expression = expression[:m.start()] + str(r_sum) + expression[m.end():]
        final_num = int(Count_result.evaluate(expression))
        return f"{final_text} = {final_num}",final_num
    def cut_result(sum_val:int,num:int,):
        if num <= 0:return _np.array([])
        if num == 1:return _np.array([sum_val])
        cuts = _np.sort(_np.random.randint(0,sum_val+1,num-1))
        return _np.diff(_np.concatenate(([0],cuts,[sum_val])))
    def list_result(options:list[str],mode:str=_const.CHOOSE):
        if not options:return UNKNOWN
        temp = options.copy()
        _random.shuffle(temp)
        if mode==_const.CHOOSE:output = _random.choice(temp)
        elif mode==_const.RESORT:output = " ".join(temp)
        return output
    def rand_result(a:int|float,b:int|float,mode:str=_const.FLOAT):
        output = round(_random.uniform(min(a,b),max(a,b)),2)
        if mode==_const.INT:a,b,output=int(a),int(b),int(output)
        return f"{a}～{b} → {output}",output

class Engine(commands.Cog):
    def __init__(self,bot:Bot):self.bot,self.db = bot,bot.db
    async def next_turn(
            self,
            group:str,
            guild_id:int,
            player:dict = {},
        ):
        turns = await self.db.find(_const.PLAYER,guild_id=guild_id,group=group)
        if not turns:return []
        player = next((t for t in turns if t.get(_const.IS_TURN)),player)
        doc = await self.db.find_one(_const.CARD,guild_id=guild_id)
        attributes:list[dict[str,str]] = doc.get(_const.ATTRIBUTE,[])
        base_field:list[str] = [attr.get(_const.NAME,UNKNOWN) for attr in attributes]
        battle_attribute:str = doc.get(_const.BATTLE_ATTRIBUTE,None)
        if battle_attribute not in base_field:raise AppError(battle_attribute+_const.NOT+_const.EXIST)
        idx = base_field.index(battle_attribute)
        turns.sort(key=lambda x:(x[_const.NOW][idx],str(x[_const.ID])),reverse=True)
        if player:next_idx = (next((i for i,p in enumerate(turns) 
            if p[_const.USER_ID]==player[_const.USER_ID] 
            and p[_const.NAME]==player[_const.NAME]),-1)+1)%len(turns)
        else:next_idx = 0
        turns = turns[next_idx:]+turns[:next_idx]
        await self.db.bulk_write(UpdateMany(_const.PLAYER,{"$set":{
            _const.IS_TURN:False}},guild_id=guild_id,group=group),UpdateOne(
                _const.PLAYER,{"$set":{_const.IS_TURN:True}},ID=turns[0][_const.ID]))
        return turns
