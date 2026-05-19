import streamlit as st
import pandas as pd
import time
import re
import smtplib
from email.mime.text import MIMEText
from modulos.database import obtener_conexao

# ==============================================================================
# CONFIGURAÇÃO DE DISPARO DE E-MAIL (SMTP GMAIL)
# ==============================================================================
EMAIL_REMETENTE = "ayrtonramos96@gmail.com"
SENHA_APP = "iajw gfdt fyyq rcok"

def disparar_email_invisivel(nome_destino, email_destino, mensagem_corpo):
    """Envia o e-mail em segundo plano conectado ao servidor SMTP do Gmail"""
    try:
        msg = MIMEText(mensagem_corpo, 'plain', 'utf-8')
        msg['Subject'] = "Aviso de Mensalidade - Lourenço Filho BJJ"
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = email_destino

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, email_destino, msg.as_string())
        server.quit()
        return True, "Enviado"
    except Exception as e:
        return False, str(e)

def aprovar_aluno_manualmente_banco(id_aluno):
    """Muda o status do aluno diretamente no PostgreSQL de Não OK para OK"""
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        cursor.execute("UPDATE alunos SET pagamento_status = 'OK' WHERE id = %s;", (id_aluno,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao aprovar no banco: {e}")
        return False

# ==============================================================================
# INTERFACE PRINCIPAL DE GESTÃO DE ALUNOS (PAINEL ADMINISTRATIVO)
# ==============================================================================
def exibir_tela_cadastro():
    st.title("📋 Central de Gestão de Alunos")
    st.write("Monitore matrículas efetivas e aprove novos cadastros pendentes de validação.")

    # 1. Puxa TODOS os dados do PostgreSQL para fazer a divisão
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, email, telefone, modalidade, pagamento_status FROM alunos ORDER BY id DESC;")
        dados_banco = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao conectar com a base de dados: {e}")
        return

    if not dados_banco:
        st.info("Nenhum aluno matriculado no sistema até o momento.")
        return

    # Converte os dados brutos para um DataFrame geral do Pandas
    df_geral = pd.DataFrame(dados_banco, columns=["ID", "Nome", "Email", "Telefone", "Modalidade", "Status Financeiro"])

    # 2. SEPARAÇÃO DOS DADOS POR STATUS
    # Matrículas Efetivas = Apenas quem está 'OK'
    df_efetivos = df_geral[df_geral["Status Financeiro"] == "OK"].copy()
    # Cadastros Pendentes = Quem está 'Não OK' e aguarda aprovação
    df_pendentes = df_geral[df_geral["Status Financeiro"] != "OK"].copy()

    # 3. BLOCO DE MÉTRICAS DO TOPO
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(label="Total Geral de Contas", value=len(df_geral))
    with col_m2:
        st.metric(label="Matrículas Efetivas (OK)", value=len(df_efetivos))
    with col_m3:
        # Mostra o delta em vermelho indicando quantos precisam de atenção
        st.metric(label="Novos Cadastros Retidos", value=len(df_pendentes), delta=f"{len(df_pendentes)} aguardando", delta_color="inverse")

    st.write("---")

    # ==============================================================================
    # SECTION 1: LISTAGEM DE MATRÍCULAS EFETIVAS (APENAS REGULARIZADOS)
    # ==============================================================================
    st.markdown("### 🥋 Listagem de Matrículas Efetivas")
    st.caption("Esta tabela exibe apenas os alunos ativos e regularizados na academia.")

    busca_nome = st.text_input("🔍 Buscar aluno ativo pelo nome:")
    if busca_nome:
        df_efetivos = df_efetivos[df_efetivos["Nome"].str.contains(busca_nome, case=False, na=False)]

    if df_efetivos.empty:
        st.info("Nenhum aluno com matrícula efetiva regularizada no momento.")
    else:
        # Exibe a tabela limpa sem caixas de seleção, já que estes já estão aprovados
        st.dataframe(
            df_efetivos,
            column_config={
                "ID": st.column_config.NumberColumn(),
                "Nome": st.column_config.TextColumn(),
                "Email": st.column_config.TextColumn(),
                "Telefone": st.column_config.TextColumn(),
                "Modalidade": st.column_config.TextColumn(),
                "Status Financeiro": st.column_config.TextColumn()
            },
            hide_index=True,
            use_container_width=True
        )

    st.write("---")

    # ==============================================================================
    # SECTION 2: PAINEL DE ADMISSÃO E AVISO DE NOVOS CADASTROS (FINAL DA TELA)
    # ==============================================================================
    st.markdown("### ⚠️ Fila de Admissão de Novos Alunos")
    
    if df_pendentes.empty:
        st.success("🎉 Excelente! Não existem novos cadastros pendentes de aprovação no momento.")
    else:
        # Alerta visual forte chamando a atenção do Administrador
        st.error(f"📣 **AVISO:** Identificamos **{len(df_pendentes)}** novo(s) cadastro(s) retido(s) aguardando a sua aprovação manual para entrar na listagem efetiva!")
        
        # Injeta a coluna de checkbox apenas para a tabela de pendentes
        df_pendentes.insert(0, "Selecionar", False)
        
        # Renderiza a tabela de triagem
        tabela_triagem = st.data_editor(
            df_pendentes,
            column_config={
                "Selecionar": st.column_config.CheckboxColumn(help="Marque para aprovar ou notificar este aluno", default=False),
                "ID": st.column_config.NumberColumn(disabled=True),
                "Nome": st.column_config.TextColumn(disabled=True),
                "Email": st.column_config.TextColumn(disabled=True),
                "Telefone": st.column_config.TextColumn(disabled=True),
                "Modalidade": st.column_config.TextColumn(disabled=True),
                "Status Financeiro": st.column_config.TextColumn(disabled=True)
            },
            disabled=["ID", "Nome", "Email", "Telefone", "Modalidade", "Status Financeiro"],
            hide_index=True,
            use_container_width=True
        )

        # Filtra quais alunos retidos foram marcados
        alunos_selecionados = tabela_triagem[tabela_triagem["Selecionar"] == True].to_dict(orient="records")
        total_fila = len(alunos_selecionados)

        st.write("")
        
        if total_fila == 0:
            st.info("💡 Ative o checkbox 'Selecionar' na linha do aluno retido acima para liberar as ações de admissão.")
        else:
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                st.markdown("**🟢 Validar Entrada:**")
                if st.button("🥋 APROVAR CADASTRO E COBRANÇA (Mudar para OK)", use_container_width=True):
                    sucessos_ap = 0
                    for aluno in alunos_selecionados:
                        if aprovar_aluno_manualmente_banco(aluno["ID"]):
                            sucessos_ap += 1
                    st.success(f"🎉 Sucesso! {sucessos_ap} aluno(s) movidos para a listagem de matrículas efetivas!")
                    time.sleep(1.5)
                    st.rerun()

            with col_btn2:
                st.markdown("**✉️ Enviar Links de Cobrança:**")
                tipo_acao = st.selectbox("Escolha o canal de envio:", ["Não selecionar", "💬 Enviar WhatsApp", "✉️ Enviar E-mail com Pix R$ 2,00"])

                if tipo_acao == "💬 Enviar WhatsApp":
                    for aluno in alunos_selecionados:
                        nome_w = aluno["Nome"]
                        tel_w = re.sub(r'\D', '', str(aluno["Telefone"]))
                        texto_w = f"Olá, {nome_w}! Seu cadastro na Lourenço Filho BJJ foi recebido. Acesse o site para realizar o pagamento do Pix de teste de R$ 2,00 e liberar seu perfil. Oss!"
                        texto_url = re.sub(r' ', '%20', texto_w)
                        st.link_button(f"Abrir WhatsApp para: {nome_w}", f"https://api.whatsapp.com/send?phone=55{tel_w}&text={texto_url}", use_container_width=True)

                elif tipo_acao == "✉️ Enviar E-mail com Pix R$ 2,00":
                    if st.button("✉️ DISPARAR AGORA POR E-MAIL", use_container_width=True):
                        from modulos.pagamento import gerar_pix_mensalidade
                        sucessos_em = 0
                        
                        for aluno in alunos_selecionados:
                            nome_e = aluno["Nome"]
                            email_e = aluno["Email"]
                            
                            id_pag, copia_cola, qr_base64 = gerar_pix_mensalidade(nome_e, email_e, valor=2.00)
                            
                            if copia_cola:
                                corpo = (
                                    f"Olá, {nome_e}! 🥋\n\n"
                                    f"Seu cadastro na academia Lourenço Filho BJJ está ativo. Geramos sua fatura de teste de R$ 2,00 para homologação.\n\n"
                                    f"Copia e Cola Pix:\n{copia_cola}\n\n"
                                    f"Após o pagamento o painel libera sozinho. Oss! 🔥"
                                )
                                ok, msg = disparar_email_invisivel(nome_e, email_e, corpo)
                                if ok: sucessos_em += 1
                                
                        st.success(f"🚀 {sucessos_em} e-mails enviados com as chaves Pix dinâmicas!")
                        time.sleep(1.5)
                        st.rerun()