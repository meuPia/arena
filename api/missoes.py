"""GET /api/missoes            -> painel da equipe (níveis, cadeados, status)
GET /api/missoes?codigo=B01 -> enunciado + código inicial + testes públicos (só se liberado)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import servico  # noqa: E402
from _lib.web import Base  # noqa: E402


class handler(Base):
    def get(self):
        eid = self.equipe_id()
        cod = self.query.get("codigo")
        return servico.missao(eid, cod.upper()) if cod else servico.missoes(eid)
