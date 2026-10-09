// A API devolve datas em UTC sem fuso ("2026-10-08T22:44:01"). Aqui viram horário local.
export function dataHora(valor: string | null | undefined): string {
  if (!valor) return "–";
  const iso = /[zZ]|[+-]\d\d:\d\d$/.test(valor) ? valor : `${valor}Z`;
  return new Date(iso).toLocaleString("pt-BR");
}

export function tempo(ms: number | null | undefined): string {
  if (ms == null) return "–";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)} s`;
  return `${(ms / 60_000).toFixed(1)} min`;
}

export function tamanho(bytes: number | null | undefined): string {
  if (bytes == null) return "–";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
