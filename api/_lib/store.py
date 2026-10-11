"""Armazenamento: Supabase (Postgres via REST), Upstash Redis via REST ou arquivo local no desenvolvimento.

As três implementações têm a mesma interface (subconjunto de comandos Redis). Variáveis aceitas:
  SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY (ou SUPABASE_SECRET_KEY)  -> Supabase (tabelas de supabase/arena.sql)
  KV_REST_API_URL / KV_REST_API_TOKEN ou UPSTASH_REDIS_REST_URL / _TOKEN -> Upstash Redis
Sem nenhuma, usa um JSON em ARENA_ARQUIVO_LOCAL (padrão: /tmp/meupia-arena.json) — só para dev/testes.
"""
import fcntl
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class RedisRest:
    def __init__(self, url, token):
        self.url = url.rstrip("/")
        self.token = token

    def _cmd(self, *args):
        req = urllib.request.Request(
            self.url, data=json.dumps([str(a) for a in args]).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            corpo = json.loads(r.read())
        if "error" in corpo:
            raise RuntimeError(corpo["error"])
        return corpo["result"]

    def hgetall(self, chave):
        r = self._cmd("HGETALL", chave) or []
        return dict(zip(r[::2], r[1::2]))

    def hget(self, chave, campo):
        return self._cmd("HGET", chave, campo)

    def hset(self, chave, campo, valor):
        self._cmd("HSET", chave, campo, valor)

    def hsetnx(self, chave, campo, valor):
        return bool(self._cmd("HSETNX", chave, campo, valor))

    def hdel(self, chave, campo):
        self._cmd("HDEL", chave, campo)

    def hincrby(self, chave, campo, n=1):
        return int(self._cmd("HINCRBY", chave, campo, n))

    def lpush(self, chave, valor):
        self._cmd("LPUSH", chave, valor)

    def lrange(self, chave, ini, fim):
        return self._cmd("LRANGE", chave, ini, fim) or []

    def apagar(self, *chaves):
        if chaves:
            self._cmd("DEL", *chaves)


class SupabaseRest:
    """Mesma interface, sobre as tabelas arena_hash/arena_lista via PostgREST (supabase/arena.sql).
    Usa a chave secreta (service_role): só no servidor, nunca no navegador."""

    PAGINA = 1000  # o PostgREST do Supabase devolve no máximo 1000 linhas por pedido

    def __init__(self, url, chave):
        self.base = url.rstrip("/") + "/rest/v1"
        self.chave = chave

    def _req(self, metodo, caminho, filtros=None, corpo=None, prefer=None):
        url = f"{self.base}/{caminho}"
        if filtros:
            url += "?" + urllib.parse.urlencode(filtros, safe="(),.:*\"")
        cab = {"apikey": self.chave, "Content-Type": "application/json", "Accept": "application/json"}
        if self.chave.startswith("eyJ"):  # chave legada (JWT); as novas sb_secret_ vão só no apikey
            cab["Authorization"] = f"Bearer {self.chave}"
        if prefer:
            cab["Prefer"] = prefer
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(url, data=dados, headers=cab, method=metodo)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                bruto = r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Supabase {e.code}: {e.read()[:300]!r}") from None
        return json.loads(bruto) if bruto.strip() else None

    @staticmethod
    def _eq(valor):
        return "eq." + str(valor)

    def hgetall(self, chave):
        linhas = self._req("GET", "arena_hash", {"select": "campo,valor", "chave": self._eq(chave)}) or []
        return {l["campo"]: l["valor"] for l in linhas}

    def hget(self, chave, campo):
        linhas = self._req("GET", "arena_hash", {"select": "valor", "chave": self._eq(chave),
                                                 "campo": self._eq(campo)}) or []
        return linhas[0]["valor"] if linhas else None

    def hset(self, chave, campo, valor):
        self._req("POST", "arena_hash", corpo={"chave": chave, "campo": campo, "valor": str(valor)},
                  prefer="resolution=merge-duplicates,return=minimal")

    def hsetnx(self, chave, campo, valor):
        r = self._req("POST", "arena_hash", corpo={"chave": chave, "campo": campo, "valor": str(valor)},
                      prefer="resolution=ignore-duplicates,return=representation")
        return bool(r)

    def hdel(self, chave, campo):
        self._req("DELETE", "arena_hash", {"chave": self._eq(chave), "campo": self._eq(campo)},
                  prefer="return=minimal")

    def hincrby(self, chave, campo, n=1):
        return int(self._req("POST", "rpc/arena_hincrby", corpo={"p_chave": chave, "p_campo": campo, "p_n": n}))

    def lpush(self, chave, valor):
        self._req("POST", "arena_lista", corpo={"chave": chave, "valor": valor}, prefer="return=minimal")

    def lrange(self, chave, ini, fim):
        """Como no Redis: índice 0 = mais recente; fim = -1 vai até o final (paginando)."""
        out, offset = [], ini
        while True:
            limite = self.PAGINA if fim == -1 else min(self.PAGINA, fim - offset + 1)
            if limite <= 0:
                break
            linhas = self._req("GET", "arena_lista", {
                "select": "valor", "chave": self._eq(chave), "order": "id.desc",
                "offset": offset, "limit": limite}) or []
            out += [l["valor"] for l in linhas]
            offset += len(linhas)
            if len(linhas) < limite:
                break
        return out

    def apagar(self, *chaves):
        if not chaves:
            return
        lista = "in.(" + ",".join('"' + c.replace('"', '') + '"' for c in chaves) + ")"
        for tabela in ("arena_hash", "arena_lista"):
            self._req("DELETE", tabela, {"chave": lista}, prefer="return=minimal")


class Local:
    """Mesma interface, num arquivo JSON com lock. Não use em produção."""

    def __init__(self, caminho):
        self.caminho = caminho

    def _tx(self, fn):
        with open(self.caminho, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            bruto = f.read()
            dados = json.loads(bruto) if bruto.strip() else {}
            r = fn(dados)
            f.seek(0)
            f.truncate()
            json.dump(dados, f)
            return r

    def hgetall(self, chave):
        return self._tx(lambda d: dict(d.get(chave, {})))

    def hget(self, chave, campo):
        return self._tx(lambda d: d.get(chave, {}).get(campo))

    def hset(self, chave, campo, valor):
        self._tx(lambda d: d.setdefault(chave, {}).__setitem__(campo, str(valor)))

    def hsetnx(self, chave, campo, valor):
        def f(d):
            h = d.setdefault(chave, {})
            if campo in h:
                return False
            h[campo] = str(valor)
            return True
        return self._tx(f)

    def hdel(self, chave, campo):
        self._tx(lambda d: d.get(chave, {}).pop(campo, None))

    def hincrby(self, chave, campo, n=1):
        def f(d):
            h = d.setdefault(chave, {})
            h[campo] = str(int(h.get(campo, 0)) + n)
            return int(h[campo])
        return self._tx(f)

    def lpush(self, chave, valor):
        self._tx(lambda d: d.setdefault(chave, []).insert(0, valor))

    def lrange(self, chave, ini, fim):
        return self._tx(lambda d: d.get(chave, [])[ini: None if fim == -1 else fim + 1])

    def apagar(self, *chaves):
        self._tx(lambda d: [d.pop(c, None) for c in chaves])


def abrir():
    sb_url = os.environ.get("SUPABASE_URL")
    sb_chave = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SECRET_KEY")
    if sb_url and sb_chave:
        return SupabaseRest(sb_url, sb_chave)
    url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    tok = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    if url and tok:
        return RedisRest(url, tok)
    return Local(os.environ.get("ARENA_ARQUIVO_LOCAL", "/tmp/meupia-arena.json"))


# Chaves (prefixo permite rodar ensaio e evento no mesmo banco)
def _p():
    return os.environ.get("ARENA_PREFIXO", "arena")


def k_aceitas(eid):
    return f"{_p()}:aceitas:{eid}"         # lista JSON {t, codigo, pontos, completo, caracteres} (mais recente primeiro)


def k_tentativas(eid):
    return f"{_p()}:tentativas:{eid}"      # hash cod -> nº de submissões


def k_ultima(eid):
    return f"{_p()}:ultima:{eid}"          # hash cod -> timestamp da última submissão


def _conteudo():
    return os.environ.get("ARENA_CONTEUDO", "conteudo")


def k_desafios():
    return f"{_conteudo()}:desafios"       # hash cod -> JSON público (enunciado, código inicial, exemplos)


def k_segredos():
    return f"{_conteudo()}:segredos"       # hash cod -> JSON {testesExtras, gabarito} (só para julgar/admin)


def k_validacao():
    return f"{_conteudo()}:validacao"      # hash cod -> JSON da última validação {ok, quando, resumo}


def k_login(janela):
    return f"{_p()}:login:{janela}"        # hash ip -> nº de logins errados na janela de 10 min


def k_equipes():
    return f"{_conteudo()}:equipes"        # hash id -> JSON {id, nome, codigo, versao, criadaEm}


def k_participantes():
    return f"{_conteudo()}:participantes"  # hash id -> JSON {id, equipe, nome, semestre, email}


def k_ajustes():
    return f"{_p()}:ajustes"               # hash id da submissão -> JSON {pontos, pontosJuiz, motivo, autor, t, ...}


def k_usuarios():
    return f"{_conteudo()}:usuarios"       # hash email -> JSON {email, nome, github, papel} (perfis da banca)


def k_auditoria():
    return f"{_conteudo()}:auditoria"      # lista JSON {t, autor, acao, alvo, resumo} (mais recente primeiro)


def k_log():
    return f"{_p()}:submissoes"            # lista JSON (mais recente primeiro)
