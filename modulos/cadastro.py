import streamlit as st
from psycopg2 import extras
import pandas as pd
import time
import urllib.parse
import smtplib  # Biblioteca nativa para conexão direta SMTP
from email.mime.text import MIMEText  # Estruturador do corpo do e-mail
from modulos.database import obtener_conexao

# ==============================================================================
# 🔑 CONFIGURAÇÃO DO SEU SERVIDOR DE E-MAIL (GMAIL DA ACADEMIA)
# ==============================================================================
EMAIL_REMETENTE = "ayrtonramos96@gmail.com"  # Seu e-mail de disparo
SENHA_APP = "iajw gfdt fyyq rcok"            # Sua senha de app de 16 dígitos

def disparar_email_invisivel(nome_aluno, email_destino, mensagem_corpo):
    """Conecta diretamente com o servidor do Gmail e envia o e-mail em background"""
    try:
        msg = MIMEText(mensagem_corpo, 'plain', 'utf-8')
        msg['Subject'] = "Pendência Financeira - Lourenço Filho BJJ"
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

def listar_alunos_ativos():
    """Busca a lista de alunos ativos direto no banco de dados"""
    try:
        conn = obtener_conexao()
        query = 'SELECT nome as "Nome", email as "E-mail", cpf as "CPF", telefone as "Telefone", plano as "Plano", pagamento_status as "Pagamento" FROM alunos ORDER BY nome ASC;'
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def processar_aprovacao(id_solicitacao, acao):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        if acao == "aprovar":
            cursor.execute("SELECT nome, email, cpf, telefone, plano, senha_hash FROM pre_cadastro WHERE id = %s;", (id_solicitacao,))
            aluno = cursor.fetchone()
            if aluno:
                cursor.execute(
                    "INSERT INTO alunos (nome, email, cpf, telefone, plano, senha_hash, pagamento_status) VALUES (%s, %s, %s, %s, %s, %s, 'Não OK');",
                    (aluno[0], aluno[1], aluno[2], aluno[3], aluno[4], aluno[5])
                )
        cursor.execute("DELETE FROM pre_cadastro WHERE id = %s;", (id_solicitacao,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao processar aprovação: {e}")
        return False

def exibir_tela_cadastro():
    st.title("📋 Gerenciamento de Alunos")
    
    sub_opcao = st.segmented_control(
        "Filtrar por:",
        options=["🔍 Ver Alunos Ativos", "⏳ Fila de Espera (QR Code)"],
        default="🔍 Ver Alunos Ativos"
    )
    
    st.write("---")
    
    if sub_opcao == "🔍 Ver Alunos Ativos":
        df_ativos = listar_alunos_ativos()
        if df_ativos.empty:
            st.info("Nenhum aluno ativo cadastrado.")
        else:
            # Escolha do canal de envio antes da tabela
            canal_envio = st.radio(
                "Escolha o canal para envio da cobrança:",
                options=["💬 Enviar pelo WhatsApp", "✉️ Enviar por E-mail (Em Lote / Tudo de uma vez)"],
                horizontal=True
            )

            df_ativos["Cobrar Manual"] = False

            config_colunas = {
                "Nome": st.column_config.TextColumn("Nome"),
                "E-mail": st.column_config.TextColumn("E-mail"),
                "CPF": st.column_config.TextColumn("CPF"),
                "Telefone": st.column_config.TextColumn("Telefone"),
                "Plano": st.column_config.TextColumn("Plano"),
                "Pagamento": st.column_config.TextColumn("Pagamento"),
                "Cobrar Manual": st.column_config.CheckboxColumn(
                    "Selecionar 🎯",
                    help="Marque todos os alunos inadimplentes que deseja cobrar",
                    default=False
                )
            }

            # Renderiza a tabela de gerenciamento
            tabela_interativa = st.data_editor(
                df_ativos,
                column_config=config_colunas,
                disabled=df_ativos.columns.drop("Cobrar Manual"), 
                use_container_width=True,
                hide_index=True,
                key="editor_gerenciamento_alunos"
            )

            # 📋 CAPTURA TODOS OS SELECIONADOS
            alunos_para_cobrar = []
            for i in range(len(tabela_interativa)):
                if tabela_interativa.iloc[i]["Cobrar Manual"] == True:
                    aluno = tabela_interativa.iloc[i]
                    if aluno["Pagamento"] == "Não OK":
                        alunos_para_cobrar.append({
                            "Nome": aluno["Nome"],
                            "Email": aluno["E-mail"],
                            "Telefone": str(aluno["Telefone"]).strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                        })

            if len(alunos_para_cobrar) > 0:
                st.write("")
                with st.container(border=True):
                    total_fila = len(alunos_para_cobrar)

                    # 🟩 FLUXO WHATSAPP: Mantém o modelo de fila (um por um por causa do bloqueio do navegador)
                    if canal_envio == "💬 Enviar pelo WhatsApp":
                        st.warning(f"📣 **Fila de Cobrança Ativa (WhatsApp):** Alunos selecionados: **{total_fila}**")
                        aluno_atual = alunos_para_cobrar[0]
                        nome_envio = aluno_atual["Nome"]
                        num_whats = aluno_atual["Telefone"]
                        
                        if not num_whats.startswith("55"):
                            num_whats = "55" + num_whats

                        mensagem_whats = (
                            f"Olá, *{nome_envio}*! 🥋\n\n"
                            f"Aqui é da *Lourenço Filho BJJ*. Passando para lembrar que identificamos uma pendência na sua mensalidade actual. 🥊\n\n"
                            f"Para garantir a sua liberação nos próximos treinos e manter o foco no tatame, por favor, regularize conosco na recepção ou via Pix.\n\n"
                            f"Qualquer dúvida, estamos à disposição! Oss. 🔥"
                        )
                        texto_codificado = urllib.parse.quote(mensagem_whats)
                        link_whatsapp = f"https://api.whatsapp.com/send?phone={num_whats}&text={texto_codificado}"
                        
                        st.info(f"Próxima ação: **{nome_envio}**")
                        st.link_button(f"💬 ABRIR WHATSAPP DE {nome_envio.upper()} ({total_fila} restantes)", link_whatsapp, use_container_width=True)

                    # 🟦 FLUXO E-MAIL: NOVO DISPARO EM LOTE (Envia para todos de uma vez só!)
                    else:
                        st.warning(f"📣 **Preparado para Envio em Lote:** **{total_fila}** e-mail(s) serão enviados de forma 100% automatizada.")
                        
                        # Exibe a lista dos nomes que vão receber o e-mail na tela antes de disparar
                        nomes_lista = ", ".join([a["Nome"] for a in alunos_para_cobrar])
                        st.caption(f"**Destinatários:** {nomes_lista}")
                        
                        if st.button(f"✉️ DISPARAR E-MAIL AGORA PARA TODOS OS {total_fila} ALUNOS", use_container_width=True):
                            sucessos = 0
                            erros = 0
                            
                            # Barra de progresso para acompanhar o envio rodando no background
                            barra_progresso = st.progress(0)
                            status_texto = st.empty()
                            
                            for index, aluno in enumerate(alunos_para_cobrar):
                                nome_envio = aluno["Nome"]
                                email_destino = aluno["Email"]
                                
                                status_texto.write(f"⏳ Enviando ({index + 1}/{total_fila}): {nome_envio}...")
                                
                                mensagem_email = (
                                    f"Olá, {nome_envio}! 🥋\n\n"
                                    f"Aqui é da Lourenço Filho BJJ. Passando para lembrar que identificamos uma pendência na sua mensalidade atual. 🥊\n\n"
                                    f"Para garantir a sua liberação nos próximos treinos e manter o foco no tatame, por favor, regularize conosco na recepção ou via Pix.\n\n"
                                    f"Qualquer dúvida, estamos à disposição! Oss. 🔥"
                                )
                                
                                OK, erro_msg = disparar_email_invisivel(nome_envio, email_destino, mensagem_email)
                                if OK:
                                    sucessos += 1
                                else:
                                    erros += 1
                                
                                # Atualiza a barra dinamicamente
                                barra_progresso.progress((index + 1) / total_fila)
                            
                            status_texto.empty()
                            barra_progresso.empty()
                            
                            if erros == 0:
                                st.success(f"🚀 Sucesso Total! {sucessos} e-mails de cobrança foram enviados perfeitamente sem sair do site!")
                            else:
                                st.warning(f"⚠️ Processo concluído: {sucessos} enviados com sucesso e {erros} falhas técnicas.")
                            
                            time.sleep(3)
                            st.rerun()

                    st.caption("💡 _Nota: Após realizar o disparo, desmarque os alunos da tabela ou avance a página para prosseguir._")

    elif sub_opcao == "⏳ Fila de Espera (QR Code)":
        st.write("Novos alunos aguardando aprovação de cadastro:")
        try:
            conn = obtener_conexao()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, email, plano FROM pre_cadastro WHERE status = 'Pendente' ORDER BY data_solicitacao ASC;")
            solicitacoes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            solicitacoes = []
            
        if not solicitacoes:
            st.success("Tudo em dia! Não há solicitações pendentes.")
        else:
            for s in solicitacoes:
                id_sol, nome_sol, email_sol, plano_sol = s
                with st.container(border=True):
                    col_info, col_sim, col_nao = st.columns([3, 1, 1])
                    with col_info:
                        st.markdown(f"**{nome_sol}**")
                        st.write(f"✉️ {email_sol}")
                        st.caption(f"Plano Escolhido: {plano_sol}")
                    with col_sim:
                        if st.button("✅ ...", key=f"sim_{id_sol}", use_container_width=True):
                            if processar_aprovacao(id_sol, "aprovar"):
                                st.success("Aprovado!")
                                st.rerun()
                    with col_nao:
                        if st.button("❌ ...", key=f"nao_{id_sol}", use_container_width=True):
                            if processar_aprovacao(id_sol, "recusar"):
                                st.warning("Recusado.")
                                st.rerun()