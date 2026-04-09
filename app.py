import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import (
    init_db, 
    load_rtid_data, load_portaria_data,
    update_rtid_status, update_portaria_status,
    add_rtid_community, update_rtid_community_info, delete_rtid_community,
    add_portaria_community, update_portaria_community_info, delete_portaria_community,
    add_contestacao, load_contestacoes, update_contestacao, delete_contestacao
)
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Dashboard Quilombolas MA", layout="wide")

# Inicialização do DB
init_db()

# --- TÍTULO E SIDEBAR ---
st.title("📊 Cardeno de Metas: Publicação de RTID's e Portarias")
st.markdown("Controle de andamento processos")

st.sidebar.header("Navegação")
page = st.sidebar.radio(
    "Ir para:", 
    ["Dashboard Geral", "Gestão RTID", "Gestão Portaria", "Progresso Individual RTID", "Progresso Individual Portaria"]
)

# Função para carregar dados com cache
@st.cache_data(ttl=0)
def carregar_dados_rtid():
    return load_rtid_data()

@st.cache_data(ttl=0)
def carregar_dados_portaria():
    return load_portaria_data()

# Carregar dados
df_rtid = carregar_dados_rtid()
df_portaria = carregar_dados_portaria()

# --- FUNÇÕES AUXILIARES ---
def calcular_progresso(row, fases):
    """Calcula a porcentagem de fases concluídas."""
    fases_presentes = [f for f in fases if f in row.index]
    total = len(fases_presentes)
    concluidas = sum(1 for fase in fases_presentes if row[fase] == 'Concluído')
    return (concluidas / total) * 100 if total > 0 else 0

# Definir listas de fases
fases_completas = [
    "notificação_aos_órgãos_e_entidades", "reunião_de_abertura",
    "comunicações_prévias", "relatório_antropológico", "cadastro_de_famílias",
    "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",
    "rtid_concluído", "reunião_de_validação_na_comunidade",
    "ficha_resumo_do_RTID", "minuta_de_Edital", "parecer_técnico_1",
    "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação",
    "publicação_DOU", "publicação_DOE", "notificação_aos_órgãos_e_entidades_art_12",
    "notificação_aos_ocupantes", "notificação_aos_confinantes",
    "prazo_de_contestação", "pareceres_técnicos", "pareceres_jurídicos",
    "julgamento_da_contestação_no_CDR", "notificações_do_resultado_do_julgamento_do_CDR",
    "prazo_de_recurso", "análise_de_recurso_na_DQ", "julgamento_do_recurso_no_CD",
    "notificações_do_resultado_do_julgamento_do_CD",
    "parecer_análise_de_instrução_processual", "instrução_do_kit_portaria",
    "publicação_portaria_DOU", "publicação_portaria_DOE"
]

fases_ate_rtid = [
    "notificação_aos_órgãos_e_entidades", "reunião_de_abertura",
    "comunicações_prévias", "relatório_antropológico", "cadastro_de_famílias",
    "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",
    "rtid_concluído", "reunião_de_validação_na_comunidade",
    "ficha_resumo_do_RTID", "minuta_de_Edital", "parecer_técnico_1",
    "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação",
    "publicação_DOU", "notificação_aos_órgãos_e_entidades_art_12",
    "notificação_aos_ocupantes", "notificação_aos_confinantes",
]

fases_portaria = [
    "parecer_análise_de_instrução_processual",
    "instrução_do_kit_portaria",
    "publicação_portaria_DOU",
    "publicação_portaria_DOE"
]

# --- PÁGINA 1: DASHBOARD GERAL ---
if page == "Dashboard Geral":
    st.header("Visão Geral")
    
    # Definir metas
    META_RTID = 8
    META_PORTARIAS = 3
    
    # Calcular progressos para RTID
    if not df_rtid.empty:
        df_rtid['Progresso_RTID'] = df_rtid.apply(lambda row: calcular_progresso(row, fases_ate_rtid), axis=1)
        rtid_publicados = len(df_rtid[df_rtid['publicação_DOU'] == 'Concluído'])
        progresso_rtid_meta = (rtid_publicados / META_RTID * 100) if META_RTID > 0 else 0
    else:
        rtid_publicados = 0
        progresso_rtid_meta = 0
    
    # Calcular progressos para Portaria
    if not df_portaria.empty:
        df_portaria['Progresso_Portaria'] = df_portaria.apply(lambda row: calcular_progresso(row, fases_portaria), axis=1)
        portarias_publicadas = len(df_portaria[
            (df_portaria['publicação_portaria_DOU'] == 'Concluído') | 
            (df_portaria['publicação_portaria_DOE'] == 'Concluído')
        ])
        progresso_portarias_meta = (portarias_publicadas / META_PORTARIAS * 100) if META_PORTARIAS > 0 else 0
    else:
        portarias_publicadas = 0
        progresso_portarias_meta = 0
    
    # Métricas
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("🎯 Meta RTID", f"{META_RTID}")
    with col2:
        st.metric("📄 RTID's Publicados", f"{rtid_publicados} / {META_RTID}")
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
    # FUNÇÃO PARA GRÁFICO RTID (COM NÃO INICIADOS)
    # ============================================
    
    def criar_grafico_rtid_com_nao_iniciados(df_meta, coluna_progresso, fases_meta, titulo):
        """
        Cria um gráfico de fases para RTID incluindo processos não iniciados
        """
        if df_meta.empty:
            st.info(f"ℹ️ Nenhum processo cadastrado para a meta RTID.")
            return None
        
        def encontrar_fase_por_progresso(row, fases_meta):
            ordem_fases = {fase: idx for idx, fase in enumerate(fases_meta)}
            fase_atual = "⏳ Não Iniciado"
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
        
        resultados = df_meta.apply(lambda row: encontrar_fase_por_progresso(row, fases_meta), axis=1)
        
        df_temp = df_meta.copy()
        df_temp['Fase Atual'] = [r[0] for r in resultados]
        df_temp['Ordem Fase'] = [r[1] for r in resultados]
        df_temp['Status Fase'] = [r[2] for r in resultados]
        
        # Criar dicionário de nomes amigáveis
        nomes_fases = {
            fase: fase.replace('_', ' ').title() 
            for fase in fases_meta
        }
        nomes_fases["⏳ Não Iniciado"] = "⏳ Não Iniciado"
        
        # Mapear fase atual para nome amigável
        def get_nome_amigavel(fase):
            if fase == "⏳ Não Iniciado":
                return "⏳ Não Iniciado"
            return nomes_fases.get(fase, fase)
        
        df_temp['Fase Atual Nome'] = df_temp['Fase Atual'].apply(get_nome_amigavel)
        
        # Status formatado
        def formatar_status(row):
            if row['Fase Atual'] == "⏳ Não Iniciado":
                return "⏳ Pendente"
            emojis = {
                'Concluído': '✅ Concluído',
                'Em Andamento': '🔄 Em Andamento',
                'Pendente': '⏳ Pendente',
                'Não Aplicável': '🚫 Não Aplicável'
            }
            return emojis.get(row['Status Fase'], f'❓ {row["Status Fase"]}')
        
        df_temp['Status Formatado'] = df_temp.apply(formatar_status, axis=1)
        
        # Ordenar: não iniciados primeiro, depois por ordem de fase
        df_temp['Ordem_Ordenacao'] = df_temp.apply(
            lambda row: -1 if row['Fase Atual'] == "⏳ Não Iniciado" else row['Ordem Fase'], 
            axis=1
        )
        df_temp_sorted = df_temp.sort_values('Ordem_Ordenacao', ascending=True)
        
        # Lista de todas as fases
        todas_fases_ordenadas = ["⏳ Não Iniciado"] + [nomes_fases[f] for f in fases_meta]
        
        # Hover customizado
        hover_custom = {
            'comunidade': True,
            'municipio': True,
            'Fase Atual Nome': True,
            'Status Formatado': True,
            coluna_progresso: ':.1f',
            'Ordem Fase': False,
            'Ordem_Ordenacao': False
        }
        
        # Criar gráfico
        fig = px.bar(
            df_temp_sorted,
            x='Ordem_Ordenacao',
            y='comunidade',
            orientation='h',
            color='Fase Atual Nome',
            color_discrete_sequence=px.colors.qualitative.Set1 + ['#808080'],
            title=titulo,
            hover_data=hover_custom,
            labels={
                'Ordem_Ordenacao': 'Fase do Processo',
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
            height=max(600, len(df_temp) * 35),
            showlegend=False,
            hoverlabel=dict(
                bgcolor="black",
                font_size=14,
                font_family="Arial",
                namelength=-1
            )
        )
        
        # Linha divisória para não iniciados
        fig.add_vline(x=-0.5, line_width=2, line_dash="dash", line_color="red", opacity=0.5)
        
        # Linhas entre fases
        for i in range(len(fases_meta)):
            if i > 0:
                fig.add_vline(x=i-0.5, line_width=1, line_dash="dash", line_color="gray", opacity=0.3)
        
        return fig
    
    # ============================================
    # FUNÇÃO PARA GRÁFICO PORTARIA (SEM NÃO INICIADOS)
    # ============================================
    
    def criar_grafico_portaria_sem_nao_iniciados(df_meta, coluna_progresso, fases_meta, titulo):
        """
        Cria um gráfico de fases para Portaria apenas com processos iniciados
        """
        if df_meta.empty:
            st.info(f"ℹ️ Nenhum processo cadastrado para a meta Portaria.")
            return None
        
        def encontrar_fase_por_progresso(row, fases_meta):
            ordem_fases = {fase: idx for idx, fase in enumerate(fases_meta)}
            fase_atual = None
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
            
            if fase_atual is None:
                return None, None, None
            
            return fase_atual, ordem_atual, status_atual
        
        resultados = df_meta.apply(lambda row: encontrar_fase_por_progresso(row, fases_meta), axis=1)
        
        # Filtrar apenas processos com fase iniciada
        mask = [r[0] is not None for r in resultados]
        df_temp = df_meta[mask].copy()
        resultados_filtrados = [r for r in resultados if r[0] is not None]
        
        if df_temp.empty:
            return None
        
        df_temp['Fase Atual'] = [r[0] for r in resultados_filtrados]
        df_temp['Ordem Fase'] = [r[1] for r in resultados_filtrados]
        df_temp['Status Fase'] = [r[2] for r in resultados_filtrados]
        
        # Nomes amigáveis
        nomes_fases = {
            fase: fase.replace('_', ' ').title() 
            for fase in fases_meta
        }
        
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
        
        # Lista de fases
        todas_fases_ordenadas = [nomes_fases[f] for f in fases_meta]
        
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
        tick_vals = [i for i in range(len(fases_meta))]
        tick_text = [nomes_fases[f] for f in fases_meta]
        
        fig.update_layout(
            xaxis=dict(
                title="Fase do Processo",
                tickmode='array',
                tickvals=tick_vals,
                ticktext=tick_text,
                tickangle=0,
                tickfont=dict(size=10),
                range=[-0.5, len(fases_meta) - 0.5]
            ),
            yaxis=dict(
                title="",
                tickfont=dict(size=14)
            ),
            height=max(400, len(df_temp) * 35),
            showlegend=False,
            hoverlabel=dict(
                bgcolor="black",
                font_size=14,
                font_family="Arial",
                namelength=-1
            )
        )
        
        # Linhas entre fases
        for i in range(len(tick_vals)):
            if i > 0:
                fig.add_vline(x=i-0.5, line_width=1, line_dash="dash", line_color="gray", opacity=0.3)
        
        return fig
    
    # ============================================
    # GRÁFICO RTID (COM NÃO INICIADOS)
    # ============================================
    st.subheader("📄 Meta RTID - Todos os Processos")
    
    if not df_rtid.empty:
        fig_rtid = criar_grafico_rtid_com_nao_iniciados(
            df_rtid, 
            'Progresso_RTID', 
            fases_ate_rtid, 
            "Fase Atual dos Processos RTID (todos os 8 processos)"
        )
        
        if fig_rtid:
            st.plotly_chart(fig_rtid, use_container_width=True)
            
            # Estatísticas
            total_rtid = len(df_rtid)
            rtid_iniciados = len(df_rtid[df_rtid['Progresso_RTID'] > 0])
            st.caption(f"📊 **Total:** {total_rtid} processos | 🟢 **Iniciados:** {rtid_iniciados} | ⏳ **Não iniciados:** {total_rtid - rtid_iniciados}")
    else:
        st.info("ℹ️ Nenhum processo RTID cadastrado.")
    
    st.divider()
    
    # ============================================
    # GRÁFICO PORTARIA (SEM NÃO INICIADOS)
    # ============================================
    st.subheader("📜 Meta Portaria - Apenas Processos Iniciados")
    
    if not df_portaria.empty:
        fig_portaria = criar_grafico_portaria_sem_nao_iniciados(
            df_portaria, 
            'Progresso_Portaria',
            fases_portaria,
            "Fase Atual dos Processos Portaria (apenas processos em andamento)"
        )
        
        if fig_portaria:
            st.plotly_chart(fig_portaria, use_container_width=True)
            
            # Estatísticas
            total_portaria = len(df_portaria)
            portaria_iniciados = len(df_portaria[df_portaria['Progresso_Portaria'] > 0])
            st.caption(f"📊 **Total:** {total_portaria} processos | 🟢 **Iniciados (exibidos):** {portaria_iniciados} | ⏳ **Não iniciados (ocultos):** {total_portaria - portaria_iniciados}")
        else:
            st.info(f"ℹ️ Existem {len(df_portaria)} processos cadastrados, mas nenhum foi iniciado ainda.")
    else:
        st.info("ℹ️ Nenhum processo Portaria cadastrado.")
    
    # Legenda explicativa
    st.divider()
    st.caption("""
    **ℹ️ Como interpretar os gráficos:**
    
    **📄 Meta RTID:**
    - Mostra **todos os 8 processos** da meta, incluindo os não iniciados
    - Processos não iniciados aparecem em **cinza** à esquerda da linha vermelha
    - Linha vermelha separa processos não iniciados dos iniciados
    
    **📜 Meta Portaria:**
    - Mostra **apenas processos que já iniciaram** alguma fase
    - Processos não iniciados são ocultados para focar nos que estão em andamento
    
    **Ordem do hover:**
    1. Comunidade
    2. Município
    3. Fase Atual
    4. Status da Fase
    5. Progresso (%)
    """)

# ============================================
# PÁGINA 2: GESTÃO RTID
# ============================================
elif page == "Gestão RTID":
    st.header("⚙️ Gestão de Processos RTID")
    
    # Aba para Adicionar Nova Comunidade RTID
    with st.expander("➕ Cadastrar Nova Comunidade RTID", expanded=False):
        with st.form("add_rtid_form"):
            novo_nome = st.text_input("Nome da Comunidade")
            novo_mun = st.text_input("Município")
            submit = st.form_submit_button("📌 Cadastrar")
            if submit and novo_nome:
                success, msg = add_rtid_community(novo_nome, novo_mun)
                if success:
                    st.success(msg)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
    
    if not df_rtid.empty:
        # Seleção da Comunidade
        if 'selected_rtid' not in st.session_state:
            st.session_state.selected_rtid = df_rtid['comunidade'].iloc[0]
        
        selected_comunidade = st.selectbox(
            "🔍 Selecione a Comunidade RTID para Editar:",
            df_rtid['comunidade'].unique(),
            index=list(df_rtid['comunidade'].unique()).index(st.session_state.selected_rtid) if st.session_state.selected_rtid in df_rtid['comunidade'].unique() else 0,
            key="rtid_selector"
        )
        st.session_state.selected_rtid = selected_comunidade
        
        # Recarregar dados
        df_rtid = carregar_dados_rtid()
        row = df_rtid[df_rtid['comunidade'] == selected_comunidade].iloc[0]
        
        # Editar Dados Básicos
        with st.expander("✏️ Editar Dados da Comunidade RTID", expanded=True):
            with st.form("edit_rtid_basic"):
                col1, col2 = st.columns(2)
                with col1:
                    nome_editado = st.text_input("Nome da Comunidade", value=row['comunidade'])
                with col2:
                    municipio_editado = st.text_input("Município", value=row['municipio'])
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    save_basic = st.form_submit_button("💾 Salvar Alterações")
                with col_btn2:
                    delete_btn = st.form_submit_button("🗑️ Excluir Comunidade")
                
                if save_basic:
                    if nome_editado != row['comunidade'] or municipio_editado != row['municipio']:
                        success, msg = update_rtid_community_info(selected_comunidade, nome_editado, municipio_editado)
                        if success:
                            st.success(msg)
                            st.cache_data.clear()
                            st.session_state.selected_rtid = nome_editado
                            st.rerun()
                        else:
                            st.error(msg)
                
                if delete_btn:
                    st.session_state.confirmar_exclusao_rtid = True
            
            # Confirmação de exclusão
            if st.session_state.get('confirmar_exclusao_rtid', False):
                st.warning(f"⚠️ **Tem certeza que deseja excluir '{selected_comunidade}'?**")
                col_conf1, col_conf2 = st.columns(2)
                with col_conf1:
                    if st.button("✅ Sim, excluir", key="conf_rtid_sim"):
                        success, msg = delete_rtid_community(selected_comunidade)
                        if success:
                            st.success(msg)
                            st.cache_data.clear()
                            st.session_state.confirmar_exclusao_rtid = False
                            if len(df_rtid) > 1:
                                novas = [c for c in df_rtid['comunidade'].unique() if c != selected_comunidade]
                                st.session_state.selected_rtid = novas[0]
                            st.rerun()
                        else:
                            st.error(msg)
                with col_conf2:
                    if st.button("❌ Cancelar", key="conf_rtid_nao"):
                        st.session_state.confirmar_exclusao_rtid = False
                        st.rerun()
        
        st.markdown(f"### Editando Fases RTID: **{row['comunidade']}**")
        
        # Editor de Fases RTID
        fases_por_categoria = {
            "Identificação e Delimitação": fases_ate_rtid[:10],
            "Publicação RTID": fases_ate_rtid[10:]
        }
        
        for categoria, lista_fases in fases_por_categoria.items():
            with st.expander(f"📋 {categoria}", expanded=True):
                cols = st.columns(2)
                for i, fase in enumerate(lista_fases):
                    with cols[i % 2]:
                        if fase in row.index:
                            status_atual = row[fase]
                            novo_status = st.selectbox(
                                f"📌 {fase.replace('_', ' ').title()}",
                                options=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"],
                                index=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"].index(status_atual),
                                key=f"rtid_{selected_comunidade}_{fase}"
                            )
                            if novo_status != status_atual:
                                success, msg = update_rtid_status(selected_comunidade, fase, novo_status)
                                if success:
                                    st.success(f"✅ Atualizado: {fase}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(msg)
        
        # Contestações
        st.divider()
        st.subheader("⚖️ Contestações")
        
        df_contestacoes = load_contestacoes(selected_comunidade)
        
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
                    
                    success, msg = add_contestacao(selected_comunidade, nome_req, data_notif_str, data_receb_str, data_edital_str, descricao)
                    if success:
                        st.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)
        
        if not df_contestacoes.empty:
            for _, row_contest in df_contestacoes.iterrows():
                with st.expander(f"📄 Contestação: {row_contest['nome_requerente']} ({row_contest['status']})"):
                    with st.form(f"edit_contest_{row_contest['id']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nome_edit = st.text_input("Nome", value=row_contest['nome_requerente'])
                            data_notif_edit = st.date_input("Data Notificação", value=pd.to_datetime(row_contest['data_notificacao']) if pd.notna(row_contest['data_notificacao']) else None)
                        with col2:
                            status_edit = st.selectbox("Status", ["Ativa", "Encerrada", "Improcedente", "Procedente"], 
                                                      index=["Ativa", "Encerrada", "Improcedente", "Procedente"].index(row_contest['status']))
                        
                        desc_edit = st.text_area("Descrição", value=row_contest['descricao'] if pd.notna(row_contest['descricao']) else "")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.form_submit_button("💾 Salvar"):
                                data_notif_str = data_notif_edit.strftime("%Y-%m-%d") if data_notif_edit else None
                                success, msg = update_contestacao(row_contest['id'], nome_edit, data_notif_str, None, None, desc_edit, status_edit)
                                if success:
                                    st.success(msg)
                                    st.cache_data.clear()
                                    st.rerun()
                        with col_btn2:
                            if st.form_submit_button("🗑️ Excluir"):
                                success, msg = delete_contestacao(row_contest['id'])
                                if success:
                                    st.success(msg)
                                    st.cache_data.clear()
                                    st.rerun()
    else:
        st.warning("⚠️ Nenhuma comunidade RTID encontrada. Cadastre uma nova comunidade para começar.")

# ============================================
# PÁGINA 3: GESTÃO PORTARIA
# ============================================
elif page == "Gestão Portaria":
    st.header("⚙️ Gestão de Processos Portaria")
    
    # Aba para Adicionar Nova Comunidade Portaria
    with st.expander("➕ Cadastrar Nova Comunidade Portaria", expanded=False):
        with st.form("add_portaria_form"):
            novo_nome = st.text_input("Nome da Comunidade")
            novo_mun = st.text_input("Município")
            submit = st.form_submit_button("📌 Cadastrar")
            if submit and novo_nome:
                success, msg = add_portaria_community(novo_nome, novo_mun)
                if success:
                    st.success(msg)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
    
    if not df_portaria.empty:
        # Seleção da Comunidade
        if 'selected_portaria' not in st.session_state:
            st.session_state.selected_portaria = df_portaria['comunidade'].iloc[0]
        
        selected_comunidade = st.selectbox(
            "🔍 Selecione a Comunidade Portaria para Editar:",
            df_portaria['comunidade'].unique(),
            index=list(df_portaria['comunidade'].unique()).index(st.session_state.selected_portaria) if st.session_state.selected_portaria in df_portaria['comunidade'].unique() else 0,
            key="portaria_selector"
        )
        st.session_state.selected_portaria = selected_comunidade
        
        # Recarregar dados
        df_portaria = carregar_dados_portaria()
        row = df_portaria[df_portaria['comunidade'] == selected_comunidade].iloc[0]
        
        # Editar Dados Básicos
        with st.expander("✏️ Editar Dados da Comunidade Portaria", expanded=True):
            with st.form("edit_portaria_basic"):
                col1, col2 = st.columns(2)
                with col1:
                    nome_editado = st.text_input("Nome da Comunidade", value=row['comunidade'])
                with col2:
                    municipio_editado = st.text_input("Município", value=row['municipio'])
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    save_basic = st.form_submit_button("💾 Salvar Alterações")
                with col_btn2:
                    delete_btn = st.form_submit_button("🗑️ Excluir Comunidade")
                
                if save_basic:
                    if nome_editado != row['comunidade'] or municipio_editado != row['municipio']:
                        success, msg = update_portaria_community_info(selected_comunidade, nome_editado, municipio_editado)
                        if success:
                            st.success(msg)
                            st.cache_data.clear()
                            st.session_state.selected_portaria = nome_editado
                            st.rerun()
                        else:
                            st.error(msg)
                
                if delete_btn:
                    st.session_state.confirmar_exclusao_portaria = True
            
            # Confirmação de exclusão
            if st.session_state.get('confirmar_exclusao_portaria', False):
                st.warning(f"⚠️ **Tem certeza que deseja excluir '{selected_comunidade}'?**")
                col_conf1, col_conf2 = st.columns(2)
                with col_conf1:
                    if st.button("✅ Sim, excluir", key="conf_portaria_sim"):
                        success, msg = delete_portaria_community(selected_comunidade)
                        if success:
                            st.success(msg)
                            st.cache_data.clear()
                            st.session_state.confirmar_exclusao_portaria = False
                            if len(df_portaria) > 1:
                                novas = [c for c in df_portaria['comunidade'].unique() if c != selected_comunidade]
                                st.session_state.selected_portaria = novas[0]
                            st.rerun()
                        else:
                            st.error(msg)
                with col_conf2:
                    if st.button("❌ Cancelar", key="conf_portaria_nao"):
                        st.session_state.confirmar_exclusao_portaria = False
                        st.rerun()
        
        st.markdown(f"### Editando Fases Portaria: **{row['comunidade']}**")
        
        # Editor de Fases Portaria
        with st.expander("📋 Fases da Portaria", expanded=True):
            cols = st.columns(2)
            for i, fase in enumerate(fases_portaria):
                with cols[i % 2]:
                    if fase in row.index:
                        status_atual = row[fase]
                        novo_status = st.selectbox(
                            f"📌 {fase.replace('_', ' ').title()}",
                            options=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"],
                            index=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"].index(status_atual),
                            key=f"portaria_{selected_comunidade}_{fase}"
                        )
                        if novo_status != status_atual:
                            success, msg = update_portaria_status(selected_comunidade, fase, novo_status)
                            if success:
                                st.success(f"✅ Atualizado: {fase}")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(msg)
    else:
        st.warning("⚠️ Nenhuma comunidade Portaria encontrada. Cadastre uma nova comunidade para começar.")

# ============================================
# PÁGINA 4: PROGRESSO INDIVIDUAL RTID
# ============================================
elif page == "Progresso Individual RTID":
    st.header("📈 Progresso Individual - Processos RTID")
    
    if not df_rtid.empty:
        selected = st.selectbox("🔍 Selecione a Comunidade:", df_rtid['comunidade'].unique())
        row = df_rtid[df_rtid['comunidade'] == selected].iloc[0]
        
        progresso = calcular_progresso(row, fases_ate_rtid)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏠 Comunidade", selected)
        with col2:
            st.metric("📍 Município", row['municipio'])
        with col3:
            st.metric("📊 Progresso RTID", f"{progresso:.1f}%")
        
        # Detalhamento das fases
        st.subheader("📋 Detalhamento das Fases RTID")
        
        dados_fases = []
        for fase in fases_ate_rtid:
            if fase in row.index:
                status = row[fase]
                emoji = {
                    'Concluído': '✅',
                    'Em Andamento': '🔄',
                    'Pendente': '⏳',
                    'Não Aplicável': '🚫'
                }.get(status, '❓')
                
                dados_fases.append({
                    'Fase': fase.replace('_', ' ').title(),
                    'Status': f"{emoji} {status}"
                })
        
        df_fases = pd.DataFrame(dados_fases)
        st.dataframe(df_fases, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Nenhum processo RTID cadastrado.")

# ============================================
# PÁGINA 5: PROGRESSO INDIVIDUAL PORTARIA
# ============================================
elif page == "Progresso Individual Portaria":
    st.header("📈 Progresso Individual - Processos Portaria")
    
    if not df_portaria.empty:
        selected = st.selectbox("🔍 Selecione a Comunidade:", df_portaria['comunidade'].unique())
        row = df_portaria[df_portaria['comunidade'] == selected].iloc[0]
        
        progresso = calcular_progresso(row, fases_portaria)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏠 Comunidade", selected)
        with col2:
            st.metric("📍 Município", row['municipio'])
        with col3:
            st.metric("📊 Progresso Portaria", f"{progresso:.1f}%")
        
        # Detalhamento das fases
        st.subheader("📋 Detalhamento das Fases Portaria")
        
        dados_fases = []
        for fase in fases_portaria:
            if fase in row.index:
                status = row[fase]
                emoji = {
                    'Concluído': '✅',
                    'Em Andamento': '🔄',
                    'Pendente': '⏳',
                    'Não Aplicável': '🚫'
                }.get(status, '❓')
                
                dados_fases.append({
                    'Fase': fase.replace('_', ' ').title(),
                    'Status': f"{emoji} {status}"
                })
        
        df_fases = pd.DataFrame(dados_fases)
        st.dataframe(df_fases, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Nenhum processo Portaria cadastrado.")