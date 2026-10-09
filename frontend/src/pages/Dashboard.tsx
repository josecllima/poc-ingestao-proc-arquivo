import { api, Contagem } from "../api";
import { tempo } from "../formato";
import { usePolling } from "../usePolling";

export function Dashboard() {
  const { dados, erro } = usePolling(() => api.dashboard(), 5000);

  return (
    <section>
      {erro && <p className="msg msg-erro">{erro}</p>}
      {dados && (
        <>
          <div className="indicadores">
            <div className="indicador"><strong>{dados.lotes.total}</strong><span>Lotes</span></div>
            <div className="indicador"><strong>{dados.lotes.concluidos}</strong><span>Concluídos</span></div>
            <div className="indicador"><strong>{dados.lotes.concluidosComErros}</strong><span>Concluídos com erros</span></div>
            <div className="indicador indicador-erro"><strong>{dados.lotes.comErro}</strong><span>Com erro</span></div>
            <div className="indicador"><strong>{dados.lotes.emAndamento}</strong><span>Em andamento</span></div>
          </div>

          <div className="grade">
            <Barras titulo="Arquivos por extensão" itens={dados.arquivosPorExtensao} />
            <Barras titulo="Arquivos por tipo documental" itens={dados.arquivosPorTipo} />
            <Barras titulo="Arquivos por status" itens={dados.arquivosPorStatus} />

            <div className="cartao">
              <h3>Tempos médios</h3>
              <p>Por arquivo: <strong>{tempo(dados.tempoMedioArquivoMs)}</strong></p>
              <p>Por lote (do recebimento à conclusão): <strong>{tempo(dados.tempoMedioLoteMs)}</strong></p>
              <table>
                <thead><tr><th>Fila</th><th>Arquivos</th><th>Média</th></tr></thead>
                <tbody>
                  {dados.tempoMedioPorFila.map((f) => (
                    <tr key={f.fila}><td>{f.fila}</td><td>{f.arquivos}</td><td>{tempo(f.mediaMs)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function Barras({ titulo, itens }: { titulo: string; itens: Contagem[] }) {
  const maximo = Math.max(1, ...itens.map((i) => i.quantidade));
  return (
    <div className="cartao">
      <h3>{titulo}</h3>
      {itens.length === 0 && <p className="vazio">Sem dados ainda.</p>}
      {itens.map((i) => (
        <div key={i.chave} className="barra-h">
          <span className="barra-h-rotulo" title={i.chave}>{i.chave.replace(/_/g, " ")}</span>
          <div className="barra-h-trilho">
            <div className="barra-h-valor" style={{ width: `${(i.quantidade / maximo) * 100}%` }} />
          </div>
          <span className="barra-h-num">{i.quantidade}</span>
        </div>
      ))}
    </div>
  );
}
