import sqlite3
import pandas as pd

DB_NAME = "processos_quilombolas.db"

def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Definição das fases (todas como TEXT para armazenar status: 'Pendente', 'Em Andamento', 'Concluído', 'Não Aplicável')
    fases = [
        # Fase de Identificação e Delimitação
        "notificação_aos_órgãos_e_entidades", "reunião_de_abertura", "comunicações_prévias", "relatório_antropológico",
        "cadastro_de_famílias", "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",  # CORRIGIDO: sobreposicão -> sobreposição
        "rtid_concluído", "reunião_de_validação_na_comunidade", 
        
        # Fase de Publicação RTID
        "ficha_resumo_do_RTID", "minuta_de_Edital", 
        "parecer_técnico_1", "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação", 
        "publicação_DOU", "publicação_DOE", "notificação_aos_órgãos_e_entidades_art_12", "notificação_aos_ocupantes", 
        "notificação_aos_confinantes", 
        
        # Fase Contenciosa
        "prazo_de_contestação", "pareceres_técnicos", "pareceres_jurídicos", "julgamento_da_contestação_no_CDR", 
        "notificações_do_resultado_do_julgamento_do_CDR", "prazo_de_recurso", "análise_de_recurso_na_DQ", "julgamento_do_recurso_no_CD", 
        "notificações_do_resultado_do_julgamento_do_CD", 
        
        # Fase Portaria de Reconhecimento
        "parecer_análise_de_instrução_processual", "instrução_do_kit_portaria", "publicação_portaria_DOU", "publicação_portaria_DOE"
    ]

    # Construção da query SQL
    cols_sql = "id INTEGER PRIMARY KEY AUTOINCREMENT, comunidade TEXT UNIQUE, municipio TEXT, status_geral TEXT DEFAULT 'Em Andamento'"
    for fase in fases:
        cols_sql += f", {fase} TEXT DEFAULT 'Pendente'"

    query = f"""
    CREATE TABLE IF NOT EXISTS processos (
        {cols_sql}
    )
    """
    
    cursor.execute(query)
    conn.commit()
    
    # Criar tabela de contestações (separadamente para evitar erros)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contestacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comunidade TEXT NOT NULL,
        nome_requerente TEXT NOT NULL,
        data_notificacao TEXT,
        data_recebimento TEXT,
        data_edital_notificacao TEXT,
        descricao TEXT,
        status TEXT DEFAULT 'Ativa',
        FOREIGN KEY (comunidade) REFERENCES processos(comunidade) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

def load_data():
    """Carrega os dados para o Pandas."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM processos ORDER BY comunidade", conn)
    conn.close()
    return df

def update_status(comunidade, fase, novo_status):
    """Atualiza o status de uma fase específica."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Validar se o status é permitido
    status_validos = ["Pendente", "Em Andamento", "Concluído", "Não Aplicável"]
    if novo_status not in status_validos:
        conn.close()
        return False, f"Status inválido. Use um dos: {', '.join(status_validos)}"
    
    try:
        query = f"UPDATE processos SET {fase} = ? WHERE comunidade = ?"
        cursor.execute(query, (novo_status, comunidade))
        conn.commit()
        return True, "Status atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar: {e}"
    finally:
        conn.close()

def add_new_community(comunidade, municipio):
    """Adiciona uma nova comunidade."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO processos (comunidade, municipio) VALUES (?, ?)", (comunidade, municipio))
        conn.commit()
        return True, "✅ Comunidade adicionada com sucesso!"
    except sqlite3.IntegrityError:
        return False, "❌ Erro: Comunidade já existe no banco."
    except Exception as e:
        return False, f"❌ Erro ao adicionar: {e}"
    finally:
        conn.close()

def update_community_info(comunidade_atual, novo_nome, novo_municipio):
    """Atualiza o nome e/ou município de uma comunidade."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Verificar se o novo nome já existe (se for diferente do atual)
        if novo_nome != comunidade_atual:
            cursor.execute("SELECT id FROM processos WHERE comunidade = ? AND comunidade != ?", (novo_nome, comunidade_atual))
            if cursor.fetchone():
                return False, "❌ Erro: Já existe outra comunidade com esse nome."
        
        # Atualiza os dados
        cursor.execute(
            "UPDATE processos SET comunidade = ?, municipio = ? WHERE comunidade = ?",
            (novo_nome, novo_municipio, comunidade_atual)
        )
        conn.commit()
        return True, "✅ Dados atualizados com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao atualizar: {e}"
    finally:
        conn.close()

def delete_community(comunidade):
    """Remove uma comunidade do banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # As contestações serão removidas automaticamente devido ao ON DELETE CASCADE
        cursor.execute("DELETE FROM processos WHERE comunidade = ?", (comunidade,))
        conn.commit()
        return True, "✅ Comunidade removida com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao remover: {e}"
    finally:
        conn.close()

# ============================================
# FUNÇÕES PARA CONTESTAÇÕES
# ============================================

def add_contestacao(comunidade, nome_requerente, data_notificacao, data_recebimento, data_edital, descricao):
    """Adiciona uma nova contestação."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Verificar se a comunidade existe
        cursor.execute("SELECT id FROM processos WHERE comunidade = ?", (comunidade,))
        if not cursor.fetchone():
            return False, "❌ Erro: Comunidade não encontrada."
        
        cursor.execute("""
            INSERT INTO contestacoes 
            (comunidade, nome_requerente, data_notificacao, data_recebimento, data_edital_notificacao, descricao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (comunidade, nome_requerente, data_notificacao, data_recebimento, data_edital, descricao))
        conn.commit()
        return True, "✅ Contestação cadastrada com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao cadastrar: {e}"
    finally:
        conn.close()

def load_contestacoes(comunidade=None):
    """Carrega as contestações. Se comunidade for None, carrega todas."""
    conn = sqlite3.connect(DB_NAME)
    if comunidade:
        df = pd.read_sql_query(
            "SELECT * FROM contestacoes WHERE comunidade = ? ORDER BY id DESC", 
            conn, params=(comunidade,)
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM contestacoes ORDER BY comunidade, id DESC", 
            conn
        )
    conn.close()
    return df

def update_contestacao(contestacao_id, nome_requerente, data_notificacao, data_recebimento, data_edital, descricao, status):
    """Atualiza os dados de uma contestação."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Validar status
    status_validos = ["Ativa", "Encerrada", "Improcedente", "Procedente"]
    if status not in status_validos:
        conn.close()
        return False, f"❌ Status inválido. Use um dos: {', '.join(status_validos)}"
    
    try:
        cursor.execute("""
            UPDATE contestacoes 
            SET nome_requerente = ?, data_notificacao = ?, data_recebimento = ?, 
                data_edital_notificacao = ?, descricao = ?, status = ?
            WHERE id = ?
        """, (nome_requerente, data_notificacao, data_recebimento, data_edital, descricao, status, contestacao_id))
        conn.commit()
        return True, "✅ Contestação atualizada!"
    except Exception as e:
        return False, f"❌ Erro ao atualizar: {e}"
    finally:
        conn.close()

def delete_contestacao(contestacao_id):
    """Remove uma contestação."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM contestacoes WHERE id = ?", (contestacao_id,))
        conn.commit()
        return True, "✅ Contestação removida!"
    except Exception as e:
        return False, f"❌ Erro ao remover: {e}"
    finally:
        conn.close()

def get_comunidade_stats(comunidade):
    """Retorna estatísticas de uma comunidade específica."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Buscar dados da comunidade
        cursor.execute("SELECT * FROM processos WHERE comunidade = ?", (comunidade,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Buscar contestações
        cursor.execute("SELECT COUNT(*) FROM contestacoes WHERE comunidade = ?", (comunidade,))
        num_contestacoes = cursor.fetchone()[0]
        
        # Calcular progresso
        colunas = [description[0] for description in cursor.description]
        fases = [col for col in colunas if col not in ['id', 'comunidade', 'municipio', 'status_geral']]
        
        cursor.execute(f"SELECT {', '.join(fases)} FROM processos WHERE comunidade = ?", (comunidade,))
        status_fases = cursor.fetchone()
        
        total_fases = len(fases)
        concluidas = sum(1 for status in status_fases if status == 'Concluído')
        progresso = (concluidas / total_fases * 100) if total_fases > 0 else 0
        
        return {
            'comunidade': comunidade,
            'num_contestacoes': num_contestacoes,
            'progresso': progresso,
            'total_fases': total_fases,
            'fases_concluidas': concluidas
        }
    except Exception as e:
        return None
    finally:
        conn.close()

def get_all_stats():
    """Retorna estatísticas de todas as comunidades."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT comunidade FROM processos ORDER BY comunidade", conn)
    conn.close()
    
    stats = []
    for comunidade in df['comunidade']:
        stat = get_comunidade_stats(comunidade)
        if stat:
            stats.append(stat)
    
    return pd.DataFrame(stats)