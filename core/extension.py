#core.extension.py
from . import constant as _constant
from .autocomplete import *

class Cog_Extension(Autocomplete):
    def __init__(self,bot:Bot):super().__init__(bot)
