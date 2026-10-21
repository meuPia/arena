import { api, sessao, salvarSessao, sair, escapar, textoRelogio } from "./api.js";

const $ = (id) => document.getElementById(id);
const SUBTITULO = {
  Bronze: "Serviços básicos", Silver: "Serviços intermediários", Gold: "Serviços críticos", Extra: "Estrutura avançada",
};

let janela = null;
let offline = false; // modo offline: sem login, sem submissão (as equipes salvam o .por)
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

const ROTULO_ESTADO = { completo: "COMPLETO", parcial: "PARCIAL", aberto: "ABERTA" };

function renderNivel(n) {
  const itens = n.itens.map((m) => {
    if (!n.liberado) {
      return `
      <div class="arena-card trancado">
        <span class="arena-card-topo"><span class="arena-cod">${escapar(m.codigo)}</span>
          <i data-lucide="lock" role="img" aria-label="Bloqueada"></i></span>
        <span class="arena-card-corpo"><span class="arena-modulo">Bloqueada</span>
          <span class="arena-tecnico">${escapar(n.dica || "Ainda bloqueado.")}</span></span>
        <span class="arena-rodape-card"><span>até ${m.pontos} pts</span></span>
      </div>`;
    }
    const estado = m.completo ? "completo" : m.melhor ? "parcial" : "aberto";
    const pts = m.melhor ? `${m.melhor.pontos}/${m.pontos} pts` : `${m.pontos} pts`;
    const pct = m.completo ? 100 : m.melhor && m.pontos ? Math.round((100 * m.melhor.pontos) / m.pontos) : 0;
    return `
      <a class="arena-card ${estado}" href="/ide.html?desafio=${encodeURIComponent(m.codigo)}">
        <span class="arena-card-topo"><span class="arena-cod nivel-${escapar(n.nivel)}">${escapar(m.codigo)}</span>
          <span class="arena-estado">${ROTULO_ESTADO[estado]}</span></span>
        <span class="arena-card-corpo"><span class="arena-modulo">${escapar(m.modulo)}</span>
          <span class="arena-tecnico">${escapar(m.problemaTecnico)}</span></span>
        <span class="arena-barra" aria-hidden="true"><span style="width: ${pct}%"></span></span>
        <span class="arena-rodape-card">
          <span>${offline ? "salve o .por na IDE" : m.tentativas ? `${m.tentativas} tentativa(s)` : "sem tentativas"}</span>
          <span class="arena-pts">${pts}${m.completo ? " ✅" : ""}</span>
        </span>
      </a>`;
  }).join("");
  return `
    <section class="arena-nivel-bloco ${n.liberado ? "" : "trancado"}">
      <h2 class="arena-nivel-titulo"><span class="a-selo a-chanfro nivel-${escapar(n.nivel)}">${escapar(n.nivel)}</span>
        <small>${SUBTITULO[n.nivel] || ""}</small></h2>
      <div class="arena-grade">${itens}</div>
    </section>`;
}

function renderProgresso(niveis) {
  const todos = niveis.flatMap((n) => n.itens);
  const completos = todos.filter((m) => m.completo).length;
  $("progresso-texto").textContent = `${completos} / ${todos.length}`;
  $("progresso-barra").innerHTML = todos
    .map((m) => `<span class="${m.completo ? "completo" : m.melhor ? "parcial" : ""}"></span>`).join("");
}

function atualizarRelogio() {
  if (!janela) return;
  const { valor, rotulo } = textoRelogio(janela, Date.now() / 1000 + deslocamentoRelogio);
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
  offline = Boolean(p.offline);
  deslocamentoRelogio = p.janela.agora - Date.now() / 1000;

  $("tela-login").classList.add("hidden");
  $("tela-painel").classList.remove("hidden");
  $("evento-nome").textContent = p.evento;
  $("equipe-nome").textContent = p.equipe.nome;
  $("topo-equipe").textContent = p.equipe.nome;
  $("kpi-pontos").textContent = offline ? "—" : p.equipe.pontos;
  $("btn-sair").classList.toggle("hidden", offline);

  const sit = {
    antes: "🕖 A Code Arena ainda não abriu. As missões aparecem aqui no horário de início.",
    aberta: "🟢 EM ANDAMENTO — escolha um módulo para recuperar.",
    encerrada: "🏁 Submissões encerradas. Aguarde o resultado.",
  };
  $("situacao").textContent = offline
    ? "💾 MODO OFFLINE — resolva na IDE e salve cada missão com o botão Salvar .por. A banca pontua os arquivos."
    : (p.janela.ensaio ? "🧪 MODO ENSAIO · " : "") + sit[p.janela.situacao];
  $("niveis").innerHTML = p.niveis.map(renderNivel).join("");
  renderProgresso(p.niveis);
  atualizarRelogio();
  icones();
}

// Sem sessão também pergunta ao servidor: no modo offline ele responde sem login (senão, 401 → tela de login).
carregarPainel();
setInterval(atualizarRelogio, 1000);
setInterval(() => { if (sessao() || offline) carregarPainel(); }, 30000);
