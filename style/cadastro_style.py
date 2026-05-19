import streamlit as st

def aplicar_estilo_cadastro():
    st.markdown("""
    <style>

        /* ==========================================================================
           🎨 CONFIGURAÇÃO GERAL E FUNDO
           ========================================================================== */
        .stApp {
            background-color: #000000 !important;
            color: #ffffff !important;
        }

        /* ==========================================================================
           🏆 TÍTULOS E TEXTOS AUXILIARES
           ========================================================================== */
        h1, h2, h3 {
            color: #ffffff !important;
            text-shadow: 0 0 12px #f6b31e;
            font-family: 'Garamond', serif !important;
            text-transform: uppercase;
            font-weight: bold !important;
        }

        p, label, span {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* ==========================================================================
           🔘 MENU DE FILTRO (SEGMENTED CONTROL)
           ========================================================================== */
        div[data-testid="stSegmentedControl"] {
            gap: 10px !important;
        }

        div[data-testid="stSegmentedControl"] button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            padding: 10px 15px !important;
            transition: all 0.2s ease-in-out !important;
        }

        div[data-testid="stSegmentedControl"] button * {
            color: #ffffff !important;
        }

        div[data-testid="stSegmentedControl"] button:hover {
            background-color: #1a1f2c !important;
            box-shadow: 0 0 15px #f6b31e !important;
        }

        div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            box-shadow: 0 0 20px #f6b31e !important;
        }

        /* ==========================================================================
           📊 BLINDAGEM MÁXIMA DA TABELA (ST.DATAFRAME) - CORRIGIDO
           ========================================================================== */

        /* 1. Container externo com a borda amarela dourada */
        div[data-testid="stDataFrame"] {
            background-color: #000000 !important;
            border: 2px solid #f6b31e !important;
            border-radius: 10px !important;
            padding: 10px !important;
        }

        /* 2. Força o fundo escuro nas camadas de bloco do Streamlit antes do Canvas */
        div[data-testid="stDataFrame"] > div,
        div[data-testid="stDataFrame"] [class*="canvas"],
        div[data-testid="stDataFrame"] [role="grid"] {
            background-color: #000000 !important;
        }

        /* 3. INJEÇÃO DIRETA DE TOKENS NO MOTOR DO GLIDE DATA GRID
           Força o fundo das células a ser preto, letras brancas e linhas douradas.
        */
        div[data-testid="stDataFrame"] {
            /* Cores das Células Normais (Dados) */
            --st-dataframe-bg-color: #000000 !important;
            --st-dataframe-text-color: #ffffff !important;
            --st-dataframe-grid-line-color: #f6b31e !important; /* Linha amarela dourada fixa */
            
            /* Cores dos Cabeçalhos (Nome, E-mail, CPF...) */
            --st-dataframe-header-bg-color: #000000 !important;
            --st-dataframe-header-text-color: #f6b31e !important;
            --st-dataframe-header-grid-line-color: #f6b31e !important;

            /* Variações alternativas que o motor Glide lê */
            --glide-bg: #000000 !important;
            --glide-text-dark: #ffffff !important;
            --glide-text-medium: #ffffff !important;
            --glide-text-light: #ffffff !important;
            --glide-border-color: #f6b31e !important;
            --glide-header-bg: #000000 !important;
            --glide-header-text: #f6b31e !important;
            
            /* Controla o destaque ao clicar/selecionar a célula */
            --glide-accent-color: #f6b31e !important;
            --glide-accent-light: rgba(246, 179, 30, 0.2) !important;
        }

        /* 4. Força o texto de fallback e componentes HTML auxiliares a ficarem brancos */
        div[data-testid="stDataFrame"] * {
            color: #ffffff !important;
            --data-grid-bg: #000000 !important;
            --data-grid-text-color: #ffffff !important;
            --data-grid-line-color: #f6b31e !important;
            --data-grid-header-bg: #000000 !important;
            --data-grid-header-text-color: #f6b31e !important;
        }

        /* 5. Estilização da Scrollbar Amarela Dourada */
        div[data-testid="stDataFrame"] ::-webkit-scrollbar {
            height: 10px;
            width: 10px;
        }

        div[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
            background: #f6b31e !important;
            border-radius: 10px;
        }

        div[data-testid="stDataFrame"] ::-webkit-scrollbar-track {
            background: #000000 !important;
        }

        /* ==========================================================================
           📦 CARDS / FILA DE ESPERA (PRÉ-CADASTRO)
           ========================================================================== */
        div[data-testid="stBlock"] {
            border: 2px solid #f6b31e !important;
            border-radius: 10px !important;
            background-color: #000000 !important;
            padding: 15px !important;
            margin-bottom: 15px !important;
        }

        /* ==========================================================================
           ✨ EFEITOS DECORATIVOS (FAIXAS DA LOGO)
           ========================================================================== */
        .color-strip-top {
            height: 5px;
            background: linear-gradient(to right, #2c3e98, #6d2f78);
            margin-bottom: 20px;
        }

        .color-strip-bottom {
            height: 5px;
            background: linear-gradient(to right, #e0d048, #c86326);
            margin-top: 20px;
        }

    </style>
    """, unsafe_allow_html=True)