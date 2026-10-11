// Botão Submeter da IDE: escolhe participantes, envia ao juiz e mostra o veredito.
import { api, escapar, formatarRelogio, textoRelogio } from "./api.js";

const fracao = (b) => `${b.aprovados}/${b.total}`;
const MOTIVO_EXEMPLO = {
  tempo: " — um exemplo passou do tempo (laço infinito?)",
  excecao: " — um exemplo deu erro durante a execução",
};

const MENSAGENS = {
  aceito: (r) => r.completo
    ? `✅ ACEITO — ${fracao(r.extras)} testes extras · ${r.pontos}/${r.pontosModulo} pts · ${r.caracteres} caracteres`
    : `🟡 ACEITO PARCIAL — ${fracao(r.extras)} extras · ${r.pontos}/${r.pontosModulo} pts`,
  reprovado_exemplos: (r) =>
    `❌ Passe primeiro em todos os testes de exemplo (${fracao(r.exemplos)})${MOTIVO_EXEMPLO[r.falhaExemplo] || ""}`,
  erro_compilacao: (r) => `🛠️ ERRO DE COMPILAÇÃO${r.linha ? ` (linha ${r.linha})` : ""}: ${r.mensagem}`,
  erro_execucao: (r) => `💥 ${r.mensagem}`,
  cooldown: (r) => `⏳ ${r.mensagem}`,
};

// "Melhor: 7/10 pts" (+ selo de completo e caracteres)
function textoMelhor(melhor, pontosModulo) {
  if (!melhor) return "";
  return `Melhor da equipe: ${melhor.pontos}/${pontosModulo} pts${melhor.completo ? " ✅ completo" : ""} · ${melhor.caracteres} caracteres`;
}

export function setupSubmissao(view, desafio) {
  const btn = document.getElementById("submit-btn");
  const modal = document.getElementById("submit-modal");
  const lista = document.getElementById("participantes-lista");
  const confirmar = document.getElementById("confirm-submit-btn");
  let fimEspera = 0;
  let timer = null;

  // Cabeçalho da IDE: código (na cor do nível), módulo e melhor pontuação
  const topo = document.getElementById("missao-topo");
  if (topo) {
    topo.innerHTML = `<span class="a-selo a-chanfro nivel-${escapar(desafio.nivel)}">${escapar(desafio.codigo)}</span>
      <strong>${escapar(desafio.modulo || "")}</strong><span class="arena-missao-sub">${escapar(desafio.problemaTecnico || "")}</span>
      <span id="arena-melhor-topo" class="arena-missao-melhor"></span>
      <span class="arena-missao-relogio a-chanfro" aria-live="off"><small id="ide-relogio-rotulo"></small><span id="ide-relogio">--:--</span></span>`;
  }

  // Cronômetro do evento (mesmo cálculo do painel, com o "agora" do servidor)
  if (desafio.janela) {
    const deslocamento = desafio.janela.agora - Date.now() / 1000;
    const tique = () => {
      const { valor, rotulo } = textoRelogio(desafio.janela, Date.now() / 1000 + deslocamento);
      const v = document.getElementById("ide-relogio"), r = document.getElementById("ide-relogio-rotulo");
      if (v) v.textContent = valor;
      if (r) r.textContent = rotulo;
    };
    tique();
    setInterval(tique, 1000);
  }

  // Cabeçalho da missão no painel de instruções
  const header = document.querySelector(".desafio-header");
  if (header) {
    header.insertAdjacentHTML("beforeend",
      `<div class="arena-meta"><span class="arena-nivel nivel-${escapar(desafio.nivel)}">${escapar(desafio.nivel)} · ${desafio.pontos} pts</span>
       <span>⏱️ ${escapar(desafio.tempoEsperado)}</span><span id="arena-status-missao"></span></div>`);
  }

  function atualizarStatus() {
    const topoMelhor = document.getElementById("arena-melhor-topo");
    if (topoMelhor) {
      const mt = desafio.melhor;
      topoMelhor.textContent = mt ? `melhor ${mt.pontos}/${desafio.pontos} pts${mt.completo ? " ✅" : ""}` : `${desafio.pontos} pts`;
    }
    const el = document.getElementById("arena-status-missao");
    if (!el) return;
    const m = desafio.melhor;
    el.textContent = (m ? `Melhor: ${m.pontos}/${desafio.pontos} pts${m.completo ? " ✅" : ""} · ` : "")
      + `Tentativas: ${desafio.tentativas}`;
  }
  atualizarStatus();

  function iniciarEspera(segundos) {
    fimEspera = Date.now() + segundos * 1000;
    clearInterval(timer);
    const tick = () => {
      const resta = Math.ceil((fimEspera - Date.now()) / 1000);
      if (resta <= 0) {
        clearInterval(timer);
        btn.innerHTML = '<i data-lucide="send"></i> Submeter';
        btn.disabled = desafio.situacao !== "aberta";
      } else {
        btn.disabled = true;
        btn.innerHTML = `<i data-lucide="hourglass"></i> ${formatarRelogio(resta)}`;
      }
      if (window.lucide) window.lucide.createIcons();
    };
    tick();
    timer = setInterval(tick, 1000);
  }

  // Participantes: lista da equipe ou campo livre
  const integrantes = desafio.integrantes || [];
  lista.innerHTML = integrantes.length
    ? integrantes.map((nome, i) =>
        `<label class="arena-check"><input type="checkbox" value="${escapar(nome)}" id="part-${i}"> ${escapar(nome)}</label>`).join("")
    : `<input type="text" id="part-livre" placeholder="Nomes separados por vírgula" class="arena-input">`;

  function participantesMarcados() {
    const livre = document.getElementById("part-livre");
    if (livre) return livre.value.split(",").map((s) => s.trim()).filter(Boolean);
    return [...lista.querySelectorAll("input:checked")].map((i) => i.value);
  }

  btn.addEventListener("click", () => modal.classList.remove("hidden"));
  document.getElementById("close-submit-btn").addEventListener("click", () => modal.classList.add("hidden"));

  confirmar.addEventListener("click", async () => {
    const participantes = participantesMarcados();
    if (!participantes.length) {
      alert("Marque pelo menos um integrante.");
      return;
    }
    modal.classList.add("hidden");
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader"></i> Julgando...';
    if (window.lucide) window.lucide.createIcons();

    let r;
    try {
      r = await api.submeter(desafio.codigo, view.state.doc.toString(), participantes);
    } catch (e) {
      r = { status: "erro_execucao", mensagem: e.message, espera: 0 };
    }
    mostrarVeredito(r);
    if (r.melhor !== undefined) desafio.melhor = r.melhor;
    if (r.tentativa) desafio.tentativas = r.tentativa;
    atualizarStatus();
    iniciarEspera(r.espera || 0);
  });

  function mostrarVeredito(r) {
    let texto = (MENSAGENS[r.status] || ((x) => x.mensagem || x.status))(r);
    if (r.status === "aceito" && r.melhor) texto += "\n" + textoMelhor(r.melhor, r.pontosModulo);
    const cls = r.status !== "aceito" ? "fail" : r.completo ? "success" : "parcial";
    let box = document.getElementById("arena-veredito");
    if (!box) {
      box = document.createElement("div");
      box.id = "arena-veredito";
      document.querySelector(".desafio-instrucoes")?.before(box);
    }
    box.className = `arena-veredito ${cls}`;
    box.textContent = texto;
  }

  if (desafio.situacao !== "aberta") {
    btn.title = "Submissões fechadas";
  }
  iniciarEspera(desafio.espera || 0);
}
