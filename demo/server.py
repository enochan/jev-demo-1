"""Jev 勉強会デモ用サーバー（標準ライブラリ + typesafe-sdk のみ）。

    export TYPESAFE_API_KEY=...   # 未設定ならキャッシュ → モックで動く
    python demo/server.py         # http://localhost:8000

外に公開するとき（Cloudflare Tunnel など）は DEMO_PASSWORD を設定すると Basic 認証がかかる
（ユーザー名は何でもよく、パスワードだけを照合する）。

- LIVE : Jev API を呼ぶ。結果は demo/cache/ に保存し、オフライン時に再生できる
- CACHE: キーなし / API 失敗時、同じ (質問, 本文) の過去結果を返す
- MOCK : キャッシュもない場合のダミー応答（画面に MOCK と表示される）
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import random
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
SCENARIOS = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))
CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CONCURRENCY = int(os.environ.get("JEV_CONCURRENCY", "8"))
FORCE_OFFLINE = os.environ.get("JEV_OFFLINE") == "1"


def live_enabled() -> bool:
    return bool(os.environ.get("TYPESAFE_API_KEY")) and not FORCE_OFFLINE


# ---------------------------------------------------------------- Jev 呼び出し


def build_state(scenario: dict, item: str | dict) -> dict:
    """item は本文（文字列）か、そのまま state にする JSON（構造化データ・ランキング）。"""
    if isinstance(item, dict):
        return {**scenario.get("state_extra", {}), **item}
    return {scenario["state_key"]: item, **scenario.get("state_extra", {})}


async def call_jev(client, scenario: dict, questions: dict, text: str | dict) -> dict:
    started = time.perf_counter()
    response = await client.system_one(state=build_state(scenario, text), questions=questions)
    latency_ms = (time.perf_counter() - started) * 1000
    return {
        "answers": {name: answer.model_dump(mode="json") for name, answer in response.answers.items()},
        "usage": response.usage.model_dump(mode="json"),
        "model": response.model,
        "latency_ms": round(latency_ms),
    }


async def judge_many(scenario: dict, questions: dict, texts: list[str | dict]) -> list[dict]:
    """texts を並列で判定する。LIVE 失敗時は cache → mock にフォールバック。"""
    results: list[dict | None] = [None] * len(texts)
    pending = []
    for i, text in enumerate(texts):
        if not live_enabled():
            results[i] = offline_answer(scenario, questions, text)
        else:
            pending.append(i)

    if pending:
        from typesafe_sdk import AsyncTypeSafeClient

        semaphore = asyncio.Semaphore(CONCURRENCY)
        async with AsyncTypeSafeClient() as client:

            async def run(i: int) -> None:
                async with semaphore:
                    try:
                        result = await call_jev(client, scenario, questions, texts[i])
                        result["source"] = "live"
                        cache_put(questions, texts[i], result)
                        results[i] = result
                    except Exception as error:  # noqa: BLE001 - デモ中は落とさない
                        print(f"[jev] live call failed: {error!r}", file=sys.stderr)
                        fallback = offline_answer(scenario, questions, texts[i])
                        fallback["error"] = f"{type(error).__name__}: {error}"
                        results[i] = fallback

            await asyncio.gather(*(run(i) for i in pending))
    return results  # type: ignore[return-value]


# ---------------------------------------------------------------- キャッシュ


def cache_key(questions: dict, text: str | dict) -> str:
    raw = json.dumps({"q": questions, "t": text}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def cache_put(questions: dict, text: str | dict, result: dict) -> None:
    (CACHE_DIR / f"{cache_key(questions, text)}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


def cache_get(questions: dict, text: str | dict) -> dict | None:
    path = CACHE_DIR / f"{cache_key(questions, text)}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def offline_answer(scenario: dict, questions: dict, text: str | dict) -> dict:
    cached = cache_get(questions, text)
    if cached:
        cached["source"] = "cache"
        return cached
    return mock_answer(scenario, questions, text)


# ---------------------------------------------------------------- モック（API キーがない時の代役）

MOCK_HINTS = {
    "incident": ["転倒", "転び", "打った", "ぶつか", "ケガ", "けが", "擦りむ", "噛", "踏み外", "誤って", "飛び出", "走り出", "ぶつけ", "落ち"],
    "safeguarding": ["あざ", "アザ", "同じ服", "におい", "パパが", "ママが", "叩かれ", "お腹すいた", "帰りたくない", "やけど"],
    "parent_share": ["ケガ", "打った", "転び", "発熱", "噛", "転倒", "泣", "パニック", "眠れて", "トラブル", "擦りむ"],
    "visit": ["見学", "体験", "説明会"],
    "certificate": ["受給者証", "手帳", "手続き", "診断"],
    "complaint": ["改善", "困ります", "不満", "待たされ", "対応が悪", "苦情"],
    "crisis": ["消えて", "死にたい", "どうでもよく", "自分を傷つけ", "いなくなりたい"],
    "injection": ["無視", "忘れて", "システムプロンプト", "開発者モード", "制限のない"],
    "pii": ["電話番号", "090-", "080-", "住所", "手帳の番号"],
    "medical": ["薬", "診断", "処方", "飲む量"],
    "health": ["眠れ", "疲れ", "体調", "起きるのがつらい", "通院"],
    "workload": ["業務が増え", "残業", "担当業務"],
    "relation": ["声をかけにくい", "上司", "同僚", "言い方がきつい"],
    "accommodation": ["配慮", "メモで"],
}
CHOICE_HINTS = {
    "健康・生活": ["発熱", "食事", "トイレ", "着替え", "服", "薬", "睡眠"],
    "運動・感覚": ["はさみ", "トランポリン", "転倒", "階段", "バランス", "ボール"],
    "認知・行動": ["パニック", "大声", "走り出", "見通し", "こだわり", "クールダウン"],
    "言語・コミュニケーション": ["ありがとう", "ことば", "言葉", "ひらがな", "伝え"],
    "人間関係・社会性": ["他児", "順番", "SST", "友達", "取り合い", "バカ"],
    "児童発達支援": ["歳", "保育園", "幼稚園", "健診", "未就学"],
    "放課後等デイサービス": ["小学", "中学", "高校", "放課後", "学校"],
    "就労移行支援": ["就職", "転職", "働きたい", "訓練", "休職"],
    "就労定着支援": ["入社", "職場", "欠勤", "就職して"],
    "採用・その他": ["求人", "応募", "障害福祉課", "指定", "取材"],
    "保護者": ["息子", "娘", "子ども"],
    "本人": ["私", "就職して", "休職中", "手帳を持っています"],
    "相談支援専門員・行政など関係機関": ["相談支援専門員", "障害福祉課", "市の"],
    "企業": ["当社", "社員", "御社の支援"],
    "対象内": ["仕事", "職場", "就職", "求人", "面接", "就労", "働"],
    "対象外": ["レシピ", "天気", "ゲーム"],
    "様子見": ["慣れて"],
    "本人と再面談": ["眠れ", "つらい"],
    "企業と三者面談": ["配慮", "業務が増え", "上司", "残業"],
    "医療・支援機関と連携": ["通院", "主治医"],
}
SCORE_HINTS = {
    "condition": [(3, ["パニック", "うずくま"]), (2, ["発熱", "噛", "個別対応"]), (1, ["泣", "あざ", "硬"])],
    "quit_risk": [(3, ["自信がない", "辞めたい"]), (2, ["眠れ", "配慮"]), (1, ["残業", "疲れ"])],
    "distress": [(2, ["消えて", "しんどく", "つらい", "情けなく"]), (1, ["迷って", "眠れない", "困って"])],
    "urgency": [(2,["至急", "今日", "すぐ", "荒れて"]), (1, ["空き状況", "改善", "来月", "話をしたい"])],
}


def _jitter(seed: str, low: float, high: float) -> float:
    return random.Random(seed).uniform(low, high)


def _noul(p: float) -> dict:
    return {"type": "noul", "noul": round(p, 3)}


def _choice(labels: list[str], top: str, conf: float, seed: str) -> dict:
    rest = [label for label in labels if label != top]
    weights = [_jitter(seed + label, 0.2, 1.0) for label in rest]
    total = sum(weights) or 1
    probs = {top: conf, **{label: (1 - conf) * w / total for label, w in zip(rest, weights)}}
    return {"type": "choice", "choice": top, "confidence": round(conf, 3), "probabilities": {k: round(v, 3) for k, v in probs.items()}}


def _score(criteria: list, level: int, conf: float) -> dict:
    n = len(criteria)
    probs = {i: (conf if i == level else (1 - conf) / max(n - 1, 1)) for i in range(n)}
    return {
        "type": "score",
        "score": round(sum(i * p for i, p in probs.items()), 2),
        "confidence": round(conf, 3),
        "probabilities": {str(i): round(p, 3) for i, p in probs.items()},
        "legend": {str(i): c if isinstance(c, str) else json.dumps(c, ensure_ascii=False) for i, c in enumerate(criteria)},
    }


def _ranking_fit(scenario: dict, item) -> dict:
    """ランキングのモック：プリセットの求職者・子どもなら用意した適合度を使う。"""
    if scenario.get("mode") != "ranking" or not isinstance(item, dict):
        return {}
    preset = next((p for p in scenario["presets"] if p["text"] == item.get(scenario["query_key"])), None)
    if not preset:
        return {}
    return {f"c_{c['id']}": c["fit"][preset["id"]] for c in scenario["candidates"]}


def mock_answer(scenario: dict, questions: dict, item: str | dict) -> dict:
    record = next((r for r in scenario.get("records", []) if r.get("state", r.get("text")) == item), None)
    expect = record["expect"] if record else {}
    ambiguous = bool(record and record.get("ambiguous"))
    fits = _ranking_fit(scenario, item)
    text = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
    answers = {}
    for name, q in questions.items():
        seed = f"{name}:{text}"
        if name in fits:
            answers[name] = _noul(min(0.99, max(0.01, fits[name] + _jitter(seed, -0.05, 0.05))))
            continue
        if name.startswith("c_") and q.get("type") == "noul" and scenario.get("mode") == "ranking":
            answers[name] = _noul(_jitter(seed, 0.05, 0.6))
            continue
        conf = _jitter(seed, 0.48, 0.66) if ambiguous else _jitter(seed, 0.86, 0.97)
        kind = q.get("type")
        if kind == "noul":
            if name in expect:
                yes = expect[name]
            else:
                yes = any(word in text for word in MOCK_HINTS.get(name, []))
                conf = _jitter(seed, 0.7, 0.9)
            answers[name] = _noul(conf if yes else 1 - conf)
        elif kind == "choice":
            labels = list(q["criteria"].keys())
            top = expect.get(name)
            if top not in labels:
                hits = {label: sum(word in text for word in CHOICE_HINTS.get(label, [])) for label in labels}
                top = max(labels, key=lambda label: (hits[label], -labels.index(label)))
                conf = _jitter(seed, 0.55, 0.85) if hits[top] else _jitter(seed, 0.3, 0.45)
            answers[name] = _choice(labels, top, conf, seed)
        elif kind == "score":
            criteria = q["criteria"]
            level = expect.get(name)
            if level is None:
                level = next((lv for lv, words in SCORE_HINTS.get(name, []) if any(w in text for w in words)), 0)
                level = min(level, len(criteria) - 1)
                conf = _jitter(seed, 0.5, 0.8)
            answers[name] = _score(criteria, level, conf)
    tokens = len(json.dumps({"s": text, "q": questions}, ensure_ascii=False)) // 2
    return {
        "answers": answers,
        "usage": {"input_tokens": tokens, "output_tokens": len(answers) * 2},
        "model": "mock",
        "latency_ms": round(_jitter(text, 70, 220)),
        "source": "mock",
    }


# ---------------------------------------------------------------- HTTP


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: D401 - 静かにする
        if "/api/" in self.path:
            sys.stderr.write("[http] " + fmt % args + "\n")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status: int = 200) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _authorized(self) -> bool:
        """DEMO_PASSWORD が設定されていれば Basic 認証を求める。未設定なら素通し。"""
        password = os.environ.get("DEMO_PASSWORD")
        if not password:
            return True
        header = self.headers.get("Authorization", "")
        if header.startswith("Basic "):
            try:
                _, _, given = base64.b64decode(header[6:]).decode().partition(":")
            except ValueError:
                given = ""
            if hmac.compare_digest(given.encode(), password.encode()):
                return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Jev demo", charset="UTF-8"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def do_GET(self):
        if not self._authorized():
            return
        if self.path in ("/", "/index.html"):
            self._send(200, (ROOT / "static" / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/config":
            self._json({"live": live_enabled(), "scenarios": SCENARIOS})
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if not self._authorized():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            scenario = SCENARIOS[body["scenario"]]
            questions = body.get("questions") or scenario["questions"]
            if self.path == "/api/judge":
                texts = [body["item"] if "item" in body else body["text"]]
            elif self.path == "/api/batch":
                texts = [r.get("state", r.get("text")) for r in scenario["records"]]
            else:
                return self._send(404, b"not found", "text/plain")
            started = time.perf_counter()
            results = asyncio.run(judge_many(scenario, questions, texts))
            wall_ms = round((time.perf_counter() - started) * 1000)
            if all(r["source"] != "live" for r in results):
                wall_ms = max(r["latency_ms"] for r in results)  # オフライン時は並列実行を模擬
            self._json({"results": results, "wall_ms": wall_ms})
        except Exception as error:  # noqa: BLE001
            self._json({"error": f"{type(error).__name__}: {error}"}, status=400)


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    mode = "LIVE (Jev API)" if live_enabled() else "OFFLINE (cache → mock)"
    print(f"Jev demo: http://localhost:{port}  mode={mode}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
