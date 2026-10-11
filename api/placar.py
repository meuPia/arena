"""GET /api/placar                              -> placar público (congela nos minutos finais)
GET /api/placar  (X-Admin-Token: ADMIN_TOKEN)  -> placar real + últimas submissões
O token vai no cabeçalho, nunca na URL (que acaba em logs e no histórico)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import servico  # noqa: E402
from _lib.web import Base, admin_ok  # noqa: E402


class handler(Base):
    def get(self):
        admin = admin_ok(self.headers.get("X-Admin-Token"))
        out = servico.placar(admin=admin)
        if admin:
            out["submissoes"] = servico.submissoes()
        return out
