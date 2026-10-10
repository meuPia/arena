"""POST /api/login  {codigo} -> {token, equipe}"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import servico  # noqa: E402
from _lib.web import Base  # noqa: E402


class handler(Base):
    def post(self):
        return servico.login(self.corpo.get("codigo", ""))
