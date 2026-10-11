// Painel da banca: login OAuth (ou token de emergência), placar real, submissões, perfis e auditoria.
// Tudo que vem do banco entra com escapar() ou textContent.
import { escapar } from "./api.js";
import { CABECALHO_PLACAR, linhasPlacar } from "./placar-tabela.js";

const $ = (id) => document.getElementById(id);
const CHAVE_EMERGENCIA = "arena_admin"; // a mesma do placar.html#admin=

const ERROS = {
  nao_autorizado: "Sua conta não tem acesso ao painel. Peça a um admin para cadastrar seu perfil.",
  estado_invalido: "O login expirou ou foi aberto em outra aba. Tente de novo.",
  identidade_nao_verificada: "O provedor não confirmou seu e-mail.",
  provedor_falhou: "Não foi possível concluir o login com o provedor. Tente de novo.",
  provedor_invalido: "Provedor de login não configurado.",
  cancelado: "Login cancelado.",
};

const ABAS = [
  { id: "placar", rotulo: "Placar real", papel: "juiz", carregar: carregarPlacar },
  { id: "submissoes", rotulo: "Submissões", papel: "juiz", carregar: carregarSubmissoes },
  { id: "perfis", rotulo: "Perfis", papel: "admin", carregar: carregarPerfis },
  { id: "auditoria", rotulo: "Auditoria", papel: "admin", carregar: carregarAuditoria },
];
const NIVEL = { juiz: 1, admin: 2 };

let usuario = null;
let abaAtual = null;
let submissoes = [];

function tokenEmergencia() {
  try { return sessionStorage.getItem(CHAVE_EMERGENCIA); } catch { return null; }
}
function guardarTokenEmergencia(valor) {
  try {
    if (valor) sessionStorage.setItem(CHAVE_EMERGENCIA, valor);
    else sessionStorage.removeItem(CHAVE_EMERGENCIA);
  } catch { /* navegação privada */ }
}

async function chamar(caminho, corpo) {
  const headers = { "Content-Type": "application/json" };
  const tok = tokenEmergencia();
  if (tok) headers["X-Admin-Token"] = tok;
  const opcoes = corpo ? { method: "POST", headers, body: JSON.stringify(corpo) } : { headers };
  const resp = await fetch(caminho, opcoes);
  let dados = {};
  try { dados = await resp.json(); } catch { /* sem corpo */ }
  if (resp.status === 401) { mostrarLogin(dados.erro); throw new Error(dados.erro || "Sessão encerrada."); }
  if (!resp.ok) throw new Error(dados.erro || `Erro ${resp.status}`);
  return dados;
}
const admin = (acao, params = {}) => chamar(`/api/admin?${new URLSearchParams({ acao, ...params })}`);
const adminPost = (acao, dados) => chamar("/api/admin", { acao, ...dados });

const hora = (t) => new Date(t * 1000).toLocaleTimeString("pt-BR");
const fracao = (b) => (b && b.total ? `${b.aprovados}/${b.total}` : "–");

// ---------------- login ----------------

function mostrarLogin(mensagem) {
  usuario = null;
  $("tela-painel").classList.add("hidden");
  $("tela-login").classList.remove("hidden");
  $("btn-sair").classList.add("hidden");
  $("usuario").textContent = "";
  if (mensagem) $("erro-login").textContent = mensagem;
}

function montarLogin(sessao) {
  $("provedores").innerHTML = sessao.provedores.map((p) =>
    `<a class="arena-primario" href="/api/oauth_inicio?provedor=${encodeURIComponent(p.id)}">Entrar com ${escapar(p.nome)}</a>`).join("");
  $("sem-provedores").classList.toggle("hidden", sessao.provedores.length > 0);
  $("form-emergencia").classList.toggle("hidden", !sessao.emergencia);
}

$("form-emergencia").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  guardarTokenEmergencia($("token-emergencia").value.trim());
  $("token-emergencia").value = "";
  await iniciar();
  if (!usuario) {
    guardarTokenEmergencia(null);
    $("erro-login").textContent = "Token de emergência inválido.";
  }
});

$("btn-sair").addEventListener("click", async () => {
  guardarTokenEmergencia(null);
  try { await chamar("/api/sessao", { acao: "sair" }); } catch { /* já saiu */ }
  location.href = "/admin.html";
});

// ---------------- abas ----------------

function montarAbas() {
  const visiveis = ABAS.filter((a) => NIVEL[usuario.papel] >= NIVEL[a.papel]);
  $("abas").innerHTML = visiveis.map((a) =>
    `<button role="tab" data-aba="${a.id}" class="arena-aba-botao">${a.rotulo}</button>`).join("");
  $("abas").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => abrirAba(b.dataset.aba)));
  abrirAba(visiveis[0].id);
}

function abrirAba(id) {
  abaAtual = ABAS.find((a) => a.id === id);
  ABAS.forEach((a) => $(`aba-${a.id}`).classList.toggle("hidden", a.id !== id));
  $("abas").querySelectorAll("button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.aba === id)));
  abaAtual.carregar().catch((e) => console.error(e));
}

async function carregarPlacar() {
  const p = await admin("placar");
  $("placar-cabecalho").innerHTML = CABECALHO_PLACAR;
  $("placar-linhas").innerHTML = linhasPlacar(p.linhas);
}

async function carregarSubmissoes() {
  submissoes = (await admin("submissoes")).submissoes;
  renderSubmissoes();
}

function renderSubmissoes() {
  const filtro = $("filtro-subs").value.trim().toLowerCase();
  const lista = submissoes.filter((s) => !filtro
    || [s.nome, s.codigo, s.status, ...(s.participantes || [])].join(" ").toLowerCase().includes(filtro));
  $("subs").innerHTML = lista.map((s) => `
    <tr class="${s.status === "aceito" && s.completo ? "ok" : ""}">
      <td>${hora(s.t)}</td><td>${escapar(s.nome)}</td><td>${escapar(s.codigo)}</td><td>${s.tentativa}</td>
      <td>${escapar(s.status)}${s.completo ? " ✅" : ""}</td>
      <td>${fracao(s.exemplos)}</td><td>${fracao(s.extras)}</td>
      <td>${s.pontos ?? "–"}</td><td>${s.caracteres ?? "–"}</td>
      <td>${escapar((s.participantes || []).join(", "))}</td>
      <td>${s.id ? `<button class="arena-link" data-id="${escapar(s.id)}">código</button>` : ""}</td>
    </tr>`).join("");
}

$("filtro-subs").addEventListener("input", renderSubmissoes);
$("atualizar-subs").addEventListener("click", () => carregarSubmissoes());
$("subs").addEventListener("click", async (ev) => {
  const id = ev.target.dataset?.id;
  if (!id) return;
  const s = await admin("submissao", { id });
  $("fonte-titulo").textContent = `${s.nome} · ${s.codigo} · tentativa ${s.tentativa} · ${s.status}`;
  $("fonte-codigo").textContent = s.fonte || "";
  $("dialogo-fonte").showModal();
});
$("fechar-fonte").addEventListener("click", () => $("dialogo-fonte").close());

async function carregarPerfis() {
  const r = await admin("perfis");
  const root = r.root.map((id) => `
    <tr><td>root</td><td colspan="2">${escapar(id)}</td><td>admin</td><td class="num">fixo (ARENA_ROOT)</td></tr>`);
  const perfis = r.perfis.map((p) => `
    <tr><td>${escapar(p.nome)}</td><td>${escapar(p.email)}</td><td>${escapar(p.github || "")}</td><td>${escapar(p.papel)}</td>
      <td><button class="arena-link" data-editar="${escapar(p.email)}">editar</button>
          <button class="arena-link" data-remover="${escapar(p.email)}">remover</button></td></tr>`);
  $("perfis").innerHTML = root.concat(perfis).join("");
  $("perfis").dataset.json = JSON.stringify(r.perfis);
}

$("form-perfil").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  $("erro-perfil").textContent = "";
  const dados = Object.fromEntries(new FormData(ev.target));
  try {
    await adminPost("salvar_perfil", dados);
    ev.target.reset();
    await carregarPerfis();
  } catch (e) {
    $("erro-perfil").textContent = e.message;
  }
});

$("perfis").addEventListener("click", async (ev) => {
  const { editar, remover } = ev.target.dataset || {};
  if (editar) {
    const p = JSON.parse($("perfis").dataset.json).find((x) => x.email === editar);
    const f = $("form-perfil");
    ["email", "nome", "github", "papel"].forEach((k) => { f.elements[k].value = p[k] || ""; });
    f.elements.nome.focus();
  } else if (remover && confirm(`Remover o perfil ${remover}?`)) {
    try {
      await adminPost("remover_perfil", { email: remover });
      await carregarPerfis();
    } catch (e) {
      $("erro-perfil").textContent = e.message;
    }
  }
});

async function carregarAuditoria() {
  const { auditoria } = await admin("auditoria");
  $("auditoria").innerHTML = auditoria.map((a) => `
    <tr><td>${hora(a.t)}</td><td>${escapar(a.autor)}${a.papel ? ` <span class="num">(${escapar(a.papel)})</span>` : ""}</td>
      <td>${escapar(a.acao)}</td><td>${escapar(a.alvo)}</td><td>${escapar(a.resumo)}</td></tr>`).join("");
}

// ---------------- início ----------------

async function iniciar() {
  const erro = new URLSearchParams(location.search).get("erro");
  if (erro) history.replaceState(null, "", location.pathname);
  let sessao;
  try {
    sessao = await chamar("/api/sessao");
  } catch (e) {
    mostrarLogin(e.message);
    return;
  }
  montarLogin(sessao);
  if (!sessao.usuario) {
    mostrarLogin(erro ? ERROS[erro] || "Não foi possível entrar." : "");
    return;
  }
  usuario = sessao.usuario;
  $("usuario").textContent = `${usuario.nome} · ${usuario.root ? "root" : usuario.papel}`;
  $("btn-sair").classList.remove("hidden");
  $("tela-login").classList.add("hidden");
  $("tela-painel").classList.remove("hidden");
  $("erro-login").textContent = "";
  montarAbas();
}

iniciar();
setInterval(() => { if (usuario && abaAtual?.id === "placar") carregarPlacar().catch(() => {}); }, 15000);
