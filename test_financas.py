#!/usr/bin/env python3
"""
Testes unitários para gestao_financas.py
"""

import os
import unittest
import tempfile
from gestao_financas import (
    init_db,
    adicionar_gasto,
    listar_gastos,
    resumo_mensal,
    excluir_gasto,
    formatar_moeda
)

class TestFinancas(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_financas.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_adicionar_e_listar_gastos(self):
        g1 = adicionar_gasto(
            valor=85.50,
            estabelecimento="Pão de Açúcar",
            categoria="Supermercado",
            metodo="Débito",
            responsavel="Gabriel",
            data_gasto="2026-09-15",
            db_path=self.db_path
        )
        self.assertIsNotNone(g1["id"])
        self.assertEqual(g1["valor"], 85.50)
        self.assertEqual(g1["categoria"], "Supermercado")
        
        g2 = adicionar_gasto(
            valor=42.00,
            estabelecimento="Drogaria Pacheco",
            categoria="Saúde",
            metodo="Pix",
            responsavel="Esposa",
            data_gasto="2026-09-15",
            db_path=self.db_path
        )
        self.assertIsNotNone(g2["id"])
        
        lista = listar_gastos(limite=5, db_path=self.db_path)
        self.assertEqual(len(lista), 2)
        self.assertEqual(lista[0]["id"], g2["id"])

    def test_resumo_mensal(self):
        adicionar_gasto(valor=100.0, estabelecimento="Mercado A", categoria="Supermercado", responsavel="Gabriel", data_gasto="2026-09-10", db_path=self.db_path)
        adicionar_gasto(valor=50.0, estabelecimento="Uber", categoria="Transporte", responsavel="Gabriel", data_gasto="2026-09-11", db_path=self.db_path)
        adicionar_gasto(valor=75.0, estabelecimento="Farmácia", categoria="Saúde", responsavel="Esposa", data_gasto="2026-09-12", db_path=self.db_path)
        
        resumo = resumo_mensal(mes=9, ano=2026, db_path=self.db_path)
        self.assertEqual(resumo["total_geral"], 225.0)
        self.assertEqual(resumo["quantidade"], 3)
        self.assertEqual(resumo["por_responsavel"]["Gabriel"]["total"], 150.0)
        self.assertEqual(resumo["por_responsavel"]["Esposa"]["total"], 75.0)
        self.assertEqual(resumo["por_categoria"]["Supermercado"]["total"], 100.0)

    def test_excluir_gasto(self):
        g = adicionar_gasto(valor=30.0, estabelecimento="Padaria", db_path=self.db_path)
        g_id = g["id"]
        self.assertTrue(excluir_gasto(g_id, db_path=self.db_path))
        self.assertFalse(excluir_gasto(g_id, db_path=self.db_path))
        lista = listar_gastos(db_path=self.db_path)
        self.assertEqual(len(lista), 0)

    def test_formatar_moeda(self):
        self.assertEqual(formatar_moeda(1250.5), "R$ 1.250,50")

if __name__ == "__main__":
    unittest.main()
