"""GET  /api/sessao          -> {usuario|null, provedores[], emergencia}
POST /api/sessao {acao: "sair"} -> apaga o cookie de sessão"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import auth  # noqa: E402
from _lib.web import Base, Erro, Resposta, cookie  # noqa: E402


class handler(Base):
    def get(self):
        try:
            autor = self.banca()
            usuario = {k: autor[k] for k in ("nome", "papel", "root", "provedor")}
        except Erro:
            usuario = None
        return {"usuario": usuario, "provedores": auth.provedores_configurados(),
                "emergencia": bool(os.environ.get("ADMIN_TOKEN"))}

    def post(self):
        if self.corpo.get("acao") != "sair":
            raise Erro(400, "Ação desconhecida.")
        return Resposta({"ok": True}, cookies=[cookie(auth.COOKIE_SESSAO, "", 0, self.seguro())])
