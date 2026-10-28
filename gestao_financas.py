#!/usr/bin/env python3
"""
Módulo de Gestão Financeira Familiar - Finanças Casa
Projetado para integração com o Guru (Hermes Agent) no Telegram.
Persistência local em SQLite com suporte a CLI e módulo Python.
"""

import sys
import os
import sqlite3
import argparse
import subprocess
import re
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any

DEFAULT_DB_PATH = os.environ.get("FINANCAS_DB_PATH", os.path.expanduser("~/.hermes/financas/financas.db"))

CATEGORIAS_PADRAO = [
    "Supermercado",
    "Alimentação",
    "Transporte",
    "Moradia",
    "Saúde",
    "Lazer",
    "Compras",
    "Educação",
    "Outros"
]

METODOS_PADRAO = [
    "Pix",
    "Crédito",
    "Débito",
    "Dinheiro",
    "Boleto"
]

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Garante a pasta e retorna a conexão com o banco SQLite."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Inicializa as tabelas do banco se não existirem."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            valor REAL NOT NULL,
            estabelecimento TEXT NOT NULL,
            categoria TEXT NOT NULL,
            metodo TEXT NOT NULL,
            responsavel TEXT NOT NULL,
            telegram_user_id INTEGER,
            descricao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gastos_data ON gastos(data)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gastos_responsavel ON gastos(responsavel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos(categoria)")
    conn.commit()
    conn.close()

def adicionar_gasto(
    valor: float,
    estabelecimento: str,
    categoria: str = "Outros",
    metodo: str = "Pix",
    responsavel: str = "Gabriel",
    data_gasto: Optional[str] = None,
    telegram_user_id: Optional[int] = None,
    descricao: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Registra uma nova despesa no banco."""
    init_db(db_path)
    
    if not data_gasto:
        data_gasto = date.today().isoformat()
        
    # Normalização de categoria
    cat_normalizada = "Outros"
    for c in CATEGORIAS_PADRAO:
        if c.lower() == categoria.strip().lower():
            cat_normalizada = c
            break
        elif c.lower() in categoria.strip().lower():
            cat_normalizada = c
            break

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO gastos (data, valor, estabelecimento, categoria, metodo, responsavel, telegram_user_id, descricao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_gasto,
        float(valor),
        estabelecimento.strip(),
        cat_normalizada,
        metodo.strip(),
        responsavel.strip(),
        telegram_user_id,
        descricao
    ))
    gasto_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": gasto_id,
        "data": data_gasto,
        "valor": float(valor),
        "estabelecimento": estabelecimento.strip(),
        "categoria": cat_normalizada,
        "metodo": metodo.strip(),
        "responsavel": responsavel.strip(),
        "telegram_user_id": telegram_user_id,
        "descricao": descricao
    }

def excluir_gasto(gasto_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Exclui um gasto pelo ID."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    removidos = cursor.rowcount
    conn.commit()
    conn.close()
    return removidos > 0

def listar_gastos(limite: int = 10, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retorna os últimos N lançamentos ordenados por data decrescente."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, data, valor, estabelecimento, categoria, metodo, responsavel, descricao, created_at
        FROM gastos
        ORDER BY data DESC, id DESC
        LIMIT ?
    """, (limite,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resumo_mensal(mes: Optional[int] = None, ano: Optional[int] = None, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Calcula o resumo financeiro de um determinado mês e ano."""
    init_db(db_path)
    hoje = date.today()
    mes = mes or hoje.month
    ano = ano or hoje.year
    
    prefixo = f"{ano:04d}-{mes:02d}"
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Total geral
    cursor.execute("SELECT COALESCE(SUM(valor), 0) as total, COUNT(*) as qtd FROM gastos WHERE data LIKE ?", (f"{prefixo}%",))
    res_geral = cursor.fetchone()
    total_geral = res_geral["total"]
    qtd_gastos = res_geral["qtd"]
    
    # Por responsável
    cursor.execute("""
        SELECT responsavel, COALESCE(SUM(valor), 0) as total, COUNT(*) as qtd
        FROM gastos
        WHERE data LIKE ?
        GROUP BY responsavel
        ORDER BY total DESC
    """, (f"{prefixo}%",))
    por_responsavel = {row["responsavel"]: {"total": row["total"], "qtd": row["qtd"]} for row in cursor.fetchall()}
    
    # Por categoria
    cursor.execute("""
        SELECT categoria, COALESCE(SUM(valor), 0) as total, COUNT(*) as qtd
        FROM gastos
        WHERE data LIKE ?
        GROUP BY categoria
        ORDER BY total DESC
    """, (f"{prefixo}%",))
    por_categoria = {row["categoria"]: {"total": row["total"], "qtd": row["qtd"]} for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "periodo": prefixo,
        "ano": ano,
        "mes": mes,
        "total_geral": total_geral,
        "quantidade": qtd_gastos,
        "por_responsavel": por_responsavel,
        "por_categoria": por_categoria
    }

def formatar_moeda(valor: float) -> str:
    """Formata valor em Real brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_relatorio_mes(resumo: Dict[str, Any]) -> str:
    """Gera texto amigável para envio pelo Telegram."""
    linhas = []
    mes_nome = datetime.strptime(resumo["periodo"], "%Y-%m").strftime("%B/%Y")
    linhas.append(f"📊 **Resumo de Gastos — {mes_nome.capitalize()}**")
    linhas.append(f"💰 **Total Geral:** {formatar_moeda(resumo['total_geral'])} ({resumo['quantidade']} lançamentos)\n")
    
    linhas.append("👥 **Por Responsável:**")
    if resumo["por_responsavel"]:
        for resp, dados in resumo["por_responsavel"].items():
            pct = (dados["total"] / resumo["total_geral"] * 100) if resumo["total_geral"] > 0 else 0
            linhas.append(f" • **{resp}:** {formatar_moeda(dados['total'])} ({pct:.1f}%)")
    else:
        linhas.append(" • Nenhum gasto registrado.")
        
    linhas.append("\n🏷️ **Por Categoria:**")
    if resumo["por_categoria"]:
        for cat, dados in resumo["por_categoria"].items():
            pct = (dados["total"] / resumo["total_geral"] * 100) if resumo["total_geral"] > 0 else 0
            linhas.append(f" • **{cat}:** {formatar_moeda(dados['total'])} ({pct:.1f}%)")
    else:
        linhas.append(" • Nenhuma categoria registrada.")
        
    return "\n".join(linhas)

def extrair_dados_pdf(pdf_path: str) -> Dict[str, Any]:
    """Extrai texto e metadados financeiros de um comprovante em PDF usando pdftotext."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
        
    try:
        proc = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, text=True, check=True)
        texto = proc.stdout
    except Exception:
        texto = ""

    dados = {
        "valor": None,
        "data": date.today().isoformat(),
        "local": "Desconhecido",
        "categoria": "Outros",
        "metodo": "Pix",
        "texto_extraido": texto[:1200]
    }
    
    # Regex de valor em Real (ex: R$ 150,00 ou Valor 150,00)
    match_valor = re.search(r'(?:R\$\s*|Valor[:\s]+R?\$?\s*)([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})', texto, re.IGNORECASE)
    if match_valor:
        val_str = match_valor.group(1).replace(".", "").replace(",", ".")
        try:
            dados["valor"] = float(val_str)
        except ValueError:
            pass
        
    # Regex data DD/MM/AAAA
    match_data = re.search(r'\b([0-3][0-9]/[0-1][0-9]/20[2-3][0-9])\b', texto)
    if match_data:
        d_str = match_data.group(1)
        try:
            dados["data"] = datetime.strptime(d_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            pass

    # Regex favorecido / recebedor / beneficiario
    match_fav = re.search(r'(?:Nome do recebedor|Recebedor|Benefici[aá]rio|Destinat[aá]rio|Para|Raz[aã]o Social|Estabelecimento)[:\s]+([^\n\r]+)', texto, re.IGNORECASE)
    if match_fav:
        local_limpo = match_fav.group(1).strip()
        # Remove caracteres indesejados
        local_limpo = re.sub(r'\s+', ' ', local_limpo)
        dados["local"] = local_limpo[:60]
        
    texto_lower = texto.lower()
    if "boleto" in texto_lower:
        dados["metodo"] = "Boleto"
        dados["categoria"] = "Moradia"
    elif "pix" in texto_lower:
        dados["metodo"] = "Pix"
    elif "cartao" in texto_lower or "cartão" in texto_lower:
        dados["metodo"] = "Crédito"
        
    if any(p in texto_lower for p in ["supermercado", "hipermercado", "atacadão", "atacado", "pão de açúcar", "carrefour", "extra"]):
        dados["categoria"] = "Supermercado"
    elif any(p in texto_lower for p in ["farmacia", "drogaria", "medicamento", "saude"]):
        dados["categoria"] = "Saúde"
    elif any(p in texto_lower for p in ["restaurante", "lanchonete", "ifood", "burger", "pizza", "padaria", "bar"]):
        dados["categoria"] = "Alimentação"
    elif any(p in texto_lower for p in ["posto", "combustivel", "gasolina", "uber", "estacionamento", "sem parar"]):
        dados["categoria"] = "Transporte"
    elif any(p in texto_lower for p in ["enel", "neoenergia", "caesb", "condominio", "aluguel", "internet", "claro", "vivo"]):
        dados["categoria"] = "Moradia"
        
    return dados

def main():
    parser = argparse.ArgumentParser(description="CLI de Gestão Financeira - Finanças Casa")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Adicionar
    p_add = subparsers.add_parser("add", help="Adicionar novo gasto")
    p_add.add_argument("--valor", type=float, required=True, help="Valor do gasto")
    p_add.add_argument("--local", required=True, help="Estabelecimento ou descrição")
    p_add.add_argument("--categoria", default="Outros", help="Categoria")
    p_add.add_argument("--metodo", default="Pix", help="Forma de pagamento (Pix, Cartão, etc.)")
    p_add.add_argument("--resp", default="Gabriel", help="Responsável pelo gasto (Gabriel / Esposa)")
    p_add.add_argument("--data", default=None, help="Data formato YYYY-MM-DD")
    p_add.add_argument("--desc", default=None, help="Observações adicionais")
    p_add.add_argument("--db", default=DEFAULT_DB_PATH, help="Caminho do banco")
    
    # Parse PDF
    p_pdf = subparsers.add_parser("parse_pdf", help="Extrair dados de comprovante PDF")
    p_pdf.add_argument("--file", required=True, help="Caminho do arquivo PDF")
    
    # Listar
    p_list = subparsers.add_parser("list", help="Listar últimos gastos")
    p_list.add_argument("--n", type=int, default=10, help="Quantidade de itens")
    p_list.add_argument("--db", default=DEFAULT_DB_PATH, help="Caminho do banco")
    
    # Resumo
    p_resumo = subparsers.add_parser("resumo", help="Resumo do mês")
    p_resumo.add_argument("--mes", type=int, default=None, help="Mês (1-12)")
    p_resumo.add_argument("--ano", type=int, default=None, help="Ano (ex: 2026)")
    p_resumo.add_argument("--db", default=DEFAULT_DB_PATH, help="Caminho do banco")
    
    # Excluir
    p_del = subparsers.add_parser("del", help="Excluir gasto por ID")
    p_del.add_argument("--id", type=int, required=True, help="ID do registro")
    p_del.add_argument("--db", default=DEFAULT_DB_PATH, help="Caminho do banco")

    args = parser.parse_args()
    
    if args.command == "add":
        gasto = adicionar_gasto(
            valor=args.valor,
            estabelecimento=args.local,
            categoria=args.categoria,
            metodo=args.metodo,
            responsavel=args.resp,
            data_gasto=args.data,
            descricao=args.desc,
            db_path=args.db
        )
        print(f"✅ Gasto #{gasto['id']} registrado: {formatar_moeda(gasto['valor'])} em {gasto['estabelecimento']} ({gasto['categoria']}) por {gasto['responsavel']}.")
        
    elif args.command == "parse_pdf":
        try:
            res = extrair_dados_pdf(args.file)
            print(json.dumps(res, ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            
    elif args.command == "list":
        itens = listar_gastos(limite=args.n, db_path=args.db)
        if not itens:
            print("Nenhum gasto registrado ainda.")
            return
        print(f"📋 Últimos {len(itens)} gastos:")
        for item in itens:
            print(f"#{item['id']} | {item['data']} | {formatar_moeda(item['valor'])} | {item['estabelecimento']} ({item['categoria']}) | {item['responsavel']} [{item['metodo']}]")
            
    elif args.command == "resumo":
        res = resumo_mensal(mes=args.mes, ano=args.ano, db_path=args.db)
        print(formatar_relatorio_mes(res))
        
    elif args.command == "del":
        sucesso = excluir_gasto(args.id, db_path=args.db)
        if sucesso:
            print(f"🗑️ Gasto #{args.id} excluído com sucesso.")
        else:
            print(f"❌ Gasto #{args.id} não encontrado.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
