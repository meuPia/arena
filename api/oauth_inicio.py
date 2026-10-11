"""GET /api/oauth_inicio?provedor=google|github -> 302 para o provedor (+ cookie arena_oauth com o nonce)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import auth  # noqa: E402
from _lib.web import Base, Resposta, cookie  # noqa: E402


class handler(Base):
    def get(self):
        try:
            url, nonce = auth.iniciar(self.query.get("provedor", ""), self.base_url())
        except auth.ErroAuth as e:
            return Resposta(local=f"/admin.html?erro={e.motivo}")
        return Resposta(local=url, cookies=[cookie(auth.COOKIE_OAUTH, nonce, auth.VALIDADE_STATE, self.seguro())])
