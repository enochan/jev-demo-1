"""demo/scenarios.json の構造チェック。

mode は省略 / "batch" / "ranking" / "realtime" を受け付ける。
batch の record は text の代わりに state（JSON オブジェクト）を持ってもよい。
"""

import pytest

from conftest import SCENARIOS


def check_questions(questions: dict) -> None:
    assert isinstance(questions, dict) and questions
    for name, q in questions.items():
        assert q.get("type") in {"choice", "score", "noul"}, name
        if q["type"] == "choice":
            assert isinstance(q["criteria"], dict) and q["criteria"], name
        elif q["type"] == "score":
            assert isinstance(q["criteria"], list) and q["criteria"], name


def check_expect(questions: dict, expect: dict, where: str) -> None:
    for name, value in expect.items():
        assert name in questions, f"{where}: 未定義の質問 {name}"
        q = questions[name]
        if q["type"] == "choice":
            assert value in q["criteria"], f"{where}.{name}: {value!r}"
        elif q["type"] == "score":
            assert type(value) is int and 0 <= value < len(q["criteria"]), f"{where}.{name}: {value!r}"
        else:
            assert type(value) is bool, f"{where}.{name}: {value!r}"


def check_gate(questions: dict, gate: dict) -> None:
    if gate["kind"] == "noul_any":
        assert gate["questions"]
        for name in gate["questions"]:
            assert questions[name]["type"] == "noul", name
    elif gate["kind"] == "choice_conf":
        assert questions[gate["question"]]["type"] == "choice"
    else:
        pytest.fail(f"未知の gate.kind: {gate['kind']}")


@pytest.mark.parametrize("sid", SCENARIOS)
def test_scenario(sid):
    s = SCENARIOS[sid]
    mode = s.get("mode", "batch")
    assert mode in {"batch", "ranking", "realtime"}
    assert s["title"]

    if mode == "batch":
        assert isinstance(s["state_key"], str)
        check_questions(s["questions"])
        check_gate(s["questions"], s["gate"])
        assert s["records"]
        ids = [r["id"] for r in s["records"]]
        assert len(ids) == len(set(ids)), "record id が重複している"
        for r in s["records"]:
            assert isinstance(r.get("text"), str) or isinstance(r.get("state"), dict), r["id"]
            check_expect(s["questions"], r.get("expect", {}), f"{sid}/{r['id']}")

    elif mode == "ranking":
        assert "questions" not in s and "records" not in s
        for key in ("query_key", "candidates_key", "question_template"):
            assert isinstance(s[key], str) and s[key], key
        preset_ids = [p["id"] for p in s["presets"]]
        assert preset_ids and len(preset_ids) == len(set(preset_ids))
        candidate_ids = [c["id"] for c in s["candidates"]]
        assert candidate_ids and len(candidate_ids) == len(set(candidate_ids))
        for c in s["candidates"]:
            assert set(c["fit"]) >= set(preset_ids), c["id"]
            assert all(0 <= v <= 1 for v in c["fit"].values()), c["id"]

    else:  # realtime
        assert "records" not in s and "gate" not in s
        assert isinstance(s["state_key"], str)
        assert s["script"] and all(isinstance(line, str) and line for line in s["script"])
        check_questions(s["questions"])
