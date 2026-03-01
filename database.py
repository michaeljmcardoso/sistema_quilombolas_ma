import sqlite3
import pandas as pd

DB_NAME = "processos_quilombolas.db"

def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Definição das colunas base
    colunas = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("comunidade", "TEXT UNIQUE"), # Unique para evitar duplicatas de nome
        ("municipio", "TEXT"),
        ("status_geral", "TEXT DEFAULT 'Parado'")
    ]

    # Definição das fases (todas como TEXT para armazenar status: 'Pendente', 'Em Andamento', 'Concluído')
    fases = [
        "comunicacao_aos_orgaos_e_entidades", "reunião_de_abertura", "notificações_prévias", "relatorio_antropologico",
        "cadastro_familias", "levantamento_fundiario", "planta_memorial_descritivo", "analise_sobreposicao",
        "rtid_concluido", "reuniao_de_validacao_RTID_na_comunidade", 
        "parecer_técnico_1", "parecer_jurídico_1", "análise_CDR", "autorização_da_diretoria_para_publicação", "ficha_resumo_RTID",
        "publicação_DOU", "publicação_DOE", "notificação_aos_incidentes", "notificação_aos_confrontantes", "prazo_de_contestacao", 
        "parecer_técnico_2", "parecer_jurídico_2", "julgamento_CD", "notificações_do_resultado_da_análise_CD",
        "prazo_recurso", "analise_recurso_dq", "julgamento_conselho_diretor", "notificacoes_resultado_conselho" 
        "julgamento_conselho_diretor", "notificacoes_resultado_conselho", 
        "instrucao_kit_portaria", "kit_portaria_instruido", "publicacao_dou_final", "publicacao_doe_final"
    ]

    # Construção da query SQL
    cols_sql = ", ".join([f"{nome} {tipo}" for nome, tipo in colunas])
    for fase in fases:
        cols_sql += f", {fase} TEXT DEFAULT 'Pendente'"

    query = f"""
    CREATE TABLE IF NOT EXISTS processos (
        {cols_sql}
    )
    """
    
    cursor.execute(query)
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
