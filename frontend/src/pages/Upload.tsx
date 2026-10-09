import { useState } from "react";
import { api, RespostaUpload } from "../api";
import { StatusBadge } from "../components/StatusBadge";

export function Upload({ abrirLote }: { abrirLote: (id: number) => void }) {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [progresso, setProgresso] = useState<number | null>(null);
  const [resultado, setResultado] = useState<RespostaUpload | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar() {
    if (!arquivo) return;
    setErro(null);
    setResultado(null);
    setProgresso(0);
    try {
      setResultado(await api.enviarLote(arquivo, setProgresso));
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setProgresso(null);
    }
  }

  const ehZip = !arquivo || arquivo.name.toLowerCase().endsWith(".zip");

  return (
    <section className="cartao">
      <h2>Enviar lote</h2>
      <p className="ajuda">Selecione um arquivo .zip. O processamento é assíncrono: a API responde na hora e o lote é processado em segundo plano.</p>

      <div className="linha">
        <input
          type="file"
          accept=".zip"
          onChange={(e) => {
            setArquivo(e.target.files?.[0] ?? null);
            setResultado(null);
            setErro(null);
          }}
        />
        <button onClick={enviar} disabled={!arquivo || !ehZip || progresso !== null}>
          {progresso !== null ? "Enviando..." : "Enviar"}
        </button>
      </div>

      {!ehZip && <p className="msg msg-erro">Selecione um arquivo com extensão .zip.</p>}

      {progresso !== null && (
        <div className="barra" aria-label="progresso do envio">
          <div className="barra-preenchida" style={{ width: `${progresso}%` }} />
          <span>{progresso}%</span>
        </div>
      )}

      {erro && <p className="msg msg-erro">{erro}</p>}

      {resultado && (
        <div className={`msg ${resultado.duplicado ? "msg-alerta" : "msg-ok"}`}>
          {resultado.duplicado
            ? <>Este ZIP já foi enviado antes. Lote existente: <strong>#{resultado.loteId}</strong> </>
            : <>Lote <strong>#{resultado.loteId}</strong> recebido ({resultado.nomeZip}) </>}
          <StatusBadge status={resultado.status} />{" "}
          <button className="link" onClick={() => abrirLote(resultado.loteId)}>Acompanhar lote →</button>
        </div>
      )}
    </section>
  );
}
