const CORES: Record<string, string> = {
  RECEBIDO: "neutro", EXTRAINDO: "andamento", CLASSIFICANDO: "andamento", PROCESSANDO: "andamento",
  PENDENTE: "neutro", PUBLICADO: "andamento", IDENTIFICADO: "neutro",
  CONCLUIDO: "ok", PROCESSADO: "ok", ARMAZENADO: "ok",
  CONCLUIDO_COM_ERROS: "alerta", IGNORADO: "neutro",
  ERRO: "erro",
};

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${CORES[status] ?? "neutro"}`}>{status.replace(/_/g, " ")}</span>;
}
