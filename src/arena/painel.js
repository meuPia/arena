import { api, sessao, salvarSessao, sair, escapar, formatarRelogio } from "./api.js";

const $ = (id) => document.getElementById(id);
const ICONE_NIVEL = { Bronze: "🟢", Silver: "🟡", Gold: "🟠", Extra: "🔴" };
const SUBTITULO = {
  Bronze: "Serviços básicos", Silver: "Serviços intermediários", Gold: "Serviços críticos", Extra: "Estrutura avançada",
};

let janela = null;
let deslocamentoRelogio = 0; // servidor - cliente (s)

function icones() { if (window.lucide) window.lucide.createIcons(); }

function mostrarLogin() {
  $("tela-painel").classList.add("hidden");
  $("tela-login").classList.remove("hidden");
  $("topo-equipe").textContent = "";
  $("codigo-equipe").focus();
  icones();
}

$("form-login").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  $("erro-login").textContent = "";
  try {
    const r = await api.login($("codigo-equipe").value);
    salvarSessao(r);
    await carregarPainel();
  } catch (e) {
    $("erro-login").textContent = e.message;
  }
});

$("btn-sair").addEventListener("click", () => {
  if (confirm("Sair desta equipe neste computador?")) sair();
});

function renderNivel(n) {
  const itens = n.itens.map((m) => {
    const estado = !n.liberado ? "trancado" : m.completo ? "completo" : m.melhor ? "parcial" : "aberto";
    const pts = m.melhor ? `${m.melhor.pontos}/${m.pontos} pts` : `${m.pontos} pts`;
    const conteudo = `
      <span class="arena-cod">${escapar(m.codigo)}</span>
      <span class="arena-modulo">${escapar(m.modulo)}</span>
      <span class="arena-tecnico">${n.liberado ? escapar(m.problemaTecnico) : "🔒 bloqueado"}</span>
      <span class="arena-rodape-card">
        <span>${pts}${m.completo ? " ✅" : ""}</span>
        <span>${m.tentativas ? `${m.tentativas} tentativa(s)` : ""}</span>
      </span>`;
    return n.liberado
      ? `<a class="arena-card ${estado}" href="/ide.html?desafio=${encodeURIComponent(m.codigo)}">${conteudo}</a>`
      : `<div class="arena-card ${estado}" aria-disabled="true">${conteudo}</div>`;
  }).join("");
  return `
    <section class="arena-nivel-bloco ${n.liberado ? "" : "trancado"}">
      <h2>${ICONE_NIVEL[n.nivel] || ""} ${escapar(n.nivel.toUpperCase())} <small>— ${SUBTITULO[n.nivel] || ""}</small></h2>
      ${n.liberado ? "" : `<p class="arena-dica">🔒 ${escapar(n.dica || "Ainda bloqueado.")}</p>`}
      <div class="arena-grade">${itens}</div>
    </section>`;
}

function atualizarRelogio() {
  if (!janela) return;
  const agora = Date.now() / 1000 + deslocamentoRelogio;
  let rotulo = "restante", valor;
  if (janela.ensaio) { rotulo = "modo ensaio"; valor = "∞"; }
  else if (agora < janela.inicio) { rotulo = "para abrir"; valor = formatarRelogio(janela.inicio - agora); }
  else if (agora <= janela.fim) { valor = formatarRelogio(janela.fim - agora); }
  else { rotulo = "encerrado"; valor = "00:00"; }
  $("kpi-relogio").textContent = valor;
  $("kpi-relogio-rotulo").textContent = rotulo;
}

async function carregarPainel() {
  let p;
  try {
    p = await api.missoes();
  } catch (e) {
    if (e.status === 401) return mostrarLogin();
    $("situacao").textContent = e.message;
    return;
  }
  janela = p.janela;
  deslocamentoRelogio = p.janela.agora - Date.now() / 1000;

  $("tela-login").classList.add("hidden");
  $("tela-painel").classList.remove("hidden");
  $("evento-nome").textContent = p.evento;
  $("equipe-nome").textContent = p.equipe.nome;
  $("topo-equipe").textContent = p.equipe.nome;
  $("kpi-pontos").textContent = p.equipe.pontos;

  const sit = {
    antes: "🕖 A Code Arena ainda não abriu. As missões aparecem aqui no horário de início.",
    aberta: "🟢 EM ANDAMENTO — escolha um módulo para recuperar.",
    encerrada: "🏁 Submissões encerradas. Aguarde o resultado.",
  };
  $("situacao").textContent = (p.janela.ensaio ? "🧪 MODO ENSAIO · " : "") + sit[p.janela.situacao];
  $("niveis").innerHTML = p.niveis.map(renderNivel).join("");
  atualizarRelogio();
  icones();
}

if (sessao()) carregarPainel(); else mostrarLogin();
setInterval(atualizarRelogio, 1000);
setInterval(() => { if (sessao()) carregarPainel(); }, 30000);
