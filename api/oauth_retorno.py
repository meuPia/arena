"""GET /api/oauth_retorno?code&state -> 302 para /admin.html (com o cookie de sessão) ou /admin.html?erro=<motivo>

É a URL de retorno registrada nos provedores: <ARENA_URL>/api/oauth_retorno (igual para todos)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import admin, auth, store  # noqa: E402
from _lib.web import Base, Resposta, cookie  # noqa: E402


class handler(Base):
    def get(self):
        seguro = self.seguro()
        apagar_oauth = cookie(auth.COOKIE_OAUTH, "", 0, seguro)  # o state é de uso único
        if self.query.get("error"):
            return Resposta(local="/admin.html?erro=cancelado", cookies=[apagar_oauth])
        db = store.abrir()
        try:
            ident = auth.concluir(self.query.get("code"), self.query.get("state"),
                                  self.cookies().get(auth.COOKIE_OAUTH), self.base_url())
        except auth.ErroAuth as e:
            return Resposta(local=f"/admin.html?erro={e.motivo}", cookies=[apagar_oauth])
        p = auth.papel(ident["ids"], db)
        autor = {"nome": ident["nome"], "papel": p and p["papel"]}
        if not p:
            # Fica na auditoria com as identidades tentadas, para o admin cadastrar a pessoa certa.
            admin.auditar(db, autor, "login_recusado", ident["provedor"], " ".join(ident["ids"]))
            return Resposta(local="/admin.html?erro=nao_autorizado", cookies=[apagar_oauth])
        admin.auditar(db, autor, "login", ident["provedor"], "root" if p["root"] else p["papel"])
        sessao = cookie(auth.COOKIE_SESSAO, auth.emitir_sessao(ident), auth.VALIDADE_SESSAO, seguro)
        return Resposta(local="/admin.html", cookies=[apagar_oauth, sessao])
