# Finanças Casa — Gestão de Despesas do Casal no Telegram

Integração de controle financeiro familiar para o **Guru (Hermes Agent)** rodando no Telegram (`@Guru_Gabriel_bot`).

## Funcionalidades
- **Registro Rápido:** Salva despesas informadas por texto ou comprovantes bancários.
- **Categorização Automática:** Supermercado, Alimentação, Transporte, Moradia, Saúde, Lazer, Compras, etc.
- **Divisão por Responsável:** Separação entre Gabriel e Esposa.
- **Relatório Mensal:** Totais do mês, percentual por pessoa e por categoria.
- **Armazenamento Seguro e Local:** SQLite local (`/home/hermes/financas/financas.db`), sem serviços pagos externos.

## Estrutura
- `gestao_financas.py`: Módulo CLI e banco de dados SQLite.
- `test_financas.py`: Testes unitários do módulo.
- `SKILL.md`: Instrução canônica para a skill do Guru no Hermes.

---
Feito por [Gabriel Ferreira](https://github.com/GABRIELFERR9).
