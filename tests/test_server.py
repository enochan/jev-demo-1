"""server.py の単体テスト（オフライン）。"""

import json

import pytest
from typesafe_sdk import SystemOneResponse

from conftest import BATCH_IDS, SCENARIOS

# text を持つ record だけを対象にする（state だけの record は別経路で扱う）
CASES = [(sid, r) for sid in BATCH_IDS for r in SCENARIOS[sid]["records"] if "text" in r]


def test_build_state(server):
    scenario = {"state_key": "record", "state_extra": {"facility": "放デイ"}}
    assert server.build_state(scenario, "本文") == {"record": "本文", "facility": "放デイ"}
    assert server.build_state({"state_key": "msg"}, "x") == {"msg": "x"}


def test_cache_key_is_stable(server):
    q = {"a": {"type": "noul"}, "b": {"type": "score", "criteria": ["x", "y"]}}
    reordered = {"b": {"criteria": ["x", "y"], "type": "score"}, "a": {"type": "noul"}}
    assert server.cache_key(q, "本文") == server.cache_key(reordered, "本文")
    assert server.cache_key(q, "本文") != server.cache_key(q, "本文2")
    assert len(server.cache_key(q, "本文")) == 24


def test_cache_round_trip(server, tmp_path):
    scenario = SCENARIOS[BATCH_IDS[0]]
    questions, text = scenario["questions"], "キャッシュ確認用の本文"
    assert server.cache_get(questions, text) is None
    result = {**server.mock_answer(scenario, questions, text), "source": "live"}
    server.cache_put(questions, text, result)
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert server.cache_get(questions, text) == result
    assert server.offline_answer(scenario, questions, text)["source"] == "cache"


@pytest.mark.parametrize("sid,record", CASES, ids=[f"{sid}/{r['id']}" for sid, r in CASES])
def test_mock_answer(server, sid, record):
    scenario = SCENARIOS[sid]
    questions = scenario["questions"]
    result = server.mock_answer(scenario, questions, record["text"])

    # 実 SDK のレスポンス型として読めること（UI は LIVE とモックを区別せず描画する）
    parsed = SystemOneResponse.model_validate_json(json.dumps(result))
    assert set(parsed.answers) == set(questions)
    for name, answer in parsed.answers.items():
        assert answer.type == questions[name]["type"]
        if answer.type == "noul":
            assert 0 <= answer.noul <= 1
        else:
            assert 0 <= answer.confidence <= 1
            assert sum(answer.probabilities.values()) == pytest.approx(1, abs=0.02)
        if answer.type == "score":
            assert set(answer.legend) == set(range(len(questions[name]["criteria"])))

    # 決定的であること
    assert server.mock_answer(scenario, questions, record["text"]) == result

    # 曖昧でない record は想定ラベルどおりに答える
    if record.get("ambiguous"):
        return
    for name, want in record.get("expect", {}).items():
        answer = parsed.answers[name]
        if answer.type == "noul":
            assert (answer.noul >= 0.5) == want, name
        elif answer.type == "choice":
            assert answer.choice == want, name
        else:
            assert round(answer.score) == want, name


@pytest.mark.parametrize("sid", BATCH_IDS)
def test_mock_answer_free_text(server, sid):
    """record にない入力（その場で入力）でも全質問に答える。"""
    scenario = SCENARIOS[sid]
    result = server.mock_answer(scenario, scenario["questions"], "今日は転倒してひざを擦りむいた。")
    assert set(SystemOneResponse.model_validate_json(json.dumps(result)).answers) == set(scenario["questions"])
