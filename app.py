import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import init_db, load_data, update_status, add_new_community, update_community_info, delete_community, add_contestacao, load_contestacoes, update_contestacao, delete_contestacao

# Configuração da Página
st.set_page_config(page_title="Dashboard Quilombolas MA", layout="wide")

# Inicialização do DB
init_db()

# --- TÍTULO E SIDEBAR ---
st.title("🛡️ Acompanhamento de Metas: Publicação de RTID's")
st.markdown("Controle de andamento processos")

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
    st.header("Visão Geral")

    if not df.empty:
        # Calcular progresso para todos
        df['Progresso'] = df.apply(calcular_progresso, axis=1)

        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Meta - 2026", len(df), "RTID's")
        col2.metric("Média de Progresso", f"{df['Progresso'].mean():.1f}%")
        col3.metric("RTID's Publicados (>90%)", len(df[df['Progresso'] > 90]))

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

        # Gráfico 2: Progresso de Cada Processo por Fase
        st.subheader("Progresso de Cada Processo por Fase")

        # Definir fases antes de usar
        fases = [col for col in df.columns if col not in ['id', 'comunidade', 'municipio', 'status_geral', 'Progresso']]

        # Função para encontrar a fase mais avançada de cada comunidade
        def encontrar_fase_atual(row):
            """Encontra a fase mais avançada (última fase com status diferente de 'Pendente')."""
            ordem_fases = {fase: idx for idx, fase in enumerate(fases)}
            
            fase_atual = "Não Iniciado"
            fase_atual_ordem = -1
            
            for fase in fases:
                status = row[fase]
                # Considera qualquer status que não seja 'Pendente' como avançado
                if status != 'Pendente':
                    if ordem_fases[fase] > fase_atual_ordem:
                        fase_atual = fase
                        fase_atual_ordem = ordem_fases[fase]
            
            return fase_atual, fase_atual_ordem

        # Aplicar função para encontrar fase atual
        df['Fase Atual'], df['Ordem Fase'] = zip(*df.apply(encontrar_fase_atual, axis=1))

        # Ordenar por ordem da fase (mais avançada primeiro)
        df_sorted = df.sort_values('Ordem Fase', ascending=False)

        # Criar gráfico de barras horizontais (UMA BARRA POR COMUNIDADE)
        fig_fase_atual = px.bar(
            df_sorted,
            x='Ordem Fase',
            y='comunidade',
            orientation='h',
            color='Ordem Fase',
            color_continuous_scale='Blues',
            range_x=[-1, len(fases)],
            title="Progresso de Cada Processo por Fase",
            hover_data={
                'comunidade': True,
                'municipio': True,
                'Fase Atual': True,
                'Ordem Fase': False
            }
        )

        fig_fase_atual.update_layout(
            xaxis_title="Fase Atual (Ordem)",
            yaxis_title="Comunidade",
            height=600,
            showlegend=False
        )

        st.plotly_chart(fig_fase_atual, use_container_width=True)

        # Tabela com fase atual de cada comunidade
        st.subheader("Resumo da Fase Atual")

        # Criar DataFrame de resumo a partir do df já ordenado
        df_resumo = df[['comunidade', 'municipio', 'Fase Atual', 'Progresso', 'Ordem Fase']].copy()

        # Formatar para exibição
        df_resumo['Fase Atual'] = df_resumo['Fase Atual'].apply(lambda x: x.replace('_', ' ').title())

        st.dataframe(
            df_resumo,
            use_container_width=True,
            hide_index=True
        )

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
        
        # Recarregar dados para garantir dados atualizados
        df = load_data()
        
        # Filtrar dados da comunidade selecionada
        row = df[df['comunidade'] == selected_comunidade].iloc[0]
        
        # ============================================
        # SEÇÃO 1: EDITAR DADOS BÁSICOS DA COMUNIDADE
        # ============================================
        with st.expander("✏️ Editar Dados da Comunidade", expanded=True):
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
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    save_basic = st.form_submit_button("💾 Salvar Alterações")
                with col_btn2:
                    delete_btn = st.form_submit_button("🗑️ Excluir Comunidade")
                
                if save_basic:
                    if nome_editado != row['comunidade'] or municipio_editado != row['municipio']:
                        success, msg = update_community_info(selected_comunidade, nome_editado, municipio_editado)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                
                if delete_btn:
                    # Confirmação antes de excluir
                    confirm = st.warning(f"⚠️ Tem certeza que deseja excluir '{selected_comunidade}'? Esta ação não pode ser desfeita.")
                    if st.checkbox("Confirmar exclusão"):
                        success, msg = delete_community(selected_comunidade)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        
        # Atualiza o nome selecionado se houve alteração
        if nome_editado != selected_comunidade:
            selected_comunidade = nome_editado
            row = df[df['comunidade'] == selected_comunidade].iloc[0]
        
        st.markdown(f"### Editando Fases: **{row['comunidade']}** ({row['municipio']})")
        
        # ============================================
        # SEÇÃO 2: EDITAR FASES DO PROCESSO
        # ============================================
        
        # Agrupamento de Fases para facilitar a visualização (Tabs)
        tab1, tab2, tab3, tab4 = st.tabs(["Fase de Identificação e Delimitação", "Fase de Publicação RTID", "Fase Contenciosa", "Fase Final"])

        # Mapeamento das fases para as abas (Tabs)
        fases_aba1 = ["comunicacao_aos_orgaos_e_entidades", "reunião_de_abertura", "notificações_prévias", "relatorio_antropologico", "cadastro_familias", "levantamento_fundiario", "planta_memorial_descritivo", "analise_sobreposicao", "rtid_concluido", "reuniao_de_validacao_RTID_na_comunidade"]
        fases_aba2 = ["parecer_técnico_1", "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação", "ficha_resumo_RTID", "publicação_DOU", "publicação_DOE", "notificação_aos_incidentes", "notificação_aos_confrontantes"]
        fases_aba3 = ["prazo_de_contestacao", "parecer_técnico_2", "parecer_jurídico_2", "julgamento_CD", "notificações_do_resultado_da_análise_CD", "prazo_recurso", "analise_recurso_dq", "julgamento_conselho_diretor", "notificacoes_resultado_conselho"]
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

        criar_formulario_edicao(tab1, fases_aba1)
        criar_formulario_edicao(tab2, fases_aba2)
        criar_formulario_edicao(tab3, fases_aba3)
        criar_formulario_edicao(tab4, fases_aba4)

   

        # ============================================
        # SEÇÃO 3: CADASTRO DE CONTESTAÇÕES
        # ============================================
        st.divider()
        st.subheader("📜 Contestações")
        
        # Carregar contestações da comunidade selecionada
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
                
                submit_contest = st.form_submit_button("Cadastrar Contestação")
                
                if submit_contest and nome_req:
                    # Converter datas para string ISO
                    data_notif_str = data_notif.strftime("%Y-%m-%d") if data_notif else None
                    data_receb_str = data_receb.strftime("%Y-%m-%d") if data_receb else None
                    data_edital_str = data_edital.strftime("%Y-%m-%d") if data_edital else None
                    
                    success, msg = add_contestacao(
                        selected_comunidade, nome_req, data_notif_str, 
                        data_receb_str, data_edital_str, descricao
                    )
                    if success:
                        st.success(msg)
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
                            data_notif_edit = st.date_input("Data da Notificação", value=pd.to_datetime(row_contest['data_notificacao']) if pd.notna(row_contest['data_notificacao']) else None)
                            data_receb_edit = st.date_input("Data do Recebimento", value=pd.to_datetime(row_contest['data_recebimento']) if pd.notna(row_contest['data_recebimento']) else None)
                        with col2:
                            data_edital_edit = st.date_input("Data do Edital de Notificação", value=pd.to_datetime(row_contest['data_edital_notificacao']) if pd.notna(row_contest['data_edital_notificacao']) else None)
                            status_edit = st.selectbox("Status", ["Ativa", "Encerrada", "Improcedente", "Procedente"], index=["Ativa", "Encerrada", "Improcedente", "Procedente"].index(row_contest['status']))
                        
                        desc_edit = st.text_area("Descrição/Observações", value=row_contest['descricao'] if pd.notna(row_contest['descricao']) else "")
                        
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
                                st.rerun()
                            else:
                                st.error(msg)
                        
                        if del_contest:
                            confirm_del = st.checkbox(f"Confirmar exclusão da contestação #{row_contest['id']}?")
                            if confirm_del:
                                success, msg = delete_contestacao(row_contest['id'])
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
        else:
            st.info("Nenhuma contestação cadastrada para esta comunidade.")
    else:
        st.warning("Nenhuma comunidade encontrada.")