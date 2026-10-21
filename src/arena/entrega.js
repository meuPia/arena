// Modo offline (submissao.js): o arquivo que a equipe entrega à banca. A 1ª linha diz o desafio (scripts/pontuar_equipe.py lê
// dela, então renomear o arquivo não atrapalha). É comentário: não conta nos caracteres significativos.
const CABECALHO = /^\s*\/\/\s*arena:\s*[A-Za-z]\d{2}\b[^\n]*\n?/;

export function comCabecalho(fonte, codigo) {
  return `// arena: ${codigo}\n` + fonte.replace(CABECALHO, "");
}

export const nomeArquivo = (codigo) => `${codigo}.por`;
