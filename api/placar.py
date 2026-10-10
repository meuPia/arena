"""GET /api/placar              -> placar público (congela nos minutos finais)
GET /api/placar?admin=TOKEN  -> placar real + últimas submissões"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import servico  # noqa: E402
from _lib.web import Base, admin_ok  # noqa: E402


class handler(Base):
    def get(self):
        admin = admin_ok(self.query.get("admin"))
        out = servico.placar(admin=admin)
        if admin:
            out["submissoes"] = servico.submissoes()
        return out
