import streamlit as st
from psycopg2 import extras
import bcrypt
import pandas as pd
from modulos.database import obtener_conexao  # CORRIGIDO DE obter PARA obtener

def enviar_pre_cadastro(nome, email, cpf, telefone, plano, senha):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        
        # Criptografa a senha do aluno antes de mandar pra fila
        senha_bytes = senha.encode('utf-8')
        senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode('utf-8')
        
        query = "INSERT INTO pre_cadastro (nome, email, cpf, telefone, plano, senha_hash) VALUES (%s, %s, %s, %s, %s, %s);"
        cursor.execute(query, (nome, email, cpf, telefone, plano, senha_hash))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Solicitação enviada! Aguarde a aprovação na recepção para liberar seu login."
    except psycopg2.errors.UniqueViolation:
        return False, "Este E-mail ou CPF já possui uma solicitação pendente ou já está ativo."
    except Exception as e:
        return False, f"Erro ao enviar: {e}"

def buscar_dados_aluno_por_email(email):
    try:
        conn = obtener_conexao()
        query = "SELECT nome, cpf, telefone, plano, pagamento_status FROM alunos WHERE email = %s;"
        df = pd.read_sql(query, conn, params=(email,))
        conn.close()
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception:
        return None

def atualizar_dados_aluno(email, nome, telefone):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        query = "UPDATE alunos SET nome = %s, telefone = %s WHERE email = %s;"
        cursor.execute(query, (nome, telefone, email))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception:
        return False

def listar_avisos():
    try:
        conn = obtener_conexao()
        df = pd.read_sql("SELECT titulo, conteudo, to_char(data_postagem, 'DD/MM') as data FROM avisos ORDER BY data_postagem DESC;", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def exibir_formulario_aluno():
    # Se o aluno já estiver logado pelo fluxo centralizado do app_auth
    if st.session_state["logado"] and st.session_state["tipo_usuario"] == "aluno":
        st.title("👤 Meu Perfil de Treino")
        
        aba_perfil, aba_avisos = st.tabs(["👤 Meus Dados", "📢 Quadro de Avisos"])
        
        with aba_perfil:
            aluno = buscar_dados_aluno_por_email(st.session_state["nome_usuario"]) # Passa o e-mail logado
            if aluno:
                if aluno['pagamento_status'] == 'OK':
                    st.success(f"Acesso Liberado! Status de Pagamento: **PAGO ✅**")
                else:
                    st.error(f"Atenção: Status de Pagamento: **PENDENTE 🚨 (Não OK)**")
                
                with st.form("form_editar_perfil"):
                    novo_nome = st.text_input("Nome cadastrado", value=aluno['nome'])
                    novo_tel = st.text_input("WhatsApp", value=aluno['telefone'])
                    st.text_input("CPF", value=aluno['cpf'], disabled=True)
                    st.text_input("Plano Atual", value=aluno['plano'], disabled=True)
                    
                    botao_atualizar = st.form_submit_button("Salvar Alterações Pessoais", use_container_width=True)
                    
                if botao_atualizar:
                    if atualizar_dados_aluno(st.session_state["nome_usuario"], novo_nome, novo_tel):
                        st.success("Cadastro atualizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar os dados.")
            else:
                st.error("Erro ao recuperar perfil. Contacte a recepção.")
                
        with aba_avisos:
            df_avisos = listar_avisos()
            if df_avisos.empty:
                st.info("Nenhum aviso importante postado.")
            else:
                for idx, row in df_avisos.iterrows():
                    with st.container(border=True):
                        st.markdown(f"#### 📌 {row['titulo']} — `{row['data']}`")
                        st.write(row['conteudo'])
                        
    # Se o usuário não estiver logado (Visualização da aba pública de cadastro via QR Code)
    else:
        st.title("🏋️‍♂️ Ficha de Matrícula - Lourenço Filho BJJ")
        st.write("Insira seus dados para solicitar o acesso à academia. Crie a senha que usará para acessar o app depois de aprovado.")
        
        with st.form("form_aluno_externo", clear_on_submit=True):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail (Será seu Login)")
            senha = st.text_input("Crie uma Senha de Acesso", type="password")
            cpf = st.text_input("CPF (Apenas números)")
            telefone = st.text_input("WhatsApp (com DDD)")
            plano = st.selectbox("Escolha seu Plano", ["Mensal", "Trimestral", "Semestral", "Anual"])
            botao_enviar = st.form_submit_button("Enviar Solicitação de Matrícula", use_container_width=True)
            
        if botao_enviar:
            if not nome or not email or not cpf or not senha:
                st.warning("Todos os campos são obrigatórios!")
            elif len(cpf) != 11 or not cpf.isdigit():
                st.error("O CPF deve conter exatamente 11 números.")
            elif "@" not in email:
                st.error("Por favor, digite um e-mail válido.")
            else:
                with st.spinner("Processando..."):
                    sucesso, msg = enviar_pre_cadastro(nome, email.lower().strip(), cpf, telefone, plano, senha)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)