import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import init_db, load_data, update_status, add_new_community

# Configuração da Página
st.set_page_config(page_title="Dashboard Quilombolas MA", layout="wide")

# Inicialização do DB
init_db()

# --- TÍTULO E SIDEBAR ---
st.title("🛡️ Sistema de Acompanhamento: Regularização Quilombola MA")
st.markdown("Controle o andamento dos processos de titulação das comunidades.")

st.sidebar.header("Navegação")
page = st.sidebar.radio("Ir para:", ["Dashboard Geral", "Gestão de Processos"])

# Carregar dados
df = load_data()

# --- FUNÇÕES AUXILIARES ---
def calcular_progresso(row):
    """Calcula a porcentagem de fases concluídas."""
    fases = [col for col in df.columns if col not in ['id', 'comunidade', 'municipio', 'status_geral']]
    total = len(fases)
    concluidas = sum(1 for fase in fases if row[fase] == 'Concluído')
    return (concluidas / total) * 100 if total > 0 else 0

# --- PÁGINA 1: DASHBOARD ---
if page == "Dashboard Geral":
    st.header("Visão Geral dos Processos")

    if not df.empty:
        # Calcular progresso para todos
        df['Progresso'] = df.apply(calcular_progresso, axis=1)

        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Comunidades", len(df))
        col2.metric("Média de Progresso", f"{df['Progresso'].mean():.1f}%")
        col3.metric("Processos Concluídos (>90%)", len(df[df['Progresso'] > 90]))

        st.divider()

        # Gráfico 1: Barra de Progresso por Comunidade
        st.subheader("Andamento por Comunidade")
        df_sorted = df.sort_values('Progresso', ascending=False)
        
        fig_bar = px.bar(
            df_sorted, 
            x='Progresso', 
            y='comunidade', 
            color='Progresso',
            color_continuous_scale='RdYlGn',
            range_x=[0, 100],
            title="Progresso da Regularização",
            hover_data=['municipio']
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Gráfico 2: Mapa de Calor das Fases
        st.subheader("Mapa de Calor das Etapas")
        # Preparar dados para heatmap (Pivot longo)
        fases_cols = [col for col in df.columns if col not in ['id', 'comunidade', 'municipio', 'status_geral', 'Progresso']]
        
        # Simplificando para visualização: Contagem de status por fase
        status_counts = {}
        for fase in fases_cols:
            status_counts[fase] = df[fase].value_counts().to_dict()
        
        # Criar DataFrame para heatmap
        heatmap_data = pd.DataFrame(status_counts).T.fillna(0)
        
        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(x="Fase do Processo", y="Status", color="Quantidade"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale="Blues",
            aspect="auto"
        )
        fig_heat.update_layout(height=600)
        st.plotly_chart(fig_heat, use_container_width=True)

    else:
        st.info("Nenhuma comunidade cadastrada ainda. Vá para a aba 'Gestão de Processos' para adicionar.")

# --- PÁGINA 2: GESTÃO DE PROCESSOS ---
elif page == "Gestão de Processos":
    st.header("Gestão e Edição de Processos")
    
    # Aba para Adicionar Nova Comunidade
    with st.expander("➕ Cadastrar Nova Comunidade", expanded=False):
        with st.form("add_form"):
            novo_nome = st.text_input("Nome da Comunidade")
            novo_mun = st.text_input("Município")
            submit = st.form_submit_button("Cadastrar")
            if submit and novo_nome:
                success, msg = add_new_community(novo_nome, novo_mun)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    if not df.empty:
        # Seleção da Comunidade para Editar
        selected_comunidade = st.selectbox("Selecione a Comunidade para Editar:", df['comunidade'].unique())
        
        # Filtrar dados da comunidade selecionada
        row = df[df['comunidade'] == selected_comunidade].iloc[0]
        
        st.markdown(f"### Editando: **{row['comunidade']}** ({row['municipio']})")
        
        # Agrupamento de Fases para facilitar a visualização (Tabs)
        tab1, tab2, tab3, tab4 = st.tabs(["Fase de Identificação e Delimitação", "Fase de Publicação RTID", "Fase Contenciosa", "Fase Final"])

        # Mapeamento das fases para as abas (Tabs)
        fases_aba1 = ["comunicacao_aos_orgaos_e_entidades", "reunião_de_abertura", "notificações_prévias", "relatorio_antropologico", "cadastro_familias", "levantamento_fundiario", "planta_memorial_descritivo", "analise_sobreposicao", "rtid_concluido", "reuniao_de_validacao_RTID_na_comunidade"]
        fases_aba2 = ["parecer_técnico_1", "parecer_jurídico_1", "análise_CDR", "autorização_da_diretoria_para_publicação", "ficha_resumo_RTID", "publicação_DOU", "publicação_DOE", "notificação_aos_incidentes", "notificação_aos_confrontantes", "prazo_de_contestacao"]
        fases_aba3 = ["parecer_técnico_2", "parecer_jurídico_2", "julgamento_CD", "notificações_do_resultado_da_análise_CD", "prazo_recurso", "analise_recurso_dq", "julgamento_conselho_diretor", "notificacoes_resultado_conselho"]
        fases_aba4 = ["instrucao_kit_portaria", "kit_portaria_instruido", "publicacao_dou_final", "publicacao_doe_final"]

        def criar_formulario_edicao(abas, lista_fases):
            with abas:
                for fase in lista_fases:
                    # Pega o status atual do banco
                    status_atual = row[fase]
                    
                    # Cria o selectbox
                    novo_status = st.selectbox(
                        f"🟢 {fase.replace('_', ' ').title()}", 
                        options=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"],
                        index=["Pendente", "Em Andamento", "Concluído", "Não Aplicável"].index(status_atual)
                    )
                    
                    # Se mudou, atualiza no banco
                    if novo_status != status_atual:
                        update_status(selected_comunidade, fase, novo_status)
                        st.success(f"Atualizado: {fase}")
                        # Opcional: st.rerun() para atualizar dados em tempo real, mas pode ser lento

        criar_formulario_edicao(tab1, fases_aba1)
        criar_formulario_edicao(tab2, fases_aba2)
        criar_formulario_edicao(tab3, fases_aba3)
        criar_formulario_edicao(tab4, fases_aba4)

    else:
        st.warning("Nenhuma comunidade encontrada.")
