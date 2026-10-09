"""Consultas de leitura para a tela (lista de lotes, detalhes e dashboard).

Ficam separadas dos repositórios de escrita: aqui só há SELECTs, escritos
em SQL direto porque são agregações (GROUP BY, AVG, paginação).
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

_CONTAGENS = """
    SUM(CASE WHEN a.status IN ('PROCESSADO', 'ARMAZENADO') THEN 1 ELSE 0 END) AS sucesso,
    SUM(CASE WHEN a.status = 'ERRO' THEN 1 ELSE 0 END) AS erros,
    SUM(CASE WHEN a.status = 'IGNORADO' THEN 1 ELSE 0 END) AS ignorados,
    SUM(CASE WHEN a.status IN ('IDENTIFICADO', 'PENDENTE', 'PUBLICADO', 'PROCESSANDO') THEN 1 ELSE 0 END) AS pendentes,
    COUNT(a.id) AS arquivos
"""


def quantidades(linha) -> dict:
    return {
        "total": linha.arquivos or 0,
        "sucesso": linha.sucesso or 0,
        "erros": linha.erros or 0,
        "ignorados": linha.ignorados or 0,
        "pendentes": linha.pendentes or 0,
    }


def listar_lotes(session: Session, pagina: int, tamanho: int, status: str | None) -> dict:
    filtro, params = "", {"offset": (pagina - 1) * tamanho, "tamanho": tamanho}
    if status:
        filtro, params["status"] = "WHERE l.status = :status", status

    total = session.execute(text(f"SELECT COUNT(*) FROM lote l {filtro}"), params).scalar_one()
    linhas = session.execute(text(f"""
        SELECT l.id, l.nome_zip, l.status, l.mensagem_erro, l.recebido_em, l.concluido_em, {_CONTAGENS}
          FROM lote l LEFT JOIN arquivo a ON a.lote_id = l.id
          {filtro}
         GROUP BY l.id, l.nome_zip, l.status, l.mensagem_erro, l.recebido_em, l.concluido_em
         ORDER BY l.id DESC
        OFFSET :offset ROWS FETCH NEXT :tamanho ROWS ONLY
    """), params).all()

    return {
        "pagina": pagina,
        "tamanho": tamanho,
        "total": total,
        "itens": [{
            "loteId": r.id, "nomeZip": r.nome_zip, "status": r.status, "erro": r.mensagem_erro,
            "recebidoEm": r.recebido_em, "concluidoEm": r.concluido_em, "quantidades": quantidades(r),
        } for r in linhas],
    }


def resumo_do_lote(session: Session, lote_id: int):
    return session.execute(text(f"""
        SELECT l.id, l.nome_zip, l.status, l.mensagem_erro, l.total_arquivos, l.recebido_em, l.concluido_em,
               {_CONTAGENS}
          FROM lote l LEFT JOIN arquivo a ON a.lote_id = l.id
         WHERE l.id = :id
         GROUP BY l.id, l.nome_zip, l.status, l.mensagem_erro, l.total_arquivos, l.recebido_em, l.concluido_em
    """), {"id": lote_id}).first()


def dashboard(session: Session) -> dict:
    def agrupar(coluna: str, vazio: str) -> list[dict]:
        # O parâmetro fica só na subconsulta: no SQL Server, cada :vazio vira um parâmetro
        # diferente, e "GROUP BY COALESCE(col, @P2)" não casa com "SELECT COALESCE(col, @P1)".
        linhas = session.execute(text(f"""
            SELECT t.chave, COUNT(*) AS qtd
              FROM (SELECT COALESCE({coluna}, :vazio) AS chave FROM arquivo) AS t
             GROUP BY t.chave
             ORDER BY qtd DESC
        """), {"vazio": vazio}).all()
        return [{"chave": r.chave, "quantidade": r.qtd} for r in linhas]

    tempos = session.execute(text("""
        SELECT COALESCE(fila, '(sem fila)') AS fila, COUNT(*) AS qtd,
               AVG(CAST(DATEDIFF(MILLISECOND, iniciado_em, finalizado_em) AS FLOAT)) AS media_ms
          FROM arquivo
         WHERE iniciado_em IS NOT NULL AND finalizado_em IS NOT NULL
         GROUP BY fila
    """)).all()
    geral = session.execute(text("""
        SELECT AVG(CAST(DATEDIFF(MILLISECOND, iniciado_em, finalizado_em) AS FLOAT))
          FROM arquivo WHERE iniciado_em IS NOT NULL AND finalizado_em IS NOT NULL
    """)).scalar()
    lote_medio = session.execute(text("""
        SELECT AVG(CAST(DATEDIFF(MILLISECOND, recebido_em, concluido_em) AS FLOAT))
          FROM lote WHERE concluido_em IS NOT NULL
    """)).scalar()
    lotes = session.execute(text("SELECT status, COUNT(*) AS qtd FROM lote GROUP BY status")).all()
    por_status = {r.status: r.qtd for r in lotes}

    return {
        "arquivosPorExtensao": agrupar("extensao", "(sem extensão)"),
        "arquivosPorTipo": agrupar("tipo_documental", "NAO_CLASSIFICADO"),
        "arquivosPorStatus": agrupar("status", "?"),
        "tempoMedioArquivoMs": round(geral, 1) if geral is not None else None,
        "tempoMedioPorFila": [{"fila": r.fila, "arquivos": r.qtd, "mediaMs": round(r.media_ms, 1)} for r in tempos],
        "tempoMedioLoteMs": round(lote_medio, 1) if lote_medio is not None else None,
        "lotes": {
            "total": sum(por_status.values()),
            "concluidos": por_status.get("CONCLUIDO", 0),
            "concluidosComErros": por_status.get("CONCLUIDO_COM_ERROS", 0),
            "comErro": por_status.get("ERRO", 0),
            "emAndamento": sum(q for s, q in por_status.items()
                               if s not in ("CONCLUIDO", "CONCLUIDO_COM_ERROS", "ERRO")),
            "porStatus": por_status,
        },
    }
