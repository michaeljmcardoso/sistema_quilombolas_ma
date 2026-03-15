import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import init_db, load_data, update_status, add_new_community, update_community_info, delete_community, add_contestacao, load_contestacoes, update_contestacao, delete_contestacao, get_comunidade_stats
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Dashboard Quilombolas MA", layout="wide")

# Inicialização do DB
init_db()

# --- TÍTULO E SIDEBAR ---
st.title("📊 Acompanhamento de Metas: Publicação de RTID's e Portarias")
#st.markdown("Controle de andamento processos")

st.sidebar.header("Navegação")
page = st.sidebar.radio("Ir para:", ["Dashboard Geral", "Gestão de Processos", "Progresso Individual"])

# Função para carregar dados com cache (melhora performance)
@st.cache_data(ttl=0)  # ttl=0 significa que os dados serão recarregados a cada interação
def carregar_dados():
    return load_data()

# Carregar dados
df = carregar_dados()

# --- FUNÇÕES AUXILIARES ---
def calcular_progresso(row):
    """Calcula a porcentagem de fases concluídas."""
    fases = [col for col in df.columns if col not in ['id', 'comunidade', 'municipio', 'status_geral']]
    total = len(fases)
    concluídas = sum(1 for fase in fases if row[fase] == 'Concluído')
    return (concluídas / total) * 100 if total > 0 else 0

def get_fase_info(row, fases):
    """Retorna informações detalhadas sobre as fases do processo."""
    fases_com_status = []
    for fase in fases:
        status = row[fase]
        fases_com_status.append({
            'fase': fase.replace('_', ' ').title(),
            'status': status,
            'concluida': status == 'Concluído'
        })
    return fases_com_status

# Definir lista completa de fases
fases_completas = [
    # Fase de Identificação e Delimitação
    "notificação_aos_órgãos_e_entidades", "reunião_de_abertura",
    "comunicações_prévias", "relatório_antropológico", "cadastro_de_famílias",
    "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",
    "rtid_concluído", "reunião_de_validação_na_comunidade",
    
    # Fase de Publicação RTID
    "ficha_resumo_do_RTID", "minuta_de_Edital", "parecer_técnico_1",
    "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação",
    "publicação_DOU", "publicação_DOE", "notificação_aos_órgãos_e_entidades_art_12",
    "notificação_aos_ocupantes", "notificação_aos_confinantes",
    
    # Fase Contenciosa
    "prazo_de_contestação", "pareceres_técnicos", "pareceres_jurídicos",
    "julgamento_da_contestação_no_CDR", "notificações_do_resultado_do_julgamento_do_CDR",
    "prazo_de_recurso", "análise_de_recurso_na_DQ", "julgamento_do_recurso_no_CD",
    "notificações_do_resultado_do_julgamento_do_CD",
    
    # Fase Portaria de Reconhecimento
    "parecer_análise_de_instrução_processual", "instrução_do_kit_portaria",
    "publicação_portaria_DOU", "publicação_portaria_DOE"
]

# Mapeamento das fases por categoria
fases_aba1 = [
    "notificação_aos_órgãos_e_entidades", "reunião_de_abertura",
    "comunicações_prévias", "relatório_antropológico", "cadastro_de_famílias",
    "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",
    "rtid_concluído", "reunião_de_validação_na_comunidade"
]

fases_aba2 = [
    "ficha_resumo_do_RTID", "minuta_de_Edital", "parecer_técnico_1",
    "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação",
    "publicação_DOU", "publicação_DOE", "notificação_aos_órgãos_e_entidades_art_12",
    "notificação_aos_ocupantes", "notificação_aos_confinantes"
]

fases_aba3 = [
    "prazo_de_contestação", "pareceres_técnicos", "pareceres_jurídicos",
    "julgamento_da_contestação_no_CDR", "notificações_do_resultado_do_julgamento_do_CDR",
    "prazo_de_recurso", "análise_de_recurso_na_DQ", "julgamento_do_recurso_no_CD",
    "notificações_do_resultado_do_julgamento_do_CD"
]

fases_aba4 = [
    "parecer_análise_de_instrução_processual", "instrução_do_kit_portaria",
    "publicação_portaria_DOU", "publicação_portaria_DOE"
]

# --- PÁGINA 1: DASHBOARD ---
if page == "Dashboard Geral":
    st.header("Visão Geral")
    
    if not df.empty:
        # Definir metas
        META_RTID = 8
        META_PORTARIAS = 3
        
        # ============================================
        # FUNÇÕES DE CÁLCULO DE PROGRESSO ESPECÍFICAS
        # ============================================
        
        # Identificar fases até a publicação do RTID
        fases_ate_rtid = [
            # Fase de Identificação e Delimitação (todas)
            "notificação_aos_órgãos_e_entidades", "reunião_de_abertura",
            "comunicações_prévias", "relatório_antropológico", "cadastro_de_famílias",
            "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",
            "rtid_concluído", "reunião_de_validação_na_comunidade",
            
            # Fase de Publicação RTID (todas até a publicação)
            "ficha_resumo_do_RTID", "minuta_de_Edital", "parecer_técnico_1",
            "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação",
            "publicação_DOU",
        ]
        
        # Identificar fases específicas da Portaria de Reconhecimento
        fases_portaria = [
            "parecer_análise_de_instrução_processual",
            "instrução_do_kit_portaria",
            "publicação_portaria_DOU",
            "publicação_portaria_DOE"
        ]
        
        def calcular_progresso_meta(row, fases_meta):
            """Calcula o progresso considerando apenas as fases da meta."""
            fases_presentes = [f for f in fases_meta if f in row.index]
            if not fases_presentes:
                return 0
            total = len(fases_presentes)
            concluidas = sum(1 for fase in fases_presentes if row[fase] == 'Concluído')
            return (concluidas / total) * 100 if total > 0 else 0
        
        # Calcular progressos
        df['Progresso_RTID'] = df.apply(lambda row: calcular_progresso_meta(row, fases_ate_rtid), axis=1)
        df['Progresso_Portaria'] = df.apply(lambda row: calcular_progresso_meta(row, fases_portaria), axis=1)
        df['Progresso_Geral'] = df.apply(calcular_progresso, axis=1)
        
        # Criar colunas de status
        df['Status_RTID'] = df['publicação_DOU'].apply(
            lambda x: '✅ Publicado' if x == 'Concluído'
            else '🔄 Em Andamento' if x == 'Em Andamento'
            else '⏳ Pendente' if x == 'Pendente'
            else '🚫 Não Aplicável'
        )
        
        def status_portaria(row):
            if row['publicação_portaria_DOU'] == 'Concluído' or row['publicação_portaria_DOE'] == 'Concluído':
                return '✅ Publicada'
            elif row['publicação_portaria_DOU'] == 'Em Andamento' or row['publicação_portaria_DOE'] == 'Em Andamento':
                return '🔄 Em Andamento'
            elif row['publicação_portaria_DOU'] == 'Pendente' and row['publicação_portaria_DOE'] == 'Pendente':
                return '⏳ Pendente'
            else:
                return '🚫 Não Aplicável'
        
        df['Status_Portaria'] = df.apply(status_portaria, axis=1)
        
        # Métricas
        rtid_dou_publicado = len(df[df['publicação_DOU'] == 'Concluído'])
        progresso_rtid_meta = (rtid_dou_publicado / META_RTID * 100) if META_RTID > 0 else 0
        
        portarias_publicadas = len(df[
            (df['publicação_portaria_DOU'] == 'Concluído') | 
            (df['publicação_portaria_DOE'] == 'Concluído')
        ])
        progresso_portarias_meta = (portarias_publicadas / META_PORTARIAS * 100) if META_PORTARIAS > 0 else 0
        
        # Métricas
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("🎯 Meta RTID", f"{META_RTID}")
        with col2:
            st.metric("📄 RTID's Publicados", f"{rtid_dou_publicado} / {META_RTID}")
        with col3:
            st.metric("📊 % Meta RTID", f"{progresso_rtid_meta:.1f}%")
        with col4:
            st.metric("🎯 Meta Portarias", f"{META_PORTARIAS}")
        with col5:
            st.metric("📜 Portarias Publicadas", f"{portarias_publicadas} / {META_PORTARIAS}")
        with col6:
            st.metric("📊 % Meta Portarias", f"{progresso_portarias_meta:.1f}%")

        st.divider()
        
        # ============================================
        # FUNÇÃO PARA CRIAR GRÁFICO DE FASES
        # ============================================
        
        def criar_grafico_fases(df, coluna_progresso, fases_meta, titulo):
            """
            Cria um gráfico de fases similar ao de fase mais avançada
            """
            # Encontrar a fase mais avançada baseada no progresso da meta específica
            def encontrar_fase_por_progresso(row, fases_meta):
                ordem_fases = {fase: idx for idx, fase in enumerate(fases_meta)}
                fase_atual = "Não Iniciado"
                ordem_atual = -1
                status_atual = "Pendente"
                
                for fase in fases_meta:
                    if fase in row.index:
                        status = row[fase]
                        if status != 'Pendente' and status != 'Não Aplicável':
                            if ordem_fases[fase] > ordem_atual:
                                fase_atual = fase
                                ordem_atual = ordem_fases[fase]
                                status_atual = status
                return fase_atual, ordem_atual, status_atual
            
            # Aplicar para as fases da meta
            resultados = df.apply(lambda row: encontrar_fase_por_progresso(row, fases_meta), axis=1)
            
            df_temp = df.copy()
            df_temp['Fase Atual'] = [r[0] for r in resultados]
            df_temp['Ordem Fase'] = [r[1] for r in resultados]
            df_temp['Status Fase'] = [r[2] for r in resultados]
            
            # Nomes amigáveis
            nomes_fases = {
                fase: fase.replace('_', ' ').title() 
                for fase in fases_meta
            }
            nomes_fases["Não Iniciado"] = "⏳ Não Iniciado"
            
            df_temp['Fase Atual Nome'] = df_temp['Fase Atual'].apply(
                lambda x: nomes_fases.get(x, x)
            )
            
            # Status formatado
            def formatar_status(status):
                emojis = {
                    'Concluído': '✅ Concluído',
                    'Em Andamento': '🔄 Em Andamento',
                    'Pendente': '⏳ Pendente',
                    'Não Aplicável': '🚫 Não Aplicável'
                }
                return emojis.get(status, f'❓ {status}')
            
            df_temp['Status Formatado'] = df_temp['Status Fase'].apply(formatar_status)
            
            # Ordenar
            df_temp_sorted = df_temp.sort_values('Ordem Fase', ascending=True)
            
            # Lista de fases ordenadas
            todas_fases_ordenadas = ["⏳ Não Iniciado"] + [nomes_fases[f] for f in fases_meta]
            
            # Hover customizado
            hover_custom = {
                'comunidade': True,
                'municipio': True,
                'Fase Atual Nome': True,
                'Status Formatado': True,
                coluna_progresso: ':.1f',
                'Ordem Fase': False
            }
            
            # Criar gráfico
            fig = px.bar(
                df_temp_sorted,
                x='Ordem Fase',
                y='comunidade',
                orientation='h',
                color='Fase Atual Nome',
                color_discrete_sequence=px.colors.qualitative.Set1,
                title=titulo,
                hover_data=hover_custom,
                labels={
                    'Ordem Fase': 'Fase do Processo',
                    'comunidade': 'Comunidade',
                    'municipio': 'Município',
                    'Fase Atual Nome': 'Fase Atual',
                    'Status Formatado': 'Status da Fase',
                    coluna_progresso: 'Progresso (%)'
                },
                category_orders={'Fase Atual Nome': todas_fases_ordenadas}
            )
            
            # Configurar ticks
            tick_vals = [-1] + [i for i in range(len(fases_meta))]
            tick_text = ["⏳ Não Iniciado"] + [nomes_fases[f] for f in fases_meta]
            
            fig.update_layout(
                xaxis=dict(
                    title="Fase do Processo",
                    tickmode='array',
                    tickvals=tick_vals,
                    ticktext=tick_text,
                    tickangle=45,
                    tickfont=dict(size=10),
                    range=[-1.5, len(fases_meta) + 0.5]
                ),
                yaxis=dict(
                    title="",
                    tickfont=dict(size=14)
                ),
                height=max(500, len(df) * 30),
                showlegend=False,
                hoverlabel=dict(
                    bgcolor="black",
                    font_size=14,
                    font_family="Arial",
                    namelength=-1
                )
            )
            
            # Adicionar linhas verticais
            for i in range(len(tick_vals)):
                if i > 0:
                    fig.add_vline(x=i-1.5, line_width=1, line_dash="dash", line_color="gray", opacity=0.3)
            
            return fig
        
        # ============================================
        # GRÁFICO 1: PROGRESSO DA META RTID
        # ============================================
        st.subheader("📄 Progresso da Meta RTID")
        
        fig_rtid = criar_grafico_fases(
            df, 
            'Progresso_RTID',
            fases_ate_rtid,
            "Fase Atual do Processo até Publicação do RTID no DOU"
        )
        
        st.plotly_chart(fig_rtid, use_container_width=True)
        
        # Tabela resumo RTID
        with st.expander("📋 Ver detalhes da Meta RTID", expanded=False):
            df_rtid_resumo = df[['comunidade', 'municipio', 'Progresso_RTID', 'Status_RTID']].copy()
            df_rtid_resumo = df_rtid_resumo.sort_values('Progresso_RTID', ascending=False)
            df_rtid_resumo['Progresso_RTID'] = df_rtid_resumo['Progresso_RTID'].round(1).astype(str) + '%'
            st.dataframe(
                df_rtid_resumo,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "comunidade": "Comunidade",
                    "municipio": "Município",
                    "Progresso_RTID": "Progresso RTID",
                    "Status_RTID": "Status Publicação"
                }
            )
        
        st.divider()
        
        # ============================================
        # GRÁFICO 2: PROGRESSO DA META PORTARIA
        # ============================================
        st.subheader("📜 Progresso da Meta Portaria de Reconhecimento")
        
        fig_portaria = criar_grafico_fases(
            df, 
            'Progresso_Portaria',
            fases_portaria,
            "Fase Atual do Processo nas Etapas da Portaria"
        )
        
        st.plotly_chart(fig_portaria, use_container_width=True)
        
        # Tabela resumo Portaria
        with st.expander("📋 Ver detalhes da Meta Portaria", expanded=False):
            df_portaria_resumo = df[['comunidade', 'municipio', 'Progresso_Portaria', 'Status_Portaria']].copy()
            df_portaria_resumo = df_portaria_resumo.sort_values('Progresso_Portaria', ascending=False)
            df_portaria_resumo['Progresso_Portaria'] = df_portaria_resumo['Progresso_Portaria'].round(1).astype(str) + '%'
            
            # Adicionar colunas individuais das fases da portaria
            df_portaria_resumo['Parecer'] = df['parecer_análise_de_instrução_processual'].apply(
                lambda x: '✅' if x == 'Concluído' else '🔄' if x == 'Em Andamento' else '⏳' if x == 'Pendente' else '🚫'
            )
            df_portaria_resumo['Instrução'] = df['instrução_do_kit_portaria'].apply(
                lambda x: '✅' if x == 'Concluído' else '🔄' if x == 'Em Andamento' else '⏳' if x == 'Pendente' else '🚫'
            )
            df_portaria_resumo['DOU'] = df['publicação_portaria_DOU'].apply(
                lambda x: '✅' if x == 'Concluído' else '🔄' if x == 'Em Andamento' else '⏳' if x == 'Pendente' else '🚫'
            )
            df_portaria_resumo['DOE'] = df['publicação_portaria_DOE'].apply(
                lambda x: '✅' if x == 'Concluído' else '🔄' if x == 'Em Andamento' else '⏳' if x == 'Pendente' else '🚫'
            )
            
            st.dataframe(
                df_portaria_resumo,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "comunidade": "Comunidade",
                    "municipio": "Município",
                    "Progresso_Portaria": "Progresso",
                    "Status_Portaria": "Status Geral",
                    "Parecer": "Parecer",
                    "Instrução": "Instrução",
                    "DOU": "DOU",
                    "DOE": "DOE"
                }
            )
        
        st.divider()
        
        # ============================================
        # GRÁFICO 3: FASE MAIS AVANÇADA (geral)
        # ============================================
        st.subheader("📋 Fase Mais Avançada de Cada Processo (Todas as Fases)")

        # Função para encontrar a fase mais avançada (todas as fases)
        def encontrar_fase_mais_avancada_geral(row):
            ordem_fases = {fase: idx for idx, fase in enumerate(fases_completas)}
            fase_mais_avancada = "Não Iniciado"
            ordem_mais_avancada = -1
            status_fase_mais_avancada = "Pendente"
            
            for fase in fases_completas:
                status = row[fase] if fase in row.index else "Pendente"
                if status != 'Pendente' and status != 'Não Aplicável':
                    if ordem_fases[fase] > ordem_mais_avancada:
                        fase_mais_avancada = fase
                        ordem_mais_avancada = ordem_fases[fase]
                        status_fase_mais_avancada = status
            return fase_mais_avancada, ordem_mais_avancada, status_fase_mais_avancada

        # Aplicar função
        resultados = df.apply(encontrar_fase_mais_avancada_geral, axis=1)
        df['Fase Mais Avançada'] = [r[0] for r in resultados]
        df['Ordem Fase Mais Avançada'] = [r[1] for r in resultados]
        df['Status Fase Mais Avançada'] = [r[2] for r in resultados]

        # Criar nomes amigáveis
        nomes_fases_amigaveis = {
            fase: fase.replace('_', ' ').title() 
            for fase in fases_completas
        }
        nomes_fases_amigaveis["Não Iniciado"] = "⏳ Não Iniciado"

        df['Fase Mais Avançada Nome'] = df['Fase Mais Avançada'].apply(
            lambda x: nomes_fases_amigaveis.get(x, x)
        )

        # Status formatado
        def formatar_status(status):
            emojis = {
                'Concluído': '✅ Concluído',
                'Em Andamento': '🔄 Em Andamento',
                'Pendente': '⏳ Pendente',
                'Não Aplicável': '🚫 Não Aplicável'
            }
            return emojis.get(status, f'❓ {status}')

        df['Status Fase Formatado'] = df['Status Fase Mais Avançada'].apply(formatar_status)

        # Ordenar
        df_sorted = df.sort_values('Ordem Fase Mais Avançada', ascending=True)
        todas_fases_ordenadas = ["⏳ Não Iniciado"] + [nomes_fases_amigaveis[f] for f in fases_completas]

        # Hover customizado
        hover_customizado = {
            'comunidade': True,
            'municipio': True,
            'Fase Mais Avançada Nome': True,
            'Status Fase Formatado': True,
            'Progresso_Geral': ':.1f',
            'Ordem Fase Mais Avançada': False
        }

        fig_fase_atual = px.bar(
            df_sorted,
            x='Ordem Fase Mais Avançada',
            y='comunidade',
            orientation='h',
            color='Fase Mais Avançada Nome',
            color_discrete_sequence=px.colors.qualitative.Set1,
            title="Fase Mais Avançada de Cada Processo (Todas as Fases)",
            hover_data=hover_customizado,
            labels={
                'Ordem Fase Mais Avançada': 'Fase do Processo',
                'comunidade': 'Comunidade',
                'municipio': 'Município',
                'Fase Mais Avançada Nome': 'Fase Atual',
                'Status Fase Formatado': 'Status da Fase',
                'Progresso_Geral': 'Progresso Geral (%)'
            },
            category_orders={'Fase Mais Avançada Nome': todas_fases_ordenadas}
        )

        tick_vals = [-1] + [i for i in range(len(fases_completas))]
        tick_text = ["⏳ Não Iniciado"] + [nomes_fases_amigaveis[f] for f in fases_completas]

        fig_fase_atual.update_layout(
            xaxis=dict(
                title="Fase do Processo",
                tickmode='array',
                tickvals=tick_vals,
                ticktext=tick_text,
                tickangle=45,
                tickfont=dict(size=10),
                range=[-1.5, len(fases_completas) + 0.5]
            ),
            yaxis=dict(
                title="",
                tickfont=dict(size=14)
            ),
            height=max(600, len(df) * 35),
            showlegend=False,
            hoverlabel=dict(
                bgcolor="black",
                font_size=14,
                font_family="Arial",
                namelength=-1
            )
        )

        # Adicionar linhas verticais
        for i in range(len(tick_vals)):
            if i > 0:
                fig_fase_atual.add_vline(x=i-1.5, line_width=1, line_dash="dash", line_color="gray", opacity=0.3)

        st.plotly_chart(fig_fase_atual, use_container_width=True)

        # Tabela comparativa
        st.divider()
        st.subheader("📊 Comparativo de Progresso por Meta")
        
        df_comparativo = df[['comunidade', 'municipio', 'Progresso_RTID', 'Progresso_Portaria', 'Progresso_Geral']].copy()
        df_comparativo = df_comparativo.sort_values('Progresso_Portaria', ascending=False)
        df_comparativo['Progresso_RTID'] = df_comparativo['Progresso_RTID'].round(1).astype(str) + '%'
        df_comparativo['Progresso_Portaria'] = df_comparativo['Progresso_Portaria'].round(1).astype(str) + '%'
        df_comparativo['Progresso_Geral'] = df_comparativo['Progresso_Geral'].round(1).astype(str) + '%'
        
        st.dataframe(
            df_comparativo,
            use_container_width=True,
            hide_index=True,
            column_config={
                "comunidade": "Comunidade",
                "municipio": "Município",
                "Progresso_RTID": "Progresso RTID",
                "Progresso_Portaria": "Progresso Portaria",
                "Progresso_Geral": "Progresso Geral"
            }
        )
        
        # Legenda
        st.caption("""
        **ℹ️ Como interpretar os gráficos:**
        - **Gráfico 1 (RTID)**: Mostra a fase atual considerando apenas as fases até a publicação do RTID no DOU
        - **Gráfico 2 (Portaria)**: Mostra a fase atual considerando apenas as 4 fases específicas da portaria
        - **Gráfico 3 (Geral)**: Mostra a fase mais avançada considerando todas as fases do processo
        
        **Ordem do hover:**
        1. Comunidade
        2. Município
        3. Fase Atual
        4. Status da Fase
        5. Progresso (%)
        """)
        
    else:
        st.info("ℹ️ Nenhuma comunidade cadastrada ainda. Vá para a aba 'Gestão de Processos' para adicionar.")

# --- PÁGINA 2: GESTÃO DE PROCESSOS ---
elif page == "Gestão de Processos":
    st.header("⚙️ Gestão e Edição de Processos")
    
    # Aba para Adicionar Nova Comunidade
    with st.expander("➕ Cadastrar Nova Comunidade", expanded=False):
        with st.form("add_form"):
            novo_nome = st.text_input("Nome da Comunidade")
            novo_mun = st.text_input("Município")
            submit = st.form_submit_button("📌 Cadastrar")
            if submit and novo_nome:
                success, msg = add_new_community(novo_nome, novo_mun)
                if success:
                    st.success(msg)
                    st.cache_data.clear()  # Limpar cache
                    st.rerun()
                else:
                    st.error(msg)
    
    if not df.empty:
        # Seleção da Comunidade
        if 'selected_comunidade' not in st.session_state:
            st.session_state.selected_comunidade = df['comunidade'].iloc[0]
        
        selected_comunidade = st.selectbox(
            "🔍 Selecione a Comunidade para Editar:",
            df['comunidade'].unique(),
            index=list(df['comunidade'].unique()).index(st.session_state.selected_comunidade) if st.session_state.selected_comunidade in df['comunidade'].unique() else 0,
            key="comunidade_selector"
        )
        st.session_state.selected_comunidade = selected_comunidade
        
        # Recarregar dados específicos da comunidade
        df = carregar_dados()
        row = df[df['comunidade'] == selected_comunidade].iloc[0]
        
        # ==============================================
        # SEÇÃO 1: EDITAR DADOS BÁSICOS
        # ==============================================
        with st.expander("✏️ Editar Dados da Comunidade", expanded=True):
            
            # Inicializar estado de confirmação no session_state
            if 'confirmar_exclusao' not in st.session_state:
                st.session_state.confirmar_exclusao = False
            
            with st.form("edit_basic_data"):
                col1, col2 = st.columns(2)
                with col1:
                    nome_editado = st.text_input(
                        "Nome da Comunidade",
                        value=row['comunidade']
                    )
                with col2:
                    municipio_editado = st.text_input(
                        "Município",
                        value=row['municipio']
                    )
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                with col_btn1:
                    save_basic = st.form_submit_button("💾 Salvar Alterações")
                with col_btn2:
                    delete_btn = st.form_submit_button("🗑️ Excluir Comunidade")
                
                if save_basic:
                    if nome_editado != row['comunidade'] or municipio_editado != row['municipio']:
                        success, msg = update_community_info(
                            selected_comunidade, nome_editado, municipio_editado
                        )
                        if success:
                            st.success(msg)
                            st.cache_data.clear()
                            st.session_state.selected_comunidade = nome_editado
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.info("ℹ️ Nenhuma alteração detectada.")
                
                if delete_btn:
                    # Ativar modo de confirmação
                    st.session_state.confirmar_exclusao = True
                    st.rerun()
            
            # Área de confirmação fora do formulário
            if st.session_state.confirmar_exclusao:
                st.warning(f"⚠️ **Tem certeza que deseja excluir '{selected_comunidade}'?** Esta ação não pode ser desfeita.")
                
                col_confirm1, col_confirm2 = st.columns([1, 3])
                with col_confirm1:
                    if st.button("✅ Sim, excluir", key="confirmar_sim"):
                        success, msg = delete_community(selected_comunidade)
                        if success:
                            st.success(msg)
                            st.cache_data.clear()
                            st.session_state.confirmar_exclusao = False
                            if len(df) > 1:
                                # Selecionar outra comunidade
                                novas_comunidades = [c for c in df['comunidade'].unique() if c != selected_comunidade]
                                st.session_state.selected_comunidade = novas_comunidades[0]
                            st.rerun()
                        else:
                            st.error(msg)
                
                with col_confirm2:
                    if st.button("❌ Não, cancelar", key="confirmar_nao"):
                        st.session_state.confirmar_exclusao = False
                        st.rerun()
            
            st.markdown(f"### Editando Fases: **{row['comunidade']}** ({row['municipio']})")
        
        # ==============================================
        # SEÇÃO 2: EDITAR FASES DO PROCESSO
        # ==============================================
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Fase de Identificação e Delimitação",
            "📄 Fase de Publicação RTID",
            "⚖️ Fase Contenciosa",
            "📜 Fase Portaria de Reconhecimento"
        ])
        
        def criar_formulario_edicao(tab, lista_fases):
            with tab:
                # Usar session_state para controlar atualizações
                if f'ultima_atualizacao_{selected_comunidade}' not in st.session_state:
                    st.session_state[f'ultima_atualizacao_{selected_comunidade}'] = datetime.now().timestamp()
                
                cols = st.columns(2)
                atualizacoes = []
                
                for i, fase in enumerate(lista_fases):
                    with cols[i % 2]:
                        # Garantir que temos o status mais recente
                        df_atual = carregar_dados()
                        row_atual = df_atual[df_atual['comunidade'] == selected_comunidade].iloc[0]
                        status_atual = row_atual[fase] if fase in row_atual.index else "Pendente"
                        
                        # Criar chave única para o selectbox
                        select_key = f"{selected_comunidade}_{fase}_{st.session_state[f'ultima_atualizacao_{selected_comunidade}']}"
                        
                        novo_status = st.selectbox(
                            f"📌 {fase.replace('_', ' ').title()}",
                            options=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"],
                            index=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"].index(status_atual),
                            key=select_key
                        )
                        
                        # Se mudou, registrar para atualização
                        if novo_status != status_atual:
                            atualizacoes.append((fase, novo_status))
                
                # Botão para aplicar todas as alterações de uma vez
                if atualizacoes:
                    st.markdown("---")
                    st.warning(f"**{len(atualizacoes)} alteração(ões) detectada(s)**")
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("✅ Aplicar Todas as Alterações", key=f"apply_all_{selected_comunidade}"):
                            sucessos = 0
                            erros = 0
                            for fase, novo_status in atualizacoes:
                                success, msg = update_status(selected_comunidade, fase, novo_status)
                                if success:
                                    sucessos += 1
                                else:
                                    erros += 1
                                    st.error(f"Erro em {fase}: {msg}")
                            
                            if sucessos > 0:
                                st.success(f"✅ {sucessos} fase(s) atualizada(s) com sucesso!")
                                # Atualizar timestamp para forçar recriação dos componentes
                                st.session_state[f'ultima_atualizacao_{selected_comunidade}'] = datetime.now().timestamp()
                                st.cache_data.clear()
                                st.rerun()
        
        criar_formulario_edicao(tab1, fases_aba1)
        criar_formulario_edicao(tab2, fases_aba2)
        criar_formulario_edicao(tab3, fases_aba3)
        criar_formulario_edicao(tab4, fases_aba4)
        
        # ==============================================
        # SEÇÃO 3: CADASTRO DE CONTESTAÇÕES
        # ==============================================
        st.divider()
        st.subheader("⚖️ Contestações")
        
        # Carregar contestações
        df_contestacoes = load_contestacoes(selected_comunidade)
        
        # Expander para adicionar nova contestação
        with st.expander("➕ Cadastrar Nova Contestação"):
            with st.form("add_contestacao_form"):
                col1, col2 = st.columns(2)
                with col1:
                    nome_req = st.text_input("Nome do Requerente")
                    data_notif = st.date_input("Data da Notificação", value=None)
                with col2:
                    data_receb = st.date_input("Data do Recebimento", value=None)
                    data_edital = st.date_input("Data do Edital de Notificação", value=None)
                
                descricao = st.text_area("Descrição/Observações")
                submit_contest = st.form_submit_button("📌 Cadastrar Contestação")
                
                if submit_contest and nome_req:
                    data_notif_str = data_notif.strftime("%Y-%m-%d") if data_notif else None
                    data_receb_str = data_receb.strftime("%Y-%m-%d") if data_receb else None
                    data_edital_str = data_edital.strftime("%Y-%m-%d") if data_edital else None
                    
                    success, msg = add_contestacao(
                        selected_comunidade, nome_req, data_notif_str,
                        data_receb_str, data_edital_str, descricao
                    )
                    if success:
                        st.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)
        
        # Visualizar contestações existentes
        if not df_contestacoes.empty:
            st.markdown(f"**Total de Contestações:** {len(df_contestacoes)}")
            for index, row_contest in df_contestacoes.iterrows():
                with st.expander(f"📄 Contestação #{row_contest['id']} - {row_contest['nome_requerente']} ({row_contest['status']})"):
                    with st.form(f"edit_contest_{row_contest['id']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nome_edit = st.text_input("Nome do Requerente", value=row_contest['nome_requerente'])
                            data_notif_edit = st.date_input(
                                "Data da Notificação",
                                value=pd.to_datetime(row_contest['data_notificacao']) if pd.notna(row_contest['data_notificacao']) else None
                            )
                            data_receb_edit = st.date_input(
                                "Data do Recebimento",
                                value=pd.to_datetime(row_contest['data_recebimento']) if pd.notna(row_contest['data_recebimento']) else None
                            )
                        with col2:
                            data_edital_edit = st.date_input(
                                "Data do Edital de Notificação",
                                value=pd.to_datetime(row_contest['data_edital_notificacao']) if pd.notna(row_contest['data_edital_notificacao']) else None
                            )
                            status_edit = st.selectbox(
                                "Status",
                                ["Ativa", "Encerrada", "Improcedente", "Procedente"],
                                index=["Ativa", "Encerrada", "Improcedente", "Procedente"].index(row_contest['status'])
                            )
                        
                        desc_edit = st.text_area(
                            "Descrição/Observações",
                            value=row_contest['descricao'] if pd.notna(row_contest['descricao']) else ""
                        )
                        
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            save_contest = st.form_submit_button("💾 Salvar")
                        with col_btn2:
                            del_contest = st.form_submit_button("🗑️ Excluir")
                        
                        if save_contest:
                            data_notif_str = data_notif_edit.strftime("%Y-%m-%d") if data_notif_edit else None
                            data_receb_str = data_receb_edit.strftime("%Y-%m-%d") if data_receb_edit else None
                            data_edital_str = data_edital_edit.strftime("%Y-%m-%d") if data_edital_edit else None
                            
                            success, msg = update_contestacao(
                                row_contest['id'], nome_edit, data_notif_str,
                                data_receb_str, data_edital_str, desc_edit, status_edit
                            )
                            if success:
                                st.success(msg)
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(msg)
                        
                        if del_contest:
                            if st.checkbox(f"Confirmar exclusão da contestação #{row_contest['id']}?", key=f"confirm_del_{row_contest['id']}"):
                                success, msg = delete_contestacao(row_contest['id'])
                                if success:
                                    st.success(msg)
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(msg)
        else:
            st.info("ℹ️ Nenhuma contestação cadastrada para esta comunidade.")
    else:
        st.warning("⚠️ Nenhuma comunidade encontrada. Cadastre uma nova comunidade para começar.")

# --- PÁGINA 3: PROGRESSO INDIVIDUAL ---
elif page == "Progresso Individual":
    st.header("📈 Progresso Individual por Processo")
    
    if not df.empty:
        # Selecionar comunidade
        selected_comunidade = st.selectbox(
            "🔍 Selecione a Comunidade para Visualizar:",
            df['comunidade'].unique(),
            key="progresso_individual_select"
        )
        
        # Recarregar dados
        df = carregar_dados()
        row = df[df['comunidade'] == selected_comunidade].iloc[0]
        
        # Calcular progresso
        progresso = calcular_progresso(row)
        
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏠 Comunidade", selected_comunidade)
        with col2:
            st.metric("📍 Município", row['municipio'])
        with col3:
            st.metric("📊 Progresso Geral", f"{progresso:.1f}%")
        
        st.divider()
        
        # Gráfico de Gauge para progresso geral
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=progresso,
            title={'text': "Progresso Geral do Processo"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 30], 'color': "lightcoral"},
                    {'range': [30, 70], 'color': "gold"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Progresso detalhado por fase
        st.subheader("📋 Detalhamento por Fase")
        
        # Agrupar fases por categoria
        categorias = {
            "Fase de Identificação e Delimitação": fases_aba1,
            "Fase de Publicação RTID": fases_aba2,
            "Fase Contenciosa": fases_aba3,
            "Fase Portaria de Reconhecimento": fases_aba4
        }
        
        # Criar abas para cada categoria
        tabs = st.tabs(list(categorias.keys()))
        
        for tab, (categoria, lista_fases) in zip(tabs, categorias.items()):
            with tab:
                # Calcular progresso da categoria
                fases_cat = [f for f in lista_fases if f in row.index]
                total_cat = len(fases_cat)
                concluidas_cat = sum(1 for f in fases_cat if row[f] == 'Concluído')
                progresso_cat = (concluidas_cat / total_cat * 100) if total_cat > 0 else 0
                
                st.metric(f"Progresso da {categoria}", f"{progresso_cat:.1f}%")
                
                # Criar DataFrame para visualização
                dados_fases = []
                for fase in lista_fases:
                    if fase in row.index:
                        status = row[fase]
                        cor = {
                            'Concluído': '✅',
                            'Em Andamento': '🔄',
                            'Pendente': '⏳',
                            'Não Aplicável': '🚫'
                        }.get(status, '❓')
                        
                        dados_fases.append({
                            'Fase': fase.replace('_', ' ').title(),
                            'Status': f"{cor} {status}",
                            'Concluída': status == 'Concluído'
                        })
                
                if dados_fases:
                    df_fases = pd.DataFrame(dados_fases)
                    
                    # Gráfico de barras para as fases
                    fig_fases = px.bar(
                        df_fases,
                        x='Fase',
                        y='Concluída',
                        title=f"Status das Fases - {categoria}",
                        labels={'Concluída': 'Concluída', 'Fase': 'Fase'},
                        color='Concluída',
                        color_discrete_map={True: '#2ecc71', False: '#e74c3c'}
                    )
                    fig_fases.update_layout(
                        xaxis_tickangle=-45,
                        height=400,
                        showlegend=False
                    )
                    st.plotly_chart(fig_fases, use_container_width=True)
                    
                    # Tabela detalhada
                    st.dataframe(
                        df_fases[['Fase', 'Status']],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(f"ℹ️ Nenhuma fase encontrada para {categoria}")
        
        # Contestações relacionadas
        st.divider()
        st.subheader("⚖️ Contestações do Processo")
        
        df_contestacoes = load_contestacoes(selected_comunidade)
        if not df_contestacoes.empty:
            for _, contest in df_contestacoes.iterrows():
                with st.expander(f"📄 Contestação: {contest['nome_requerente']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Status:** {contest['status']}")
                        st.write(f"**Data Notificação:** {contest['data_notificacao']}")
                    with col2:
                        st.write(f"**Data Recebimento:** {contest['data_recebimento']}")
                        st.write(f"**Data Edital:** {contest['data_edital_notificacao']}")
                    if pd.notna(contest['descricao']):
                        st.write(f"**Observações:** {contest['descricao']}")
        else:
            st.info("ℹ️ Nenhuma contestação registrada para esta comunidade.")
    else:
        st.warning("⚠️ Nenhuma comunidade encontrada. Cadastre comunidades na aba 'Gestão de Processos'.")