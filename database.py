import sqlite3
import pandas as pd

DB_NAME = "processos_quilombolas.db"

def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Definição das fases (todas como TEXT para armazenar status: 'Pendente', 'Em Andamento', 'Concluído')
    fases = [
        "notificação_aos_órgãos_e_entidades", "reunião_de_abertura", "comunicações_prévias", "relatório_antropológico",
        "cadastro_famílias", "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",
        "rtid_concluído", "reunião_de_validação_na_comunidade", "ficha_resumo_do_RTID", "minuta_de_Edital", 
        "parecer_técnico_1", "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação", 
        "publicação_DOU", "publicação_DOE", "notificação_aos_órgãos_e_entidades_art_12", "notificação_aos_ocupantes", 
        "notificação_aos_confinantes", "prazo_de_contestação", "pareceres_técnicos", "pareceres_jurídicos", "julgamento_da_contestação_no_CDR", 
        "notificações_do_resultado_do_julgamento_do_CDR", "prazo_de_recurso", "análise_de_recurso_na_DQ", "julgamento_do_recurso_no_CD", 
        "notificações_do_resultado_do_julgamento_do_CD", "instrução_do_kit_portaria", "publicação_portaria_DOU", "publicação_portaria_DOE"
    ]

    # Construção da query SQL
    cols_sql = "id INTEGER PRIMARY KEY AUTOINCREMENT, comunidade TEXT UNIQUE, municipio TEXT, status_geral TEXT DEFAULT 'Parado'"
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
        FOREIGN KEY (comunidade) REFERENCES processos(comunidade)
    )
    """)
    conn.commit()
    conn.close()

def load_data():
    """Carrega os dados para o Pandas."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM processos", conn)
    conn.close()
    return df

def update_status(comunidade, fase, novo_status):
    """Atualiza o status de uma fase específica."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = f"UPDATE processos SET {fase} = ? WHERE comunidade = ?"
    cursor.execute(query, (novo_status, comunidade))
    
    conn.commit()
    conn.close()

def add_new_community(comunidade, municipio):
    """Adiciona uma nova comunidade."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO processos (comunidade, municipio) VALUES (?, ?)", (comunidade, municipio))
        conn.commit()
        return True, "Comunidade adicionada com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Erro: Comunidade já existe no banco."
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
                return False, "Erro: Já existe outra comunidade com esse nome."
        
        # Atualiza os dados
        cursor.execute(
            "UPDATE processos SET comunidade = ?, municipio = ? WHERE comunidade = ?",
            (novo_nome, novo_municipio, comunidade_atual)
        )
        conn.commit()
        return True, "Dados atualizados com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar: {e}"
    finally:
        conn.close()

def delete_community(comunidade):
    """Remove uma comunidade do banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM processos WHERE comunidade = ?", (comunidade,))
        conn.commit()
        return True, "Comunidade removida com sucesso!"
    except Exception as e:
        return False, f"Erro ao remover: {e}"
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
        cursor.execute("""
            INSERT INTO contestacoes 
            (comunidade, nome_requerente, data_notificacao, data_recebimento, data_edital_notificacao, descricao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (comunidade, nome_requerente, data_notificacao, data_recebimento, data_edital, descricao))
        conn.commit()
        return True, "Contestação cadastrada com sucesso!"
    except Exception as e:
        return False, f"Erro ao cadastrar: {e}"
    finally:
        conn.close()

def load_contestacoes(comunidade):
    """Carrega as contestações de uma comunidade específica."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT * FROM contestacoes WHERE comunidade = ? ORDER BY id DESC", 
        conn, params=(comunidade,)
    )
    conn.close()
    return df

def update_contestacao(contestacao_id, nome_requerente, data_notificacao, data_recebimento, data_edital, descricao, status):
    """Atualiza os dados de uma contestação."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE contestacoes 
            SET nome_requerente = ?, data_notificacao = ?, data_recebimento = ?, 
                data_edital_notificacao = ?, descricao = ?, status = ?
            WHERE id = ?
        """, (nome_requerente, data_notificacao, data_recebimento, data_edital, descricao, status, contestacao_id))
        conn.commit()
        return True, "Contestação atualizada!"
    except Exception as e:
        return False, f"Erro ao atualizar: {e}"
    finally:
        conn.close()

def delete_contestacao(contestacao_id):
    """Remove uma contestação."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM contestacoes WHERE id = ?", (contestacao_id,))
        conn.commit()
        return True, "Contestação removida!"
    except Exception as e:
        return False, f"Erro ao remover: {e}"
    finally:
        conn.close()
