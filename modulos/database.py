import psycopg2
import streamlit as st

# Em produção, o Streamlit busca a senha de um arquivo secreto escondido
if "DATABASE_URL" in st.secrets:
    DATABASE_URL = st.secrets["DATABASE_URL"]
else:
    # Caso você rode localmente, ele usa o seu link direto
    DATABASE_URL = "postgresql://neondb_owner:npg_aVzTt25UbWdL@ep-odd-dust-act90b9z.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def obter_conexao():
    return psycopg2.connect(DATABASE_URL, connect_timeout=5)
def criar_tabela_alunos():
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        # Tabela oficial de alunos ativos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            cpf VARCHAR(11) UNIQUE NOT NULL,
            telefone VARCHAR(20),
            plano VARCHAR(30),
            pagamento_status VARCHAR(10) DEFAULT 'Não OK',
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Tabela de pré-cadastro (fila de aprovação)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pre_cadastro (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            cpf VARCHAR(11) UNIQUE NOT NULL,
            telefone VARCHAR(20),
            plano VARCHAR(30),
            status VARCHAR(20) DEFAULT 'Pendente',
            data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")