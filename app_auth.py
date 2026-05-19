import streamlit as st
import bcrypt
import qrcode
from io import BytesIO

# IMPORTANDO A TELA DO MÓDULO ISOLADO
from modulos.cadastro import exibir_tela_cadastro
from modulos.aluno_publico import exibir_formulario_aluno

# IMPORTANDO AS FUNÇÕES DO BANCO DE DADOS DA PASTA MODULOS
from modulos.database import obter_conexao, criar_tabela_alunos

# Garante que as tabelas existam assim que o sistema inicializar
criar_tabela_alunos()

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit do script)
# ==============================================================================
st.set_page_config(page_title="Sistema Academia", page_icon="💪", layout="centered")

# ==============================================================================
# 2. INICIALIZAÇÃO DOS ESTADOS DE SESSÃO
# ==============================================================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""

# ==============================================================================
# 3. FUNÇÕES DE AUTENTICAÇÃO DO ADMINISTRADOR
# ==============================================================================
def cadastrar_usuario(nome, email, senha):
    """Criptografa a senha e salva o novo administrador no banco"""
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        senha_bytes = senha.encode('utf-8')
        senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode('utf-8')
        
        query = "INSERT INTO usuarios_adm (nome, email, senha_hash) VALUES (%s, %s, %s);"
        cursor.execute(query, (nome, email, senha_hash))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Usuário cadastrado com sucesso!"
    except Exception as e:
        if "unique constraint" in str(e).lower():
            return False, "Este e-mail já está cadastrado."
        return False, f"Erro na conexão com o banco: {e}"

def verificar_login(email, senha):
    """Busca o administrador no banco e valida a senha criptografada"""
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        query = "SELECT nome, senha_hash FROM usuarios_adm WHERE email = %s;"
        cursor.execute(query, (email,))
        resultado = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if resultado:
            nome_usuario, hash_banco = resultado
            if bcrypt.checkpw(senha.encode('utf-8'), hash_banco.encode('utf-8')):
                return True, nome_usuario
                
        return False, "E-mail ou senha incorretos."
    except Exception as e:
        return False, f"Erro na conexão: {e}"


# ==============================================================================
# 4. FLUXO DE TELAS DO APLICATIVO
# ==============================================================================

# --- CASO O USUÁRIO ESTEJA LOGADO -> EXIBE O MENU PRINCIPAL COM AS ABAS ---
if st.session_state["logado"]:
    
    # Barra superior com o nome do ADM conectado e o botão de logout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🏋️‍♂️ Painel Geral - Lourenço")
        st.caption(f"Administrador conectado: **{st.session_state['nome_usuario']}**")
    with col2:
        st.write("") 
        if st.button("🚪 Sair"):
            st.session_state["logado"] = False
            st.session_state["nome_usuario"] = ""
            st.rerun()

    # --- BARRA LATERAL DO ADM COM O QR CODE ---
    st.sidebar.markdown("### 📱 QR Code da Recepção")
    st.sidebar.write("Deixe este QR Code visível para os alunos escanearem no balcão.")
    
    # IMPORTANTE: Altera para o teu Network URL atual que aparece no terminal (ex: http://192.168.0.15:8501)
    LINK_REDE = "http://localhost:8501" 
    
    # Gera a imagem do QR Code em memória
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(LINK_REDE)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Converte a imagem para um formato que o Streamlit consegue desenhar
    buf = BytesIO()
    img_qr.save(buf, format="PNG")
    byte_im = buf.getvalue()
    
    # Desenha o QR Code na barra lateral
    st.sidebar.image(byte_im, caption="Escaneia para te matriculares")

    st.write("---")

    # CRIAÇÃO DAS ABAS DO MENU PRINCIPAL
    aba_alunos, aba_treinos, aba_financeiro = st.tabs([
        "📋 Gestão de Alunos", 
        "💪 Gestão de Treinos", 
        "💰 Controle Financeiro"
    ])

    # ABA 1: Executa a tela que está isolada em modulos/cadastro.py
    with aba_alunos:
        exibir_tela_cadastro()

    # ABA 2: Espaço reservado para os treinos
    with aba_treinos:
        st.subheader("💪 Fichas de Exercícios")
        st.info("Espaço reservado para montar o treino A, B, C dos alunos.")

    # ABA 3: Espaço reservado para o financeiro
    with aba_financeiro:
        st.subheader("💰 Caixa e Mensalidades")
        st.info("Espaço reservado para fluxo de caixa e controle de adimplência.")


# --- CASO NÃO ESTEJA LOGADO -> EXIBE TELA DE ACESSO / CADASTRO DE ADM ---
else:
    st.sidebar.title("Navegação")
    opcao = st.sidebar.selectbox("Escolha uma opção", ["Login", "Área do Aluno (QR Code)", "Criar Conta ADM"])

    if opcao == "Área do Aluno (QR Code)":
        exibir_formulario_aluno()

    elif opcao == "Login":
        st.title("🔐 Sistema de Gestão - Academia")
        st.subheader("Área Restrita do Administrador")
        
        with st.form("form_login"):
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar")
            
        if botao_login:
            if not email_login or not senha_login:
                st.warning("Preencha e-mail e senha!")
            else:
                with st.spinner("Autenticando..."):
                    sucesso, info = verificar_login(email_login, senha_login)
                if sucesso:
                    st.session_state["logado"] = True
                    st.session_state["nome_usuario"] = info
                    st.rerun()
                else:
                    st.error(info)

    elif opcao == "Criar Conta ADM":
        st.title("🔐 Sistema de Gestão - Academia")
        st.subheader("Criar Nova Conta de Administrador")
        
        with st.form("form_registro"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            botao_registrar = st.form_submit_button("Cadastrar")
            
        if botao_registrar:
            if not nome or not email or not senha:
                st.warning("Preencha todos os campos!")
            else:
                with st.spinner("Conectando ao banco Neon..."):
                    sucesso, msg = cadastrar_usuario(nome, email, senha)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)