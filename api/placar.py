"""GET /api/placar -> placar público (congela nos minutos finais).

Sempre público: ignora sessão da banca e token de emergência, para que um telão logado nunca
descongele. O placar real (vivo) e o log ficam no painel: GET /api/admin?acao=placar|submissoes."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import servico  # noqa: E402
from _lib.web import Base  # noqa: E402


class handler(Base):
    def get(self):
        return servico.placar()
