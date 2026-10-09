import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Busca dados e repete a cada `intervaloMs` enquanto `ativo` for true.
 * É a "consulta periódica à API" que o desafio aceita (SSE/WebSocket seriam diferencial).
 */
export function usePolling<T>(buscar: () => Promise<T>, intervaloMs: number, deps: unknown[] = []) {
  const [dados, setDados] = useState<T | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [ativo, setAtivo] = useState(true);
  const buscarRef = useRef(buscar);
  buscarRef.current = buscar;

  const recarregar = useCallback(async () => {
    try {
      setDados(await buscarRef.current());
      setErro(null);
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    setAtivo(true);
    void recarregar();
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!ativo) return;
    const id = window.setInterval(() => void recarregar(), intervaloMs);
    return () => window.clearInterval(id);
  }, [ativo, intervaloMs, recarregar]);

  return { dados, erro, recarregar, setAtivo };
}
