"""Chama os handlers de api/*.py em memória (sem servidor), como a Vercel faria."""
import email.message
import importlib.util
import io
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _modulo(nome):
    spec = importlib.util.spec_from_file_location(f"api_{nome}", os.path.join(RAIZ, "api", nome + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chamar(nome, metodo="GET", caminho=None, cabecalhos=None, corpo=None, host="localhost:8787"):
    """Devolve (status, cabecalhos{nome: [valores]}, corpo_json_ou_None)."""
    cls = _modulo(nome).handler
    h = cls.__new__(cls)
    h.path = caminho or f"/api/{nome}"
    h.command, h.request_version, h.requestline = metodo, "HTTP/1.1", ""
    h.client_address = ("127.0.0.1", 0)
    msg = email.message.Message()
    msg["Host"] = host
    dados = b""
    if corpo is not None:
        dados = json.dumps(corpo).encode()
        msg["Content-Type"] = "application/json"
        msg["Content-Length"] = str(len(dados))
    for k, v in (cabecalhos or {}).items():
        del msg[k]
        msg[k] = v
    h.headers, h.rfile, h.wfile = msg, io.BytesIO(dados), io.BytesIO()
    getattr(h, "do_" + metodo)()
    bruto = h.wfile.getvalue().decode()
    cabeca, _, resto = bruto.partition("\r\n\r\n")
    linhas = cabeca.split("\r\n")
    status = int(linhas[0].split()[1])
    cab = {}
    for l in linhas[1:]:
        k, _, v = l.partition(": ")
        cab.setdefault(k.lower(), []).append(v)
    return status, cab, (json.loads(resto) if resto.strip() else None)
