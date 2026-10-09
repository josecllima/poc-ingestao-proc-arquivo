import { Fragment, useEffect, useState } from "react";
import { api, STATUS_FINAIS_LOTE } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import { dataHora, tamanho, tempo } from "../formato";
import { usePolling } from "../usePolling";

export function LoteDetalhe({ id, voltar }: { id: number; voltar: () => void }) {
  const { dados: lote, erro, setAtivo } = usePolling(() => api.obterLote(id), 2000, [id]);
  const [aberto, setAberto] = useState<number | null>(null);

  // quando o lote termina, para de consultar a API
  const finalizado = !!lote && STATUS_FINAIS_LOTE.includes(lote.status);
  useEffect(() => setAtivo(!finalizado), [finalizado, setAtivo]);

  return (
    <section className="cartao">
      <button className="link" onClick={voltar}>← Voltar para os lotes</button>
      {erro && <p className="msg msg-erro">{erro}</p>}
      {lote && (
        <>
          <div className="cabecalho">
            <h2>Lote #{lote.loteId} – {lote.nomeZip}</h2>
            <StatusBadge status={lote.status} />
            <a className="botao-download" href={api.urlZip(lote.loteId)} download>⬇ Baixar ZIP original</a>
          </div>
          {lote.erro && <p className="msg msg-erro">{lote.erro}</p>}

          <div className="barra">
            <div className={`barra-preenchida ${lote.quantidades.erros ? "com-erros" : ""}`} style={{ width: `${lote.progresso}%` }} />
            <span>{lote.progresso}%</span>
          </div>

          <div className="indicadores">
            <Indicador rotulo="Arquivos" valor={lote.quantidades.total} />
            <Indicador rotulo="Sucesso" valor={lote.quantidades.sucesso} />
            <Indicador rotulo="Erros" valor={lote.quantidades.erros} destaque={lote.quantidades.erros > 0} />
            <Indicador rotulo="Ignorados" valor={lote.quantidades.ignorados} />
            <Indicador rotulo="Pendentes" valor={lote.quantidades.pendentes} />
          </div>
          <p className="ajuda">
            Recebido em {dataHora(lote.recebidoEm)} · Concluído em {dataHora(lote.concluidoEm)}
            {!finalizado && " · atualizando a cada 2 s"}
          </p>

          <table>
            <thead>
              <tr>
                <th>Arquivo</th><th>Extensão</th><th>Tamanho</th><th>Tipo documental</th>
                <th>Fila</th><th>Status</th><th>Tentativas</th><th>Tempo</th><th>Erro</th><th>Download</th>
              </tr>
            </thead>
            <tbody>
              {lote.arquivos.map((a) => (
                <Fragment key={a.arquivoId}>
                  <tr className={a.resultado ? "clicavel" : ""} onClick={() => setAberto(aberto === a.arquivoId ? null : a.arquivoId)}>
                    <td title={a.caminhoRelativo}>{a.caminhoRelativo}</td>
                    <td>{a.extensao ?? "–"}</td>
                    <td>{tamanho(a.tamanhoBytes)}</td>
                    <td>{a.tipoDocumental ?? "–"}</td>
                    <td>{a.fila ?? "–"}</td>
                    <td><StatusBadge status={a.status} /></td>
                    <td>{a.tentativas}</td>
                    <td>{tempo(a.tempoMs)}</td>
                    <td className="num-erro">{a.erro ?? ""}</td>
                    <td>
                      {a.disponivel ? (
                        <a href={api.urlArquivo(lote.loteId, a.arquivoId)} download={a.nome}
                           title={`Baixar ${a.nome}`} onClick={(e) => e.stopPropagation()}>
                          ⬇ Baixar
                        </a>
                      ) : "–"}
                    </td>
                  </tr>
                  {aberto === a.arquivoId && a.resultado && (
                    <tr className="resultado">
                      <td colSpan={10}><pre>{JSON.stringify(a.resultado, null, 2)}</pre></td>
                    </tr>
                  )}
                </Fragment>
              ))}
              {lote.arquivos.length === 0 && (
                <tr><td colSpan={10} className="vazio">Ainda não há arquivos (o ZIP está sendo extraído).</td></tr>
              )}
            </tbody>
          </table>
          <p className="ajuda">Clique em um arquivo processado para ver o resultado (linhas, colunas, elemento raiz...).</p>
        </>
      )}
    </section>
  );
}

function Indicador({ rotulo, valor, destaque }: { rotulo: string; valor: number; destaque?: boolean }) {
  return (
    <div className={`indicador ${destaque ? "indicador-erro" : ""}`}>
      <strong>{valor}</strong>
      <span>{rotulo}</span>
    </div>
  );
}
