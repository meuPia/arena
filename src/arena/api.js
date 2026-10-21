// Cliente da API da Code Arena + sessão da equipe (token no localStorage).

const CHAVE_SESSAO = "arena_sessao";

function lerStorage(chave) {
  try { return localStorage.getItem(chave); } catch { return null; }
}
function gravarStorage(chave, valor) {
  try {
    if (valor === null) localStorage.removeItem(chave);
    else localStorage.setItem(chave, valor);
  } catch { /* navegação privada: segue sem persistir */ }
}

let sessaoMemoria = null;

export function sessao() {
  if (sessaoMemoria) return sessaoMemoria;
  const bruto = lerStorage(CHAVE_SESSAO);
  try { sessaoMemoria = bruto ? JSON.parse(bruto) : null; } catch { sessaoMemoria = null; }
  return sessaoMemoria;
}

export function salvarSessao(s) {
  sessaoMemoria = s;
  gravarStorage(CHAVE_SESSAO, s ? JSON.stringify(s) : null);
}

export function sair() {
  salvarSessao(null);
  window.location.href = "/";
}

export class ErroApi extends Error {
  constructor(status, mensagem) { super(mensagem); this.status = status; }
}

async function chamar(caminho, opcoes = {}) {
  const s = sessao();
  const headers = { "Content-Type": "application/json", ...(opcoes.headers || {}) };
  if (s?.token) headers.Authorization = `Bearer ${s.token}`;
  let resp;
  try {
    resp = await fetch(caminho, { ...opcoes, headers });
  } catch {
    throw new ErroApi(0, "Sem conexão com o servidor da arena. Tente de novo.");
  }
  let corpo = {};
  try { corpo = await resp.json(); } catch { /* corpo vazio */ }
  if (resp.status === 401) {
    salvarSessao(null);
    if (!location.pathname.endsWith("/") && !location.pathname.endsWith("index.html")) location.href = "/";
  }
  if (!resp.ok) throw new ErroApi(resp.status, corpo.erro || `Erro ${resp.status}`);
  return corpo;
}

export const api = {
  login: (codigo) => chamar("/api/login", { method: "POST", body: JSON.stringify({ codigo }) }),
  missoes: () => chamar("/api/missoes"),
  missao: (codigo) => chamar(`/api/missoes?codigo=${encodeURIComponent(codigo)}`),
  submeter: (codigo, fonte, participantes) =>
    chamar("/api/submeter", { method: "POST", body: JSON.stringify({ codigo, fonte, participantes }) }),
  placar: () => chamar("/api/placar"),
};

// Rascunho do código por equipe + missão (sobrevive a voltar ao painel / recarregar).
export function chaveRascunho(codigo) {
  return `arena_rascunho_${sessao()?.equipe?.id || "anon"}_${codigo}`;
}
export const lerRascunho = (codigo) => lerStorage(chaveRascunho(codigo));
export const gravarRascunho = (codigo, texto) => gravarStorage(chaveRascunho(codigo), texto);

export function formatarRelogio(segundos) {
  segundos = Math.max(0, Math.floor(segundos));
  const h = Math.floor(segundos / 3600), m = Math.floor((segundos % 3600) / 60), s = segundos % 60;
  const dd = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${dd(m)}:${dd(s)}` : `${dd(m)}:${dd(s)}`;
}

// Relógio do evento a partir da janela do servidor ({inicio, fim, ensaio} em segundos) e do "agora" do servidor.
export function textoRelogio(janela, agora) {
  if (!janela) return { valor: "--:--", rotulo: "" };
  if (janela.offline) return { valor: "∞", rotulo: "modo offline" }; // o tempo é controlado na sala
  if (janela.ensaio) return { valor: "∞", rotulo: "modo ensaio" };
  if (agora < janela.inicio) return { valor: formatarRelogio(janela.inicio - agora), rotulo: "para abrir" };
  if (agora <= janela.fim) return { valor: formatarRelogio(janela.fim - agora), rotulo: "restante" };
  return { valor: "00:00", rotulo: "encerrado" };
}

export function escapar(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
