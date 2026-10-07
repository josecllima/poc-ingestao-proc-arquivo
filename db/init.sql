IF DB_ID('poc_ingestao_proc_arquivo') IS NULL CREATE DATABASE poc_ingestao_proc_arquivo;
GO
USE poc_ingestao_proc_arquivo;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID('dbo.lote') IS NULL
CREATE TABLE dbo.lote (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    nome_zip        NVARCHAR(255)  NOT NULL,
    hash_sha256     CHAR(64)       NULL,
    status          VARCHAR(30)    NOT NULL,
    total_arquivos  INT            NULL,
    mensagem_erro   NVARCHAR(1000) NULL,
    recebido_em     DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
    concluido_em    DATETIME2      NULL
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ux_lote_hash')
CREATE UNIQUE INDEX ux_lote_hash ON dbo.lote(hash_sha256) WHERE hash_sha256 IS NOT NULL;
GO

IF OBJECT_ID('dbo.arquivo') IS NULL
CREATE TABLE dbo.arquivo (
    id                INT IDENTITY(1,1) PRIMARY KEY,
    lote_id           INT            NOT NULL REFERENCES dbo.lote(id),
    nome              NVARCHAR(255)  NOT NULL,
    caminho_relativo  NVARCHAR(500)  NOT NULL,
    caminho_storage   NVARCHAR(500)  NULL,
    extensao          VARCHAR(20)    NULL,
    tamanho_bytes     BIGINT         NULL,
    tipo_documental   VARCHAR(50)    NULL,
    fila              VARCHAR(30)    NULL,
    status            VARCHAR(20)    NOT NULL,
    tentativas        INT            NOT NULL DEFAULT 0,
    resultado         NVARCHAR(MAX)  NULL,
    erro              NVARCHAR(1000) NULL,
    criado_em         DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
    iniciado_em       DATETIME2      NULL,
    finalizado_em     DATETIME2      NULL
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_arquivo_lote_status')
CREATE INDEX ix_arquivo_lote_status ON dbo.arquivo(lote_id, status);
GO
