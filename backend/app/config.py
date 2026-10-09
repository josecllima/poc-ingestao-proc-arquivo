from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "sqlserver"
    db_port: int = 1433
    db_name: str = "poc_ingestao_proc_arquivo"
    db_user: str = "sa"
    db_password: str

    rabbit_host: str = "rabbitmq"
    rabbit_port: int = 5672
    rabbit_user: str
    rabbit_password: str

    storage_path: str = "/storage"
    max_zip_mb: int = 100
    max_arquivos_por_lote: int = 500
    max_descompactado_mb: int = 500
    max_tentativas: int = 3
    retencao_dias: int = 30  # app.manutencao.retencao apaga do storage lotes finalizados há mais tempo
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def database_url(self) -> str:
        senha = quote_plus(self.db_password)  # escapa caracteres como @ e #
        return (
            f"mssql+pyodbc://{self.db_user}:{senha}@{self.db_host}:{self.db_port}/{self.db_name}"
            "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        )


settings = Settings()