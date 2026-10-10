// Funções puras para interpretar e apresentar erros de compilação do meupia-core.
// Sem dependências de DOM ou Pyodide, para poderem ser testadas com `node --test`.

// O core indenta a mensagem com tab depois de "[COMPILATION ERROR]:".
const REGEX_ERRO_PADRAO = /^[ \t]*(Erro (léxico|sintático|semântico) na linha (\d+), coluna (\d+): (.*))$/m;
const MARCADOR_ERRO = "[COMPILATION ERROR]:";
const REGEX_LOG_LEXER = /^\s*(\(Lexer started\)|Scanning line\b)/;

export const MENSAGEM_BLOCO_ABERTO =
    "Algum bloco não foi fechado. Confira se cada se, enquanto, para, funcao e classe tem o seu fim_… correspondente.";

/**
 * Extrai a mensagem de erro do stdout do compilador.
 * Linha e coluna vêm do core começando em 1 e são devolvidas sem ajuste.
 */
export function extrairMensagemErro(saida) {
    const texto = saida || "";
    const match = texto.match(REGEX_ERRO_PADRAO);

    if (match) {
        return {
            tipo: match[2],
            linha: Number(match[3]),
            coluna: Number(match[4]),
            descricao: match[5].trim(),
            texto: match[1].trim()
        };
    }

    const posMarcador = texto.indexOf(MARCADOR_ERRO);
    const trecho = posMarcador !== -1 ? texto.slice(posMarcador + MARCADOR_ERRO.length) : texto;
    return { tipo: null, linha: null, coluna: null, descricao: null, texto: removerLogDoLexer(trecho) };
}

function removerLogDoLexer(texto) {
    return texto
        .split("\n")
        .filter(linha => !REGEX_LOG_LEXER.test(linha))
        .join("\n")
        .trim();
}

/**
 * Converte a linha do programa montado para a origem do erro.
 * info = null fora de desafio; senão { linhaUsarTestes, inicioAnexo, linhaFimAnexado }.
 */
export function mapearLinhaErro(linhaMontada, info) {
    if (!info) return { origem: "editor", linha: linhaMontada };

    if (linhaMontada === info.linhaFimAnexado) return { origem: "bloco-aberto" };
    if (linhaMontada >= info.inicioAnexo) return { origem: "testes" };
    if (linhaMontada === info.linhaUsarTestes) return { origem: "testes" };

    if (info.linhaUsarTestes !== null && linhaMontada > info.linhaUsarTestes) {
        return { origem: "editor", linha: linhaMontada - 1 };
    }
    return { origem: "editor", linha: linhaMontada };
}

/**
 * Monta a mensagem final mostrada no terminal.
 */
export function formatarMensagemErro(erro, mapeado) {
    if (erro.linha === null || !mapeado) return erro.texto;

    if (mapeado.origem === "bloco-aberto") return MENSAGEM_BLOCO_ABERTO;
    if (mapeado.origem === "testes") return `Erro nos testes automáticos do desafio: ${erro.descricao}`;

    return `Erro ${erro.tipo} na linha ${mapeado.linha}, coluna ${erro.coluna}: ${erro.descricao}`;
}
