import sqlite3
import pandas as pd

DB_NAME = "processos_quilombolas.db"

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Definição das fases para processos RTID
    fases_rtid = [
        "notificação_aos_órgãos_e_entidades", "reunião_de_abertura", "comunicações_prévias", "relatório_antropológico",
        "cadastro_de_famílias", "levantamento_fundiário", "planta_memorial_descritivo", "análise_de_sobreposicão",
        "rtid_concluído", "reunião_de_validação_na_comunidade", 
        "ficha_resumo_do_RTID", "minuta_de_Edital", 
        "parecer_técnico_1", "parecer_jurídico_1", "análise_do_CDR", "autorização_da_diretoria_para_publicação", 
        "publicação_DOU", "publicação_DOE", "notificação_aos_órgãos_e_entidades_art_12", "notificação_aos_ocupantes", 
        "notificação_aos_confinantes", "prazo_de_contestação", "pareceres_técnicos", "pareceres_jurídicos", 
        "julgamento_da_contestação_no_CDR", "notificações_do_resultado_do_julgamento_do_CDR", "prazo_de_recurso", 
        "análise_de_recurso_na_DQ", "julgamento_do_recurso_no_CD", "notificações_do_resultado_do_julgamento_do_CD", 
        "parecer_análise_de_instrução_processual", "instrução_do_kit_portaria", "publicação_portaria_DOU", "publicação_portaria_DOE"
    ]

    # Criar tabela de processos RTID
    cols_rtid_sql = "id INTEGER PRIMARY KEY AUTOINCREMENT, comunidade TEXT UNIQUE, municipio TEXT, status_geral TEXT DEFAULT 'Em Andamento'"
    for fase in fases_rtid:
        cols_rtid_sql += f", {fase} TEXT DEFAULT 'Pendente'"

    query_rtid = f"""
    CREATE TABLE IF NOT EXISTS processos_rtid (
        {cols_rtid_sql}
    )
    """
    
    cursor.execute(query_rtid)
    
    # Definição das fases específicas para Portaria
    fases_portaria = [
        "parecer_análise_de_instrução_processual",
        "instrução_do_kit_portaria",
        "publicação_portaria_DOU",
        "publicação_portaria_DOE"
    ]
    
    # Criar tabela de processos Portaria
    cols_portaria_sql = "id INTEGER PRIMARY KEY AUTOINCREMENT, comunidade TEXT UNIQUE, municipio TEXT, status_geral TEXT DEFAULT 'Em Andamento'"
    for fase in fases_portaria:
        cols_portaria_sql += f", {fase} TEXT DEFAULT 'Pendente'"
    
    query_portaria = f"""
    CREATE TABLE IF NOT EXISTS processos_portaria (
        {cols_portaria_sql}
    )
    """
    
    cursor.execute(query_portaria)
    
    # Criar tabela de contestações (relacionada a processos_rtid)
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
        FOREIGN KEY (comunidade) REFERENCES processos_rtid(comunidade) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# ============================================
# FUNÇÕES PARA PROCESSOS RTID
# ============================================

def load_rtid_data():
    """Carrega os dados dos processos RTID."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM processos_rtid ORDER BY comunidade", conn)
    conn.close()
    return df

def update_rtid_status(comunidade, fase, novo_status):
    """Atualiza o status de uma fase específica em processos RTID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    status_validos = ["Pendente", "Em Andamento", "Concluído", "Não Aplicável"]
    if novo_status not in status_validos:
        conn.close()
        return False, f"Status inválido. Use um dos: {', '.join(status_validos)}"
    
    try:
        query = f"UPDATE processos_rtid SET {fase} = ? WHERE comunidade = ?"
        cursor.execute(query, (novo_status, comunidade))
        conn.commit()
        return True, "Status atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar: {e}"
    finally:
        conn.close()

def add_rtid_community(comunidade, municipio):
    """Adiciona uma nova comunidade na tabela RTID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO processos_rtid (comunidade, municipio) VALUES (?, ?)", (comunidade, municipio))
        conn.commit()
        return True, "✅ Comunidade RTID adicionada com sucesso!"
    except sqlite3.IntegrityError:
        return False, "❌ Erro: Comunidade já existe no banco."
    except Exception as e:
        return False, f"❌ Erro ao adicionar: {e}"
    finally:
        conn.close()

def update_rtid_community_info(comunidade_atual, novo_nome, novo_municipio):
    """Atualiza o nome e/ou município de uma comunidade RTID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        if novo_nome != comunidade_atual:
            cursor.execute("SELECT id FROM processos_rtid WHERE comunidade = ? AND comunidade != ?", (novo_nome, comunidade_atual))
            if cursor.fetchone():
                return False, "❌ Erro: Já existe outra comunidade com esse nome."
        
        cursor.execute(
            "UPDATE processos_rtid SET comunidade = ?, municipio = ? WHERE comunidade = ?",
            (novo_nome, novo_municipio, comunidade_atual)
        )
        conn.commit()
        return True, "✅ Dados atualizados com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao atualizar: {e}"
    finally:
        conn.close()

def delete_rtid_community(comunidade):
    """Remove uma comunidade RTID do banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM processos_rtid WHERE comunidade = ?", (comunidade,))
        conn.commit()
        return True, "✅ Comunidade RTID removida com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao remover: {e}"
    finally:
        conn.close()

# ============================================
# FUNÇÕES PARA PROCESSOS PORTARIA
# ============================================

def load_portaria_data():
    """Carrega os dados dos processos Portaria."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM processos_portaria ORDER BY comunidade", conn)
    conn.close()
    return df

def update_portaria_status(comunidade, fase, novo_status):
    """Atualiza o status de uma fase específica em processos Portaria."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    status_validos = ["Pendente", "Em Andamento", "Concluído", "Não Aplicável"]
    if novo_status not in status_validos:
        conn.close()
        return False, f"Status inválido. Use um dos: {', '.join(status_validos)}"
    
    try:
        query = f"UPDATE processos_portaria SET {fase} = ? WHERE comunidade = ?"
        cursor.execute(query, (novo_status, comunidade))
        conn.commit()
        return True, "Status atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar: {e}"
    finally:
        conn.close()

def add_portaria_community(comunidade, municipio):
    """Adiciona uma nova comunidade na tabela Portaria."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO processos_portaria (comunidade, municipio) VALUES (?, ?)", (comunidade, municipio))
        conn.commit()
        return True, "✅ Comunidade Portaria adicionada com sucesso!"
    except sqlite3.IntegrityError:
        return False, "❌ Erro: Comunidade já existe no banco."
    except Exception as e:
        return False, f"❌ Erro ao adicionar: {e}"
    finally:
        conn.close()

def update_portaria_community_info(comunidade_atual, novo_nome, novo_municipio):
    """Atualiza o nome e/ou município de uma comunidade Portaria."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        if novo_nome != comunidade_atual:
            cursor.execute("SELECT id FROM processos_portaria WHERE comunidade = ? AND comunidade != ?", (novo_nome, comunidade_atual))
            if cursor.fetchone():
                return False, "❌ Erro: Já existe outra comunidade com esse nome."
        
        cursor.execute(
            "UPDATE processos_portaria SET comunidade = ?, municipio = ? WHERE comunidade = ?",
            (novo_nome, novo_municipio, comunidade_atual)
        )
        conn.commit()
        return True, "✅ Dados atualizados com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao atualizar: {e}"
    finally:
        conn.close()

def delete_portaria_community(comunidade):
    """Remove uma comunidade Portaria do banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM processos_portaria WHERE comunidade = ?", (comunidade,))
        conn.commit()
        return True, "✅ Comunidade Portaria removida com sucesso!"
    except Exception as e:
        return False, f"❌ Erro ao remover: {e}"
    finally:
        conn.close()

# ============================================
# FUNÇÕES PARA CONTESTAÇÕES (mantidas para RTID)
# ============================================

def add_contestacao(comunidade, nome_requerente, data_notificacao, data_recebimento, data_edital, descricao):
    """Adiciona uma nova contestação."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM processos_rtid WHERE comunidade = ?", (comunidade,))
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