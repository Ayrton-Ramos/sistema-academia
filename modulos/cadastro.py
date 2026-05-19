import streamlit as st
import psycopg2
import pandas as pd
from modulos.database import obter_conexao

def listar_alunos_ativos():
    try:
        conn = obter_conexao()
        query = 'SELECT nome as "Nome", cpf as "CPF", telefone as "Telefone", plano as "Plano", pagamento_status as "Pagamento" FROM alunos ORDER BY nome ASC;'
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def processar_aprovacao(id_solicitacao, acao):
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        if acao == "aprovar":
            # 1. Busca os dados do pré-cadastro
            cursor.execute("SELECT nome, cpf, telefone, plano FROM pre_cadastro WHERE id = %s;", (id_solicitacao,))
            aluno = cursor.fetchone()
            
            if aluno:
                # 2. Insere na tabela oficial de alunos
                cursor.execute(
                    "INSERT INTO alunos (nome, cpf, telefone, plano, pagamento_status) VALUES (%s, %s, %s, %s, 'Não OK');",
                    (aluno[0], aluno[1], aluno[2], aluno[3])
                )
        
        # 3. Remove da fila de pré-cadastro em ambos os casos (aprovado ou recusado)
        cursor.execute("DELETE FROM pre_cadastro WHERE id = %s;", (id_solicitacao,))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return False

def exibir_tela_cadastro():
    st.subheader("📋 Gerenciamento de Alunos")
    
    aba_ativos, aba_pendentes = st.tabs(["🔍 Alunos Cadastrados", "⏳ Solicitações por QR Code"])
    
    with aba_ativos:
        df_ativos = listar_alunos_ativos()
        if df_ativos.empty:
            st.info("Nenhum aluno ativo encontrado.")
        else:
            st.dataframe(df_ativos, use_container_width=True, hide_index=True)
            
    with aba_pendentes:
        st.write("Novos alunos que escanearam o QR Code e aguardam liberação:")
        
        try:
            conn = obter_conexao()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, cpf, plano FROM pre_cadastro WHERE status = 'Pendente' ORDER BY data_solicitacao ASC;")
            solicitacoes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            solicitacoes = []
            
        if not solicitacoes:
            st.success("Não há nenhuma solicitação pendente no momento!")
        else:
            for s in solicitacoes:
                id_sol, nome_sol, cpf_sol, plano_sol = s
                
                # Cria um card visual para cada aluno pendente
                with st.container(border=True):
                    col_info, col_Sim, col_Nao = st.columns([3, 1, 1])
                    
                    with col_info:
                        st.markdown(f"**Nome:** {nome_sol} | **Plano:** {plano_sol}")
                        st.caption(f"CPF: {cpf_sol}")
                        
                    with col_Sim:
                        if st.button("✅ Aprovar", key=f"sim_{id_sol}"):
                            if processar_aprovacao(id_sol, "aprovar"):
                                st.success("Aluno aprovado!")
                                st.rerun()
                                
                    with col_Nao:
                        if st.button("❌ Recusar", key=f"nao_{id_sol}"):
                            if processar_aprovacao(id_sol, "recusar"):
                                st.warning("Solicitação descartada.")
                                st.rerun()