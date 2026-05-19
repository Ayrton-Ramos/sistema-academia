import sys
import os
# 🪛 GARANTIA LINUX: Força o Python a enxergar a raiz do projeto no Streamlit Cloud
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import psycopg2
from psycopg2 import extras
import bcrypt
import qrcode
import time
import threading
import base64
import smtplib  # ✉️ Biblioteca nativa para conexão direta SMTP
from email.mime.text import MIMEText  # Estruturador do corpo do e-mail
from datetime import datetime
from io import BytesIO

# IMPORTANDO AS TELAS E LOGICAS DOS MÓDULOS ISOLADOS
from modulos.cadastro import exibir_tela_cadastro
from modulos.aluno_publico import exibir_formulario_aluno
from modulos.database import obtener_conexao

# IMPORTANDO OS DESIGNERS INJETÁVEIS DA PASTA STYLE
try:
    from style.auth_style import aplicar_estilo_auth
    from style.cadastro_style import aplicar_estilo_cadastro
    from style.aluno_style import aplicar_estilo_aluno
except Exception:
    def aplicar_estilo_auth(): pass
    def aplicar_estilo_cadastro(): pass
    def aplicar_estilo_aluno(): pass

# ==============================================================================
# 1. GARANTIA DE ESTRUTURA DO BANCO DE DADOS (AUTO-MIGRATION)
# ==============================================================================
def inicializar_e_corrigir_banco():
    """Garante que a tabela existe e injeta as colunas necessárias se faltarem"""
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                telefone VARCHAR(50),
                cpf VARCHAR(20),
                senha_hash VARCHAR(255),
                pagamento_status VARCHAR(50) DEFAULT 'Não OK',
                dat_vencimento DATE DEFAULT CURRENT_DATE
            );
        """)
        
        try:
            cursor.execute("ALTER TABLE alunos ADD COLUMN modalidade VARCHAR(255) DEFAULT 'Jiu-Jitsu';")
            conn.commit()
        except psycopg2.errors.DuplicateColumn:
            conn.rollback()
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERRO BANCO]: Falha ao rodar migração: {e}")

inicializar_e_corrigir_banco()

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E CONTROLE DE ESTADOS DA SESSÃO
# ==============================================================================
st.set_page_config(page_title="Loyalty Team Martial Arts", page_icon="💪", layout="centered")

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""
if "email_usuario" not in st.session_state:
    st.session_state["email_usuario"] = ""
if "tipo_usuario" not in st.session_state:
    st.session_state["tipo_usuario"] = "" 
if "pagamento_status" not in st.session_state:
    st.session_state["pagamento_status"] = "OK"
if "tela_atual" not in st.session_state:
    st.session_state["tela_atual"] = "login"

# ==============================================================================
# 🔥 FUNÇÃO CORRIGIDA: APLICAR BACKGROUND ESCURO E MENOR COM INFIGHT.PNG
# ==============================================================================
def aplicar_fundo_infight():
    """Aplica a imagem infight.png de forma reduzida e escurecida no fundo"""
    caminhos_possiveis = ["img/infight.png", "infight.png"]
    caminho_final = None
    
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            caminho_final = caminho
            break
            
    if caminho_final:
        with open(caminho_final, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                /* 🎯 ESCURECIMENTO: Cria uma camada preta opaca por cima da imagem */
                background-color: rgba(6, 6, 6, 0.91) !important;
                background-image: url("data:image/png;base64,{encoded_string}");
                
                /* 🎯 ESCURECIMENTO ATIVO: Ativa a mistura da cor com a imagem */
                background-blend-mode: overlay;
                
                /* 🎯 TAMANHO REDUZIDO: Altere de 45% para mais ou menos para controlar o tamanho */
                background-size: 160% !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
                
            }}
            
            /* Ajuste fino nos boxes do formulário para garantir 100% de contraste */
            div[data-testid="stForm"] {{
                background-color: rgba(15, 15, 15, 0.95) !important;
                border: 1px solid #D4AF37 !important;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.5);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# ==============================================================================
# 2. MOTOR DE COBRANÇA AUTOMÁTICA EM SEGUNDO PLANO
# ==============================================================================
EMAIL_REMETENTE = "ayrtonramos96@gmail.com"  
SENHA_APP = "iajw gfdt fyyq rcok"            

def enviar_email_automatico_pix(nome, email, copia_cola_pix):
    try:
        mensagem_corpo = (
            f"Olá, {nome}! 🥋\n\n"
            f"Sua mensalidade de teste da Loyalty Team Martial Arts está aberta. 🥊\n"
            f"Conforme combinado para homologação do sistema, o valor atual é de R$ 2,00.\n\n"
            f"Utilize o Pix Copia e Cola abaixo para efectuar o pagamento:\n\n"
            f"{copia_cola_pix}\n\n"
            f"Após o pagamento, o sistema liberará seu access automaticamente no site.\n\n"
            f"Qualquer dúvida, estamos à disposição! Oss. 🔥"
        )
        msg = MIMEText(mensagem_corpo, 'plain', 'utf-8')
        msg['Subject'] = "Aviso de Mensalidade (Teste Pix R$ 2,00) - Loyalty Team"
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

def rotina_cobranca_mensal(dia_alvo, hora_alvo, minuto_alvo):
    while True:
        agora = datetime.now()
        if agora.day == dia_alvo and agora.hour == hora_alvo and agora.minute == minuto_alvo:
            try:
                conn = obtener_conexao()
                cursor = conn.cursor()
                cursor.execute("SELECT nome, email FROM alunos WHERE pagamento_status = 'Não OK';")
                lista_devedores = cursor.fetchall()
                
                for nome, email in lista_devedores:
                    from modulos.pagamento import gerar_pix_mensalidade
                    id_pag, copia_cola, qr_base64 = gerar_pix_mensalidade(nome, email, valor=2.00)
                    if copia_cola:
                        enviar_email_automatico_pix(nome, email, copia_cola)
                    time.sleep(3)
                cursor.close()
                conn.close()
            except Exception:
                pass
            time.sleep(65)
        time.sleep(30)

if not any(t.name == "ThreadCobrancaBJJ" for t in threading.enumerate()):
    motor_cobranca = threading.Thread(target=rotina_cobranca_mensal, args=(19, 10, 27), name="ThreadCobrancaBJJ", daemon=True)
    motor_cobranca.start()

# ==============================================================================
# 3. FUNÇÕES DE INFRAESTRUTURA E BANCO DE DADOS
# ==============================================================================
def buscar_dados_aluno(email):
    conn = None
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT nome, email, modalidade, pagamento_status, dat_vencimento FROM alunos WHERE email = %s;", (email,))
            aluno = cursor.fetchone()
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            cursor.execute("SELECT nome, email, modalidade, pagamento_status, data_vencimento FROM alunos WHERE email = %s;", (email,))
            aluno = cursor.fetchone()
            
        cursor.close()
        conn.close()
        return aluno
    except Exception as e:
        if conn: conn.close()
        st.error(f"⚠️ Nota do Sistema: Sincronizando dados do perfil... ({e})")
        return ("Guerreiro Loyalty", email, "Jiu-Jitsu", "Não OK", datetime.now().date())

def verificar_login_adm(email, senha):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, senha_hash FROM usuarios_adm WHERE email = %s;", (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        if resultado:
            nome, hash_banco = resultado
            if bcrypt.checkpw(senha.encode('utf-8'), hash_banco.encode('utf-8')):
                return True, nome
        return False, "E-mail ou senha incorretos adm."
    except Exception:
        return False, "Erro de conexão externa."

def verificar_login_aluno(email, senha):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, senha_hash, pagamento_status FROM alunos WHERE email = %s;", (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        if resultado:
            nome_aluno, hash_banco, status_pagto = resultado
            if hash_banco and bcrypt.checkpw(senha.encode('utf-8'), hash_banco.encode('utf-8')):
                return True, {"nome": nome_aluno, "status_pagto": status_pagto}
        return False, "E-mail ou senha de aluno incorretos."
    except Exception:
        return False, "Erro de conexão externa."

def cadastrar_usuario_adm(nome, email, senha):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO usuarios_adm (nome, email, senha_hash) VALUES (%s, %s, %s);", (nome, email, senha_hash))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Administrador cadastrado com sucesso!"
    except Exception:
        return False, "E-mail já registrado no sistema."

# ==============================================================================
# INTERFACE LOCAL DE INSCRIÇÃO PÚBLICA
# ==============================================================================
def exibir_formulario_aluno_customizado():
    st.title("📝 Ficha de Matrícula - Loyalty Team Martial Arts")
    st.write("Preencha seus dados cadastrais e escolha as modalidades que deseja treinar:")
    
    with st.form("form_nova_matricula"):
        nome_m = st.text_input("Nome Completo")
        email_m = st.text_input("E-mail (Será seu login)")
        tel_m = st.text_input("Telefone com DDD")
        cpf_m = st.text_input("CPF (Apenas números - Obrigatório)")
        senha_m = st.text_input("Crie uma Senha de Acesso", type="password")
        
        modalidades_selecionadas = st.multiselect(
            "Selecione as Modalidades Contratadas (Escolha uma ou mais):",
            options=["🥋 Jiu-Jitsu", "🥊 Muay Thai", "🏋️ Funcional"],
            default=["🥋 Jiu-Jitsu"]
        )
        
        botao_matricular = st.form_submit_button("ENVIAR SOLICITAÇÃO DE MATRÍCULA", use_container_width=True)
        
    if botao_matricular:
        if not nome_m or not email_m or not senha_m or not cpf_m or not modalidades_selecionadas:
            st.warning("⚠️ Preencha todos os campos, incluindo o CPF, e marque pelo menos uma modalidade!")
        else:
            try:
                conn = obtener_conexao()
                cursor = conn.cursor()
                
                cpf_limpo = "".join(filter(str.isdigit, cpf_m))
                string_modalidades = ", ".join(modalidades_selecionadas)
                senha_hash = bcrypt.hashpw(senha_m.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute(
                    """INSERT INTO alunos (nome, email, telefone, cpf, senha_hash, modalidade, pagamento_status) 
                       VALUES (%s, %s, %s, %s, %s, %s, 'Não OK');""",
                    (nome_m, email_m.lower().strip(), tel_m, cpf_limpo, senha_hash, string_modalidades)
                )
                conn.commit()
                cursor.close()
                conn.close()
                st.success("🎉 Pré-matrícula realizada! Utilize o botão abaixo para ir para a tela de login.")
            except Exception as e:
                st.error(f"Erro ao salvar matrícula (E-mail ou CPF já cadastrados): {e}")

# ==============================================================================
# 4. RENDERIZAÇÃO DA ÁREA EXCLUSIVA DO ALUNO
# ==============================================================================
def exibir_painel_aluno(email_usuario):
    dados_aluno = buscar_dados_aluno(email_usuario)
    if not dados_aluno:
        st.error("⚠️ Não foi possível carregar os dados do seu perfil. Contate a recepção.")
        return

    nome_aluno, email_aluno, modalidade, status_pagamento, data_vencimento = dados_aluno

    if status_pagamento != "OK":
        from modulos.pagamento import exibir_tela_checkout_pix
        exibir_tela_checkout_pix(nome_aluno, email_aluno, valor=2.00)
        return

    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>🥋 Área do Aluno - Loyalty Team</h1>", unsafe_allow_html=True)
    st.write(f"Olá, **{nome_aluno}**! Seja bem-vindo de volta aos treinos.")
    st.write("---")

    st.markdown("### 📋 Meus Dados Cadastrais")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**👤 Nome:** {nome_aluno}")
        st.markdown(f"**📧 E-mail:** {email_aluno}")
    with col2:
        data_formatada = data_vencimento.strftime('%d/%m/%Y') if hasattr(data_vencimento, 'strftime') else str(data_vencimento)
        st.markdown(f"**📅 Próximo Vencimento:** {data_formatada}")

    st.write("---")

    st.markdown("### 🥋 Suas Modalidades Contratadas")
    modalidade_limpa = str(modalidade).lower()
    
    col_muay, col_bjj, col_func = st.columns(3)
    with col_muay:
        st.checkbox("🥊 Muay Thai", value=("muay" in modalidade_limpa), disabled=True)
    with col_bjj:
        st.checkbox("🥋 Jiu-Jitsu", value=("jiu" in modalidade_limpa or "jiujitsu" in modalidade_limpa), disabled=True)
    with col_func:
        st.checkbox("🏋️ Funcional", value=("func" in modalidade_limpa or "funcional" in modalidade_limpa), disabled=True)

    st.write("---")

    st.markdown("### 💳 Situação do Plano Comercial")
    st.markdown(
        """
        <div style='background-color: #2ec4b6; padding: 18px; border-radius: 8px; text-align: center;'>
            <h3 style='color: #ffffff; margin: 0; font-weight: bold; font-family: sans-serif;'>🟢 STATUS: REGULARIZADO / PAGO</h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.write("")

# ==============================================================================
# CARD VISUAL DO FALE CONOSCO (RODAPÉ)
# ==============================================================================
def renderizar_fale_conosco_centro():
    st.write("")
    st.markdown(
        """
        <div style='background-color: rgba(17, 17, 17, 0.95); padding: 15px; border-radius: 8px; border: 1px solid #D4AF37; margin-top: 20px;'>
            <h4 style='color: #D4AF37; margin: 0 0 10px 0; font-family: sans-serif; text-align: center;'>📞 FALE CONOSCO — LOYALTY TEAM</h4>
            <div style='display: flex; justify-content: space-around; flex-wrap: wrap;'>
                <div style='min-width: 200px; margin-bottom: 5px;'>
                    <p style='margin: 0; font-weight: bold; color: #D4AF37; font-size: 13px;'>📍 Endereço:</p>
                    <p style='margin: 0; color: #ffffff; font-size: 13px;'>R. Rio Branco, 522 - Centro<br>Mauá - SP, 09310-110</p>
                </div>
                <div style='min-width: 200px;'>
                    <p style='margin: 0; font-weight: bold; color: #D4AF37; font-size: 13px;'>📱 Contato Direto:</p>
                    <p style='margin: 0; color: #ffffff; font-size: 13px;'>(11) 96272-9922</p>
                    <p style='margin: 0; color: #aaaaaa; font-style: italic; font-size: 11px;'>Falar com Lourenço Filho</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================================================================
# 5. FLUXO DE TELAS DO APLICATIVO (ROTEAMENTO DINÂMICO PRINCIPAL)
# ==============================================================================
if st.session_state["logado"]:
    aplicar_estilo_auth()
    
    try:
        st.sidebar.image("img/logo_bjj.png", use_container_width=True)
    except Exception:
        st.sidebar.write("### 🥋 LOYALTY TEAM")
        
    st.sidebar.markdown(f"Guerreiro: **{st.session_state['nome_usuario']}**")
    st.sidebar.caption(f"Perfil: {st.session_state['tipo_usuario'].upper()}")
    st.sidebar.write("---")
    
    if st.session_state["tipo_usuario"] == "adm":
        st.sidebar.markdown("### 🥷 MENU PRINCIPAL")
        tela_selecionada = st.sidebar.radio("Ir para:", ["📋 Gestão de Alunos", "💪 Gestão de Treinos", "💰 Controle Financeiro"])
    elif st.session_state["tipo_usuario"] == "aluno":
        tela_selecionada = "👤 Área do Aluno"

    if st.sidebar.button("🚪 Sair da Conta", use_container_width=True):
        st.session_state["logado"] = False
        st.session_state["nome_usuario"] = ""
        st.session_state["email_usuario"] = ""
        st.session_state["tipo_usuario"] = ""
        st.session_state["pagamento_status"] = "OK"
        st.rerun()

    if st.session_state["tipo_usuario"] == "adm":
        if tela_selecionada == "📋 Gestão de Alunos":
            st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
            aplicar_estilo_cadastro()
            exibir_tela_cadastro()
        elif tela_selecionada == "💪 Gestão de Treinos":
            st.title("💪 Fichas de Exercícios")
            st.info("Módulo em desenvolvimento.")
        elif tela_selecionada == "💰 Controle Financeiro":
            st.title("💰 Caixa e Mensalidades")
            st.info("Módulo em desenvolvimento.")
            
    elif st.session_state["tipo_usuario"] == "aluno":
        st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
        aplicar_estilo_aluno()
        exibir_painel_aluno(st.session_state["email_usuario"])

else:
    # 🎨 CHAMADA DO MOTOR ATUALIZADO DE BACKGROUND CALIBRADO ESCURO
    aplicar_fundo_infight()
    st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
    
    st.write("")
    st.write("")
        
    if st.session_state["tela_atual"] == "login":
        tipo_login = st.segmented_control("Entrar como:", options=["🥷 Administrador", "👤 Aluno"], default="🥷 Administrador")
        
        with st.form("form_login"):
            email_login = st.text_input("E-mail Cadastrado")
            senha_login = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True)
            
        if botao_login:
            if not email_login or not senha_login:
                st.warning("Preencha todos os campos!")
            else:
                with st.spinner("Autenticando..."):
                    email_limpo = email_login.lower().strip()
                    if tipo_login == "🥷 Administrador":
                        sucesso, info = verificar_login_adm(email_limpo, senha_login)
                        tipo_perfil = "adm"
                        status_p = "OK"
                        email_usuario_salvo = email_limpo
                    else:
                        sucesso, info = verificar_login_aluno(email_limpo, senha_login)
                        tipo_perfil = "aluno"
                        if Caravans := sucesso:
                            email_usuario_salvo = email_limpo
                            status_p = info["status_pagto"]
                            info = info["nome"]
                        
                if sucesso:
                    st.session_state["logado"] = True
                    st.session_state["nome_usuario"] = info
                    st.session_state["email_usuario"] = email_usuario_salvo
                    st.session_state["tipo_usuario"] = tipo_perfil
                    st.session_state["pagamento_status"] = status_p
                    st.rerun()
                else:
                    st.error(info)

        c_v1, c_v2 = st.columns(2)
        with c_v1:
            if st.button("📝 Fazer Nova Matrícula", use_container_width=True):
                st.session_state["tela_atual"] = "matricula"
                st.rerun()
        with c_v2:
            if st.button("🔑 Criar Conta ADM", use_container_width=True):
                st.session_state["tela_atual"] = "criar_adm"
                st.rerun()

    elif st.session_state["tela_atual"] == "matricula":
        aplicar_estilo_aluno()
        exibir_formulario_aluno_customizado()
        st.write("")
        if st.button("⬅️ Voltar para a Tela de Login", use_container_width=True):
            st.session_state["tela_atual"] = "login"
            st.rerun()

    elif st.session_state["tela_atual"] == "criar_adm":
        st.title("🔐 Novo Administrador")
        with st.form("form_registro"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            botao_registrar = st.form_submit_button("Cadastrar", use_container_width=True)
        if botao_registrar:
            sucesso, msg = cadastrar_usuario_adm(nome, email, senha)
            if sucesso: st.success(msg)
            else: st.error(msg)
            
        st.write("")
        if st.button("⬅️ Voltar para a Tela de Login", use_container_width=True):
            st.session_state["tela_atual"] = "login"
            st.rerun()

    renderizar_fale_conosco_centro()
    st.markdown('<div class="color-strip-bottom"></div>', unsafe_allow_html=True)