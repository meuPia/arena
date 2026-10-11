// Linhas da tabela do placar: usada pelo telão (placar.js) e pelo placar real do painel (admin.js).
import { escapar } from "./api.js";

const SIMBOLO = { completo: '<span class="bolas">●</span>', parcial: '<span class="meias">◐</span>' };
const NIVEIS = ["Bronze", "Silver", "Gold", "Extra"];

function bolinhas(estados) {
  if (!estados || !estados.length) return "–";
  return estados.map((e) => SIMBOLO[e] || '<span class="vazias">○</span>').join("");
}

export function linhasPlacar(linhas) {
  return linhas.map((l) => `
    <tr>
      <td class="pos">${l.posicao}</td>
      <td class="nome">${escapar(l.nome)}</td>
      ${NIVEIS.map((n) => `<td class="modulos">${bolinhas(l.modulos[n])}</td>`).join("")}
      <td class="pts">${l.pontos}</td>
      <td class="num">${l.completos}</td>
      <td class="num">${l.completos ? l.caracteres : "–"}</td>
    </tr>`).join("");
}

export const CABECALHO_PLACAR = `<tr><th>#</th><th>Equipe</th>${NIVEIS.map((n) => `<th>${n}</th>`).join("")}`
  + "<th>Pontos</th><th>Completos</th><th>Caracteres</th></tr>";
