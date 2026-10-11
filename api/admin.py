"""Painel da banca (sessão OAuth ou X-Admin-Token de emergência).
GET  /api/admin?acao=placar|submissoes|submissao&id=|perfis|auditoria
POST /api/admin {acao: salvar_perfil|remover_perfil, ...}"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import admin  # noqa: E402
from _lib.web import Base  # noqa: E402


class handler(Base):
    def get(self):
        q = dict(self.query)
        return admin.executar(q.pop("acao", ""), self.banca(), q)

    def post(self):
        c = dict(self.corpo)
        return admin.executar(str(c.pop("acao", "")), self.banca(), c)
