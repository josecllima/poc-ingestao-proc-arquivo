import { useState } from "react";
import { api } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import { dataHora } from "../formato";
import { usePolling } from "../usePolling";

const TAMANHO = 10;
const FILTROS = ["", "RECEBIDO", "PROCESSANDO", "CONCLUIDO", "CONCLUIDO_COM_ERROS", "ERRO"];

export function Lotes({ abrirLote }: { abrirLote: (id: number) => void }) {
  const [pagina, setPagina] = useState(1);
  const [status, setStatus] = useState("");
  const { dados, erro } = usePolling(() => api.listarLotes(pagina, TAMANHO, status), 3000, [pagina, status]);
  const totalPaginas = dados ? Math.max(1, Math.ceil(dados.total / TAMANHO)) : 1;

  return (
    <section className="cartao">
      <div className="cabecalho">
        <h2>Lotes</h2>
        <label>
          Status:{" "}
          <select value={status} onChange={(e) => { setStatus(e.target.value); setPagina(1); }}>
            {FILTROS.map((f) => <option key={f} value={f}>{f ? f.replace(/_/g, " ") : "Todos"}</option>)}
          </select>
        </label>
      </div>
      {erro && <p className="msg msg-erro">{erro}</p>}

      <table>
        <thead>
          <tr>
            <th>#</th><th>ZIP</th><th>Status</th><th>Arquivos</th><th>Sucesso</th>
            <th>Erros</th><th>Ignorados</th><th>Pendentes</th><th>Recebido em</th>
          </tr>
        </thead>
        <tbody>
          {dados?.itens.map((l) => (
            <tr key={l.loteId} className="clicavel" onClick={() => abrirLote(l.loteId)}>
              <td>{l.loteId}</td>
              <td title={l.erro ?? ""}>{l.nomeZip}</td>
              <td><StatusBadge status={l.status} /></td>
              <td>{l.quantidades.total}</td>
              <td>{l.quantidades.sucesso}</td>
              <td className={l.quantidades.erros ? "num-erro" : ""}>{l.quantidades.erros}</td>
              <td>{l.quantidades.ignorados}</td>
              <td>{l.quantidades.pendentes}</td>
              <td>{dataHora(l.recebidoEm)}</td>
            </tr>
          ))}
          {dados && dados.itens.length === 0 && (
            <tr><td colSpan={9} className="vazio">Nenhum lote encontrado.</td></tr>
          )}
        </tbody>
      </table>

      <div className="paginacao">
        <button disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>← Anterior</button>
        <span>Página {pagina} de {totalPaginas} {dados ? `(${dados.total} lotes)` : ""}</span>
        <button disabled={pagina >= totalPaginas} onClick={() => setPagina(pagina + 1)}>Próxima →</button>
      </div>
    </section>
  );
}
