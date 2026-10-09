// Cliente da API: tipos das respostas + funções de chamada.
// A URL da API vem da variável VITE_API_URL (definida no build); padrão: localhost:8000.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type StatusLote =
  | "RECEBIDO" | "EXTRAINDO" | "CLASSIFICANDO" | "PROCESSANDO"
  | "CONCLUIDO" | "CONCLUIDO_COM_ERROS" | "ERRO";

export interface Quantidades {
  total: number;
  sucesso: number;
  erros: number;
  ignorados: number;
  pendentes: number;
}

export interface LoteResumo {
  loteId: number;
  nomeZip: string;
  status: StatusLote;
  erro: string | null;
  recebidoEm: string;
  concluidoEm: string | null;
  quantidades: Quantidades;
}

export interface PaginaLotes {
  pagina: number;
  tamanho: number;
  total: number;
  itens: LoteResumo[];
}

export interface Arquivo {
  arquivoId: number;
  nome: string;
  caminhoRelativo: string;
  extensao: string | null;
  tamanhoBytes: number | null;
  tipoDocumental: string | null;
  fila: string | null;
  status: string;
  tentativas: number;
  tempoMs: number | null;
  erro: string | null;
  resultado: Record<string, unknown> | null;
}

export interface LoteDetalhe extends LoteResumo {
  progresso: number;
  arquivos: Arquivo[];
}

export interface Contagem {
  chave: string;
  quantidade: number;
}

export interface Dashboard {
  arquivosPorExtensao: Contagem[];
  arquivosPorTipo: Contagem[];
  arquivosPorStatus: Contagem[];
  tempoMedioArquivoMs: number | null;
  tempoMedioPorFila: { fila: string; arquivos: number; mediaMs: number }[];
  tempoMedioLoteMs: number | null;
  lotes: {
    total: number;
    concluidos: number;
    concluidosComErros: number;
    comErro: number;
    emAndamento: number;
  };
}

export interface RespostaUpload {
  loteId: number;
  nomeZip: string;
  status: StatusLote;
  recebidoEm: string;
  duplicado: boolean;
}

export const STATUS_FINAIS_LOTE: StatusLote[] = ["CONCLUIDO", "CONCLUIDO_COM_ERROS", "ERRO"];

async function getJson<T>(caminho: string): Promise<T> {
  const r = await fetch(`${API_URL}${caminho}`);
  if (!r.ok) {
    throw new Error(await mensagemDeErro(r.status, await r.text()));
  }
  return (await r.json()) as T;
}

async function mensagemDeErro(status: number, corpo: string): Promise<string> {
  try {
    const json = JSON.parse(corpo);
    if (typeof json.detail === "string") return json.detail;
  } catch {
    /* corpo não é JSON */
  }
  return `Erro ${status}`;
}

export const api = {
  listarLotes: (pagina: number, tamanho: number, status?: string) =>
    getJson<PaginaLotes>(
      `/lotes?pagina=${pagina}&tamanho=${tamanho}${status ? `&status=${status}` : ""}`,
    ),
  obterLote: (id: number) => getJson<LoteDetalhe>(`/lotes/${id}`),
  dashboard: () => getJson<Dashboard>("/dashboard"),

  /** Upload com progresso: usa XMLHttpRequest porque o fetch não informa o andamento do envio. */
  enviarLote(arquivo: File, aoProgredir: (pct: number) => void): Promise<RespostaUpload> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_URL}/lotes`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) aoProgredir(Math.round((e.loaded / e.total) * 100));
      };
      xhr.onload = async () => {
        if (xhr.status === 200 || xhr.status === 202) {
          resolve(JSON.parse(xhr.responseText) as RespostaUpload);
        } else {
          reject(new Error(await mensagemDeErro(xhr.status, xhr.responseText)));
        }
      };
      xhr.onerror = () => reject(new Error("Não foi possível falar com a API. Ela está no ar?"));
      const form = new FormData();
      form.append("arquivo", arquivo);
      xhr.send(form);
    });
  },
};
