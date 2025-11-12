import io
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd

try:  # pragma: no cover - dependência opcional em tempo de execução
    from fugashi import Tagger

    TAGGER: Optional[Tagger] = Tagger()
except Exception:  # fallback silencioso quando o dicionário não está disponível
    TAGGER = None


app = FastAPI(title="Tatemae & Honne Analyzer", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


HEDGES = [
    "と思います",
    "かもしれません",
    "でしょう",
    "ではないかと",
    "存じます",
    "かなと",
    "検討",
    "前向きに検討",
    "社内調整",
    "改めてご連絡",
    "助かります",
    "差し支えなければ",
    "もう少し",
    "〜ていただけると",
    "参考までに",
    "一旦",
    "可能であれば",
]

HONORIFICS = [
    "いたします",
    "申し上げます",
    "させていただきます",
    "でございます",
    "存じます",
    "お世話になっております",
    "お手数",
    "恐れ入ります",
    "恐縮",
    "お忙しいところ",
]

HONOR_PREFIX = ["お", "ご"]

DIRECTNESS = [
    "本音",
    "率直に",
    "正直に",
    "実は",
    "明確に",
    "断言します",
    "合意は難しい",
    "難しいです",
    "できません",
    "無理です",
    "反対です",
    "致しかねます",
]

NEGATIONS = ["できません", "無理", "難しい", "致しかねます", "否定", "不可能"]

SENT_SPLIT = re.compile(r"[。．！？!?]\s*")


def tokenize(text: str) -> List[str]:
    if TAGGER:
        return [tok.surface for tok in TAGGER(text)]
    return list(text)


def honorific_score(sentence: str) -> int:
    score = 0
    for hp in HONOR_PREFIX:
        score += sentence.count(hp)
    for honorific in HONORIFICS:
        score += sentence.count(honorific)
    return score


def hedge_score(sentence: str) -> int:
    return sum(sentence.count(h) for h in HEDGES)


def directness_score(sentence: str) -> int:
    return sum(sentence.count(d) for d in DIRECTNESS)


def negation_score(sentence: str) -> int:
    return sum(sentence.count(n) for n in NEGATIONS)


def analyze_sentence(sentence: str) -> Optional[Dict[str, Any]]:
    if not sentence.strip():
        return None

    hed = hedge_score(sentence)
    hon = honorific_score(sentence)
    direct = directness_score(sentence)
    neg = negation_score(sentence)

    tatemae_raw = hed + 0.6 * hon
    honne_raw = direct + 1.2 * neg

    total = tatemae_raw + honne_raw
    if total == 0:
        tatemae_prob = 0.5
        honne_prob = 0.5
    else:
        tatemae_prob = tatemae_raw / total
        honne_prob = honne_raw / total

    signals: List[str] = []
    if hed > 0:
        signals.append("Hedge/mitigação")
    if hon > 0:
        signals.append("Honorífico/keigo")
    if direct > 0:
        signals.append("Franqueza/diretividade")
    if neg > 0:
        signals.append("Negação clara")

    leitura_t = (
        "Preserva harmonia, adia/mitiga, evita confronto"
        if tatemae_prob >= honne_prob
        else "Baixa presença de Tatemae"
    )
    leitura_h = (
        "Transmite intenção real com maior clareza"
        if honne_prob >= tatemae_prob
        else "Honne pouco evidente"
    )

    evid_points = hed + hon + direct + neg
    confidence = min(0.95, 0.5 + 0.1 * evid_points)

    return {
        "trecho": sentence.strip(),
        "sinal": "・".join(signals) if signals else "Indeterminado",
        "leitura_tatemae": leitura_t,
        "leitura_honne": leitura_h,
        "evidencias": (
            f"hedges={hed}, honoríficos={hon}, direção={direct}, negação={neg}"
        ),
        "confianca": round(confidence, 2),
        "tatemae_prob": round(tatemae_prob, 2),
        "honne_prob": round(honne_prob, 2),
    }


def split_sentences(text: str) -> List[str]:
    parts = SENT_SPLIT.split(text)
    return [part for part in parts if part and part.strip()]


def aggregate_probs(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    if not rows:
        return {"tatemae": 0.5, "honne": 0.5}
    tatemae_avg = sum(row["tatemae_prob"] for row in rows) / len(rows)
    honne_avg = sum(row["honne_prob"] for row in rows) / len(rows)
    return {"tatemae": round(tatemae_avg, 2), "honne": round(honne_avg, 2)}


def scientific_analysis(context: str) -> str:
    return (
        "◆ Enquadramento científico\n"
        "- Pragmática: mitigação (hedges), honoríficos (keigo), indireção e leitura de contexto (空気を読む) como dispositivos de facework.\n"
        "- Antropologia/Psicologia cultural: uchi/soto, amae/enryo, giri/ninjō; manutenção da harmonia relacional (和) e evitação de incerteza (Hofstede UAI).\n"
        "- Teorias-chave: Goffman (face), Brown & Levinson (polidez), Hall (alto contexto), Grice (máximas conversacionais).\n"
        "- Interpretação: Tatemae funciona como camada protetiva e protocolo social; Honne emerge por marcas de franqueza, negação explícita ou metacomunicação (率直に, 本音).\n"
        f"- Contexto do usuário: {context or 'não fornecido'}.\n"
    )


def recommendations(lang: str) -> List[str]:
    if lang == "JP":
        return [
            "確認のため、本件の理解は次の通りで相違ありませんでしょうか。",
            "不躾なお願いで恐縮ですが、意思決定の基準と期限を共有いただけますか。",
            "ご懸念点を明文化できれば、こちらで代替案を準備いたします。",
        ]
    if lang == "EN":
        return [
            "To confirm, may I restate our understanding like this...?",
            "Could you share the decision criteria and timeline so we stay aligned?",
            "If we can surface any concerns explicitly, I'll prepare relationship-safe alternatives.",
        ]
    return [
        "Para confirmar: nosso entendimento está correto desta forma…?",
        "Poderia compartilhar critérios e prazo de decisão para alinharmos expectativas?",
        "Se pudermos explicitar as preocupações, preparo alternativas que preservem a relação.",
    ]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(
    text: str = Form(...),
    context: str = Form(""),
    mode: str = Form("profundo"),
    lang: str = Form("PT-BR"),
) -> JSONResponse:
    sentences = split_sentences(text)
    rows = [result for sentence in sentences if (result := analyze_sentence(sentence))]

    agg = aggregate_probs(rows)
    resumo = (
        f"Tatemae≈{agg['tatemae'] * 100:.0f}% / Honne≈{agg['honne'] * 100:.0f}% — "
        "o texto sugere equilíbrio entre fachada social (mitigação/keigo) e intenção real "
        "(franqueza/negação) conforme os sinais linguísticos detectados."
    )

    analise_cient = (
        scientific_analysis(context)
        if mode != "rapido"
        else "Modo rápido: síntese executiva sem aprofundamento teórico."
    )
    recs = recommendations(lang)

    df = pd.DataFrame(
        rows,
        columns=[
            "trecho",
            "sinal",
            "leitura_tatemae",
            "leitura_honne",
            "evidencias",
            "confianca",
            "tatemae_prob",
            "honne_prob",
        ],
    )
    app.state.last_df = df

    return JSONResponse(
        {
            "resumo": resumo,
            "probs": agg,
            "tabela": rows,
            "analise_cientifica": analise_cient,
            "recomendacoes": recs,
            "limites": [
                "Inferências dependem de contexto relacional/hierárquico; evite conclusões categóricas.",
                "Solicite confirmação educada para reduzir ruído intercultural.",
            ],
        }
    )


@app.get("/export/csv")
async def export_csv() -> StreamingResponse | JSONResponse:
    df = getattr(app.state, "last_df", None)
    if df is None or df.empty:
        return JSONResponse({"error": "Nenhuma análise disponível para exportar."}, status_code=400)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analise_tatemae_honne.csv"},
    )


# Execução local: uvicorn app:app --reload
