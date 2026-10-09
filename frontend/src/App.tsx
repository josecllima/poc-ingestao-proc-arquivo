import { useEffect, useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { LoteDetalhe } from "./pages/LoteDetalhe";
import { Lotes } from "./pages/Lotes";
import { Upload } from "./pages/Upload";

// Navegação simples pelo endereço (#/lotes, #/lotes/15...), sem biblioteca de rotas.
function lerRota() {
  const partes = window.location.hash.replace(/^#\/?/, "").split("/");
  if (partes[0] === "lotes" && partes[1]) return { tela: "detalhe" as const, id: Number(partes[1]) };
  if (partes[0] === "lotes") return { tela: "lotes" as const };
  if (partes[0] === "dashboard") return { tela: "dashboard" as const };
  return { tela: "upload" as const };
}

export function App() {
  const [rota, setRota] = useState(lerRota);
  useEffect(() => {
    const aoMudar = () => setRota(lerRota());
    window.addEventListener("hashchange", aoMudar);
    return () => window.removeEventListener("hashchange", aoMudar);
  }, []);

  const ir = (hash: string) => { window.location.hash = hash; };
  const abrirLote = (id: number) => ir(`/lotes/${id}`);

  return (
    <>
      <header>
        <h1>Ingestão de Arquivos</h1>
        <nav>
          <a className={rota.tela === "upload" ? "ativo" : ""} href="#/">Upload</a>
          <a className={rota.tela === "lotes" || rota.tela === "detalhe" ? "ativo" : ""} href="#/lotes">Lotes</a>
          <a className={rota.tela === "dashboard" ? "ativo" : ""} href="#/dashboard">Dashboard</a>
        </nav>
      </header>
      <main>
        {rota.tela === "upload" && <Upload abrirLote={abrirLote} />}
        {rota.tela === "lotes" && <Lotes abrirLote={abrirLote} />}
        {rota.tela === "detalhe" && <LoteDetalhe id={rota.id} voltar={() => ir("/lotes")} />}
        {rota.tela === "dashboard" && <Dashboard />}
      </main>
    </>
  );
}
