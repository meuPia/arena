"""POST /api/submeter  {codigo, fonte, participantes[]} -> resultado do juiz"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import servico  # noqa: E402
from _lib.web import Base  # noqa: E402


class handler(Base):
    def post(self):
        eid = self.equipe_id()
        c = self.corpo
        return servico.submeter(eid, str(c.get("codigo", "")).upper(), c.get("fonte", ""),
                                c.get("participantes") or [])
