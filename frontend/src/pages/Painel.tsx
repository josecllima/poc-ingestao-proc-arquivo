import { API_URL, api } from "../api";
import { usePolling } from "../usePolling";

// Endereço do painel do RabbitMQ: mesmo host do front, porta 15672.
const RABBIT_URL = `${window.location.protocol}//${window.location.hostname}:15672`;
const FRONT_URL = `${window.location.origin}${window.location.pathname}`;

interface Link {
  titulo: string;
  descricao: string;
  url: string;
  rotulo: string;
}

const GRUPOS: { titulo: string; links: Link[] }[] = [
  {
    titulo: "Aplicação",
    links: [
      { titulo: "Tela principal – Upload", descricao: "Enviar um ZIP para processamento", url: `${FRONT_URL}#/`, rotulo: "#/" },
      { titulo: "Lotes", descricao: "Lista de lotes, progresso, detalhes e download dos arquivos", url: `${FRONT_URL}#/lotes`, rotulo: "#/lotes" },
      { titulo: "Dashboard", descricao: "Arquivos por tipo, status e tempos médios", url: `${FRONT_URL}#/dashboard`, rotulo: "#/dashboard" },
    ],
  },
  {
    titulo: "API – documentação",
    links: [
      { titulo: "Swagger", descricao: "Testar os endpoints direto no navegador", url: `${API_URL}/docs`, rotulo: "/docs" },
      { titulo: "ReDoc", descricao: "Documentação da API para leitura", url: `${API_URL}/redoc`, rotulo: "/redoc" },
    ],
  },
  {
    titulo: "API – endpoints (JSON)",
    links: [
      { titulo: "Status (health)", descricao: "API, banco e fila estão respondendo?", url: `${API_URL}/health`, rotulo: "GET /health" },
      { titulo: "Lotes", descricao: "Lista paginada dos lotes", url: `${API_URL}/lotes`, rotulo: "GET /lotes" },
      { titulo: "Dashboard", descricao: "Indicadores consolidados", url: `${API_URL}/dashboard`, rotulo: "GET /dashboard" },
    ],
  },
  {
    titulo: "Mensageria",
    links: [
      { titulo: "RabbitMQ – Filas", descricao: "Mensagens em cada fila, retry e DLQ", url: `${RABBIT_URL}/#/queues`, rotulo: ":15672/#/queues" },
      { titulo: "RabbitMQ – Visão geral", descricao: "Conexões, consumidores (workers) e taxa de mensagens", url: `${RABBIT_URL}/#/`, rotulo: ":15672" },
    ],
  },
];

type Estado = "ok" | "fora" | "verificando";

export function Painel() {
  // Consulta o /health a cada 10 s: ele informa a API e também o SQL Server e o RabbitMQ.
  const { dados: saude, erro } = usePolling(() => api.saude(), 10000);

  const api_: Estado = erro ? "fora" : saude ? "ok" : "verificando";
  const dependencia = (nome: string): Estado =>
    erro ? "fora" : !saude ? "verificando" : saude.checks[nome] === "ok" ? "ok" : "fora";

  return (
    <section className="cartao">
      <h2 className="painel-titulo">Gerenciando Ingestão de Processamento de Arquivos</h2>
      <p className="ajuda">
        POC – ingestão assíncrona de lotes ZIP (FastAPI · RabbitMQ · SQL Server · React).
        Cada link abre em uma nova aba.
      </p>

      <div className="servicos">
        <Servico nome="Front-end" detalhe=":3000" estado="ok" />
        <Servico nome="API" detalhe=":8000" estado={api_} />
        <Servico nome="SQL Server" detalhe="via /health" estado={dependencia("sqlserver")} />
        <Servico nome="RabbitMQ" detalhe="via /health" estado={dependencia("rabbitmq")} />
        <span className="ajuda">atualiza a cada 10 s</span>
      </div>

      {GRUPOS.map((g) => (
        <div key={g.titulo}>
          <h3 className="grupo-titulo">{g.titulo}</h3>
          <div className="links">
            {g.links.map((l) => (
              <a key={l.url} className="link-card" href={l.url} target="_blank" rel="noopener noreferrer">
                <strong>{l.titulo}</strong>
                <span>{l.descricao}</span>
                <code>{l.rotulo}</code>
              </a>
            ))}
          </div>
        </div>
      ))}

      <p className="ajuda" style={{ marginTop: 24 }}>
        O painel do RabbitMQ pede o usuário e a senha definidos em RABBIT_USER e RABBIT_PASSWORD no arquivo .env.
      </p>
    </section>
  );
}

function Servico({ nome, detalhe, estado }: { nome: string; detalhe: string; estado: Estado }) {
  const classe = estado === "ok" ? "ponto-ok" : estado === "fora" ? "ponto-fora" : "";
  const texto = estado === "ok" ? "No ar" : estado === "fora" ? "Fora do ar" : "Verificando…";
  return (
    <div className="servico" title={texto}>
      <span className={`ponto ${classe}`} />
      {nome} <small>{detalhe}</small>
    </div>
  );
}
