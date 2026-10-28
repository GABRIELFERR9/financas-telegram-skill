---
name: financas-casa
description: "Gerencia as despesas da casa para Gabriel e sua esposa no Telegram. Registra gastos via texto ou comprovantes, categoriza despesas e gera resumos mensais por responsável e categoria."
version: 1.0.0
author: Gabriel
metadata:
  hermes:
    tags: [Finanças, Gastos, Orçamento, Telegram, Casa]
---

# Finanças Casa — Skill de Gestão Financeira Familiar

Esta skill capacita o Guru a gerenciar os gastos da casa de Gabriel e de sua esposa. Toda despesa informada em conversa privada ou em grupo no Telegram deve ser persistida imediatamente no banco SQLite local através do script helper `gestao_financas.py`.

## Script Helper Local
Caminho no servidor: `/home/hermes/financas/gestao_financas.py`
Banco de dados padrão: `/home/hermes/financas/financas.db`

---

## 1. Como registrar um gasto

Sempre que Gabriel ou a esposa mencionarem um gasto (ex: *"gastei 85 no mercado no debito"*, *"paguei 150 de luz no pix"*, *"farmacia 42"*, *"almoço 35 credito"*) ou enviarem imagem/dados de comprovante:

1. **Extrair os campos:**
   - **valor:** número float (ex: `85.50`).
   - **local:** nome do local ou item (ex: `Pão de Açúcar`, `Enel`, `Farmácia Pacheco`).
   - **categoria:** escolher entre `Supermercado`, `Alimentação`, `Transporte`, `Moradia`, `Saúde`, `Lazer`, `Compras`, `Educação`, `Outros`.
   - **metodo:** `Pix`, `Crédito`, `Débito`, `Dinheiro` ou `Boleto` (padrão: `Pix`).
   - **resp:** `Gabriel` ou `Esposa` (identificar pelo remetente da mensagem ou pelo nome citado).
   - **data:** `YYYY-MM-DD` (padrão: data atual).

2. **Executar no terminal:**
   ```bash
   python3 /home/hermes/financas/gestao_financas.py add --valor <VALOR> --local "<LOCAL>" --categoria "<CATEGORIA>" --metodo "<METODO>" --resp "<RESP>"
   ```

3. **Confirmar na resposta:**
   - Confirmar de forma direta e amigável:
     *"✅ Registrado! **R$ 85,50** em **Supermercado (Pão de Açúcar)** por **Gabriel** via Débito."*
   - Informar o total acumulado do mês logo abaixo.

---

## 2. Como consultar o resumo do mês

Quando perguntarem *"quanto gastamos esse mês?"*, *"resumo de gastos"*, *"relatório financeiro"*, *"gastos da casa"*:

1. **Executar no terminal:**
   ```bash
   python3 /home/hermes/financas/gestao_financas.py resumo
   ```
2. Retornar a saída formatada com o total geral, a divisão entre Gabriel e a Esposa, e os valores por categoria.

---

## 3. Como listar últimos lançamentos

Quando pedirem *"quais foram os últimos gastos?"*, *"lista os gastos"*, *"extrato"*:

1. **Executar no terminal:**
   ```bash
   python3 /home/hermes/financas/gestao_financas.py list --n 10
   ```
2. Apresentar a lista com ID, data, valor, estabelecimento e responsável.

---

## 4. Como excluir um lançamento incorreto

Quando pedirem *"excluir o gasto 12"* ou *"apagar o último lançamento"*:

1. **Executar no terminal:**
   ```bash
   python3 /home/hermes/financas/gestao_financas.py del --id <ID>
   ```
2. Confirmar a exclusão.

---

## 5. Como processar comprovantes em PDF

Quando Gabriel ou Ana enviarem um comprovante em formato PDF (Pix, fatura, boleto, nota):

1. **Extrair dados do PDF automaticamente:**
   O Guru pode usar o parser integrado:
   ```bash
   python3 /home/hermes/financas/gestao_financas.py parse_pdf --file "<CAMINHO_DO_PDF>"
   ```
   Ou ler diretamente o texto do PDF via `pdftotext "<CAMINHO_DO_PDF>" -`.

2. **Registrar a despesa extraída:**
   ```bash
   python3 /home/hermes/financas/gestao_financas.py add --valor <VALOR> --local "<LOCAL>" --categoria "<CATEGORIA>" --metodo "<METODO>" --resp "<RESP>"
   ```

3. **Confirmar no chat:**
   Confirmar o valor lido do PDF, local/beneficiário e quem enviou.

