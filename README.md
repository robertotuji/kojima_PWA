# Tatemae & Honne Analyzer (FastAPI)

Aplicativo FastAPI para interpretar Tatemae (fachada social) e Honne (intenção real) em textos japoneses, combinando heurísticas linguísticas e insights socioculturais.

## Requisitos

```bash
python -m pip install -r requirements.txt
python -m unidic_lite.download
```

> O comando `unidic_lite.download` instala um dicionário leve necessário para a tokenização japonesa com Fugashi.

## Executando localmente

```bash
uvicorn app:app --reload
```

Abra: <http://127.0.0.1:8000/>

## Como funciona

- **Heurística híbrida**: identifica hedges/mitigadores, honoríficos (keigo) e sinais de franqueza/negação para estimar Tatemae vs. Honne em cada sentença.
- **Probabilidades agregadas**: calcula médias documentais de Tatemae/Honne e gera um resumo executivo (5–7 linhas).
- **Análise científica**: referencia pragmática, antropologia/psicologia cultural (uchi/soto, amae/enryo, giri/ninjō, Hofstede, Hall, Goffman, Brown & Levinson).
- **Recomendações interculturais**: frases-modelo (JP↔PT/EN) para confirmar entendimentos com cortesia.
- **Exportação CSV**: baixa a tabela de sentenças com sinais, leituras e confiança.
- **Privacidade**: não registra textos analisados no console por padrão.

## Estrutura de pastas

```
.
├── app.py
├── requirements.txt
├── static/
│   └── .keep
├── templates/
│   └── index.html
└── README.md
```

## Considerações e extensões

- Este MVP prioriza heurísticas explicáveis; você pode incorporar embeddings ou modelos transformer japoneses para maior precisão.
- Ajuste pesos das listas de sinais conforme o domínio (corporativo, acadêmico, cotidiano).
- Inclua autenticação ou persistência se precisar armazenar históricos (não implementado por questões de privacidade).
