// Painel da banca: login OAuth (ou token de emergência) e as seções por papel.
// admin: Equipes, Participantes, Perfis, Submissões, Placar real e Auditoria · juiz: Submissões e Placar real.
// Tudo que vem do banco entra com escapar() ou textContent.
import { escapar } from "./api.js";
import { CABECALHO_PLACAR, linhasPlacar } from "./placar-tabela.js";

const $ = (id) => document.getElementById(id);
const CHAVE_EMERGENCIA = "arena_admin";

const ERROS = {
  nao_autorizado: "Acesso não autorizado: sua conta não está cadastrada. Peça a um admin para cadastrar seu perfil.",
  estado_invalido: "O login expirou ou foi aberto em outra aba. Tente de novo.",
  identidade_nao_verificada: "O provedor não confirmou seu e-mail.",
  provedor_falhou: "Não foi possível concluir o login com o provedor. Tente de novo.",
  provedor_invalido: "Provedor de login não configurado.",
  cancelado: "Login cancelado.",
};
const ORIGENS = { env: "As equipes ainda vêm da variável ARENA_EQUIPES.", arquivo: "As equipes ainda vêm de arena/equipes.json.",
  exemplo: "As equipes ainda vêm do arquivo de exemplo (códigos públicos: só para testes)." };

const ABAS = [
  { id: "equipes", rotulo: "Equipes", papel: "admin", carregar: carregarEquipes },
  { id: "participantes", rotulo: "Participantes", papel: "admin", carregar: carregarParticipantes },
  { id: "perfis", rotulo: "Perfis", papel: "admin", carregar: carregarPerfis },
  { id: "submissoes", rotulo: "Submissões", papel: "juiz", carregar: carregarSubmissoes },
  { id: "placar", rotulo: "Placar real", papel: "juiz", carregar: carregarPlacar },
  { id: "auditoria", rotulo: "Auditoria", papel: "admin", carregar: carregarAuditoria },
];
const NIVEL = { juiz: 1, admin: 2 };

let usuario = null;
let abaAtual = null;
let submissoes = [];
let subAberta = null;
let equipesCache = [];

// ---------------- infraestrutura ----------------

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
const adminPost = (acao, dados = {}) => chamar("/api/admin", { acao, ...dados });

const hora = (t) => (t ? new Date(t * 1000).toLocaleTimeString("pt-BR") : "–");
const fracao = (b) => (b && b.total ? `${b.aprovados}/${b.total}` : "–");
const opcoes = (lista, rotuloTodos) =>
  `<option value="">${rotuloTodos}</option>` + lista.map((v) => `<option value="${escapar(v)}">${escapar(v)}</option>`).join("");

function erroPainel(e) { $("erro-painel").textContent = e ? e.message || String(e) : ""; }

// Executa uma ação e mostra o erro no topo do painel, sem quebrar a tela.
async function tentar(fn) {
  erroPainel(null);
  try { return await fn(); } catch (e) { erroPainel(e); return undefined; }
}

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
  try { await chamar("/api/sessao", { acao: "sair" }); } catch { /* já saiu */ }
  guardarTokenEmergencia(null);
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
  tentar(abaAtual.carregar);
}

// ---------------- equipes ----------------

async function carregarEquipes() {
  const r = await admin("equipes");
  equipesCache = r.equipes;
  const noBanco = r.origem === "banco";
  const semNenhuma = r.origem === "nenhuma";
  $("aviso-origem").classList.toggle("hidden", noBanco);
  $("aviso-origem").textContent = noBanco ? "" : semNenhuma
    ? "Nenhuma equipe cadastrada ainda. Crie as equipes abaixo."
    : `${ORIGENS[r.origem] || r.origem} Importe-as para o banco para editar, gerar códigos e cadastrar participantes.`;
  $("importar-equipes").classList.toggle("hidden", noBanco || semNenhuma);
  $("equipes").innerHTML = r.equipes.map((e) => `
    <tr>
      <td class="nome">${escapar(e.nome)}</td>
      <td><code>${escapar(e.codigo)}</code></td>
      <td>${escapar(e.integrantes.join(", ")) || "–"}</td>
      <td>${e.pontos}</td><td>${e.completos}</td><td>${e.submissoes}</td><td>${hora(e.ultimaSubmissao)}</td>
      <td>${noBanco ? `
        <button class="arena-link" data-renomear="${escapar(e.id)}">renomear</button>
        <button class="arena-link" data-regenerar="${escapar(e.id)}">novo código</button>
        <button class="arena-link" data-excluir="${escapar(e.id)}">excluir</button>` : ""}</td>
    </tr>`).join("");
  $("impressao").innerHTML = r.equipes.map((e) => `
    <article><h2>${escapar(e.nome)}</h2><p class="codigo">${escapar(e.codigo)}</p>
      <p>${escapar(e.integrantes.join(" · "))}</p></article>`).join("");
}

$("form-equipe").addEventListener("submit", (ev) => {
  ev.preventDefault();
  tentar(async () => {
    await adminPost("criar_equipe", { nome: ev.target.elements.nome.value });
    ev.target.reset();
    await carregarEquipes();
  });
});

$("importar-equipes").addEventListener("click", () => {
  if (!confirm("Importar as equipes para o banco? Os códigos atuais continuam valendo.")) return;
  tentar(async () => { await adminPost("importar_equipes"); await carregarEquipes(); });
});

$("imprimir-equipes").addEventListener("click", () => window.print());

$("equipes").addEventListener("click", (ev) => {
  const { renomear, regenerar, excluir } = ev.target.dataset || {};
  const e = equipesCache.find((x) => x.id === (renomear || regenerar || excluir));
  if (!e) return;
  tentar(async () => {
    if (renomear) {
      const nome = prompt("Novo nome da equipe:", e.nome);
      if (!nome) return;
      await adminPost("editar_equipe", { id: e.id, nome });
    } else if (regenerar) {
      if (!confirm(`Gerar um novo código para ${e.nome}? O código atual para de funcionar e a equipe precisa entrar de novo.`)) return;
      await adminPost("regenerar_codigo", { id: e.id });
    } else {
      if (!confirm(`Excluir a equipe ${e.nome} e os participantes dela?`)) return;
      await adminPost("excluir_equipe", { id: e.id });
    }
    await carregarEquipes();
  });
});

// ---------------- participantes ----------------

let participantesCache = [];

async function carregarParticipantes() {
  const [eqs, r] = await Promise.all([admin("equipes"), admin("participantes")]);
  const select = $("form-participante").elements.equipe;
  const noBanco = eqs.origem === "banco";
  select.innerHTML = noBanco
    ? eqs.equipes.map((e) => `<option value="${escapar(e.id)}">${escapar(e.nome)}</option>`).join("")
    : `<option value="">Importe as equipes na aba Equipes</option>`;
  participantesCache = r.participantes;
  $("participantes").innerHTML = r.participantes.map((p) => `
    <tr><td>${escapar(p.nomeEquipe)}</td><td>${escapar(p.nome)}</td><td>${escapar(p.semestre)}</td><td>${escapar(p.email || "")}</td>
      <td><button class="arena-link" data-editar="${escapar(p.id)}">editar</button>
          <button class="arena-link" data-remover="${escapar(p.id)}">remover</button></td></tr>`).join("");
}

function limparFormParticipante() {
  const f = $("form-participante");
  f.reset();
  f.elements.id.value = "";
  $("cancelar-participante").classList.add("hidden");
}

$("form-participante").addEventListener("submit", (ev) => {
  ev.preventDefault();
  tentar(async () => {
    await adminPost("salvar_participante", Object.fromEntries(new FormData(ev.target)));
    limparFormParticipante();
    await carregarParticipantes();
  });
});
$("cancelar-participante").addEventListener("click", limparFormParticipante);

$("participantes").addEventListener("click", (ev) => {
  const { editar, remover } = ev.target.dataset || {};
  const p = participantesCache.find((x) => x.id === (editar || remover));
  if (!p) return;
  if (editar) {
    const f = $("form-participante");
    ["id", "equipe", "nome", "semestre", "email"].forEach((k) => { f.elements[k].value = p[k] || ""; });
    $("cancelar-participante").classList.remove("hidden");
    f.elements.nome.focus();
  } else if (confirm(`Remover ${p.nome}?`)) {
    tentar(async () => { await adminPost("remover_participante", { id: p.id }); await carregarParticipantes(); });
  }
});

// ---------------- perfis ----------------

let perfisCache = [];

async function carregarPerfis() {
  const r = await admin("perfis");
  perfisCache = r.perfis;
  const root = r.root.map((id) => `
    <tr><td>root</td><td colspan="2">${escapar(id)}</td><td>admin</td><td class="num">fixo (ARENA_ROOT)</td></tr>`);
  const perfis = r.perfis.map((p) => `
    <tr><td>${escapar(p.nome)}</td><td>${escapar(p.email)}</td><td>${escapar(p.github || "")}</td><td>${escapar(p.papel)}</td>
      <td><button class="arena-link" data-editar="${escapar(p.email)}">editar</button>
          <button class="arena-link" data-remover="${escapar(p.email)}">remover</button></td></tr>`);
  $("perfis").innerHTML = root.concat(perfis).join("");
}

$("form-perfil").addEventListener("submit", (ev) => {
  ev.preventDefault();
  tentar(async () => {
    await adminPost("salvar_perfil", Object.fromEntries(new FormData(ev.target)));
    ev.target.reset();
    await carregarPerfis();
  });
});

$("perfis").addEventListener("click", (ev) => {
  const { editar, remover } = ev.target.dataset || {};
  if (editar) {
    const p = perfisCache.find((x) => x.email === editar);
    const f = $("form-perfil");
    ["email", "nome", "github", "papel"].forEach((k) => { f.elements[k].value = p[k] || ""; });
    f.elements.nome.focus();
  } else if (remover && confirm(`Remover o perfil ${remover}?`)) {
    tentar(async () => { await adminPost("remover_perfil", { email: remover }); await carregarPerfis(); });
  }
});

// ---------------- submissões e ajuste ----------------

async function carregarSubmissoes() {
  submissoes = (await admin("submissoes")).submissoes;
  const filtros = { "filtro-equipe": ["nome", "Todas as equipes"], "filtro-modulo": ["codigo", "Todos os módulos"],
    "filtro-status": ["status", "Todos os status"] };
  for (const [id, [campo, todos]] of Object.entries(filtros)) {
    const atual = $(id).value;
    $(id).innerHTML = opcoes([...new Set(submissoes.map((s) => s[campo]))].sort(), todos);
    $(id).value = atual;
  }
  renderSubmissoes();
}

function renderSubmissoes() {
  const eq = $("filtro-equipe").value, mod = $("filtro-modulo").value, st = $("filtro-status").value;
  const lista = submissoes.filter((s) => (!eq || s.nome === eq) && (!mod || s.codigo === mod) && (!st || s.status === st));
  $("subs").innerHTML = lista.map((s) => `
    <tr class="${s.status === "aceito" && s.completo && !s.ajuste ? "ok" : ""}">
      <td>${hora(s.t)}</td><td>${escapar(s.nome)}</td><td>${escapar(s.codigo)}</td><td>${s.tentativa}</td>
      <td>${escapar(s.status)}${s.completo ? " ✅" : ""}</td>
      <td>${fracao(s.exemplos)}</td><td>${fracao(s.extras)}</td>
      <td>${s.pontos ?? "–"}</td>
      <td class="${s.ajuste ? "ajustado" : ""}">${s.pontosEfetivos ?? "–"}${s.ajuste ? " ✎" : ""}</td>
      <td>${s.caracteres ?? "–"}</td>
      <td>${escapar((s.participantes || []).join(", "))}</td>
      <td>${s.id ? `<button class="arena-link" data-id="${escapar(s.id)}">abrir</button>` : ""}</td>
    </tr>`).join("");
}

["filtro-equipe", "filtro-modulo", "filtro-status"].forEach((id) => $(id).addEventListener("change", renderSubmissoes));
$("atualizar-subs").addEventListener("click", () => tentar(carregarSubmissoes));

async function abrirSubmissao(id) {
  const s = await admin("submissao", { id });
  subAberta = s;
  $("sub-titulo").textContent = `${s.nome} · ${s.codigo} · tentativa ${s.tentativa} · ${s.status}`;
  $("sub-info").textContent = `${hora(s.t)} · exemplos ${fracao(s.exemplos)} · extras ${fracao(s.extras)} · `
    + `${s.caracteres} caracteres · participantes: ${(s.participantes || []).join(", ") || "–"}`;
  const aceita = s.status === "aceito";
  $("sub-ajuste").classList.toggle("hidden", !aceita);
  $("erro-ajuste").textContent = "";
  $("form-ajuste").reset();
  if (aceita) {
    const a = s.ajuste;
    $("sub-ajuste-atual").textContent = a
      ? `Ajustada: ${a.pontosJuiz} → ${a.pontos} pts por ${a.autor} às ${hora(a.t)}. Motivo: ${a.motivo}`
      : `Pontos calculados pelo juiz: ${s.pontos}. Sem ajuste.`;
    $("desfazer-ajuste").classList.toggle("hidden", !a);
  }
  $("sub-codigo").textContent = s.fonte || "";
  if (!$("dialogo-sub").open) $("dialogo-sub").showModal();
}

$("subs").addEventListener("click", (ev) => {
  const id = ev.target.dataset?.id;
  if (id) tentar(() => abrirSubmissao(id));
});
$("fechar-sub").addEventListener("click", () => $("dialogo-sub").close());

async function aposAjuste() {
  await abrirSubmissao(subAberta.id);
  await carregarSubmissoes();
}

$("form-ajuste").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  $("erro-ajuste").textContent = "";
  const f = ev.target.elements;
  try {
    await adminPost("ajustar", { id: subAberta.id, pontos: f.pontos.value, motivo: f.motivo.value });
    await aposAjuste();
  } catch (e) {
    $("erro-ajuste").textContent = e.message;
  }
});

$("desfazer-ajuste").addEventListener("click", async () => {
  if (!confirm("Desfazer o ajuste? A submissão volta a valer os pontos do juiz.")) return;
  try {
    await adminPost("desfazer_ajuste", { id: subAberta.id });
    await aposAjuste();
  } catch (e) {
    $("erro-ajuste").textContent = e.message;
  }
});

// ---------------- placar real e auditoria ----------------

async function carregarPlacar() {
  const p = await admin("placar");
  $("placar-cabecalho").innerHTML = CABECALHO_PLACAR;
  $("placar-linhas").innerHTML = linhasPlacar(p.linhas);
}

async function carregarAuditoria() {
  const { auditoria } = await admin("auditoria");
  $("auditoria").innerHTML = auditoria.map((a) => `
    <tr><td>${hora(a.t)}</td>
      <td>${escapar(a.autor)}${a.papel ? ` <span class="num">(${escapar(a.papel)}${a.provedor ? ` · ${escapar(a.provedor)}` : ""})</span>` : ""}</td>
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
