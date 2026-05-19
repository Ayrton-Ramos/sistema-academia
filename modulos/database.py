import psycopg2
import streamlit as st

try:
    if "DATABASE_URL" in st.secrets:
        DATABASE_URL = st.secrets["DATABASE_URL"]
    else:
        DATABASE_URL = "postgresql://neondb_owner:npg_aVzTt25UbWdL@ep-odd-dust-act90b9z.sa-east-1.aws.neon.tech/neondb?sslmode=require"
except Exception:
    DATABASE_URL = "postgresql://neondb_owner:npg_aVzTt25UbWdL@ep-odd-dust-act90b9z.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def obtener_conexao():
    return psycopg2.connect(DATABASE_URL, connect_timeout=5)

def criar_tabela_alunos():
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        
        # Tabela oficial de alunos ativos com EMAIL e SENHA_HASH
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            cpf VARCHAR(11) UNIQUE NOT NULL,
            telefone VARCHAR(20),
            plano VARCHAR(30),
            pagamento_status VARCHAR(10) DEFAULT 'Não OK',
            senha_hash VARCHAR(255),
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Tabela de pré-cadastro (Fila do QR Code)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pre_cadastro (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            cpf VARCHAR(11) UNIQUE NOT NULL,
            telefone VARCHAR(20),
            plano VARCHAR(30),
            senha_hash VARCHAR(255),
            status VARCHAR(20) DEFAULT 'Pendente',
            data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")