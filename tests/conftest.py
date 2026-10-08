"""テスト共通設定。

server.py は import 時に JEV_OFFLINE を読むので、import より前にオフライン化しておく。
"""

import json
import os
import sys
from pathlib import Path

import pytest

os.environ["JEV_OFFLINE"] = "1"
os.environ.pop("TYPESAFE_API_KEY", None)

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"
sys.path.insert(0, str(DEMO_DIR))

SCENARIOS = json.loads((DEMO_DIR / "scenarios.json").read_text(encoding="utf-8"))
BATCH_IDS = [sid for sid, s in SCENARIOS.items() if s.get("mode", "batch") == "batch"]


@pytest.fixture
def server(monkeypatch, tmp_path):
    """キャッシュを一時ディレクトリに向けた server モジュール（demo/cache を汚さない）。"""
    import server as module

    monkeypatch.setattr(module, "CACHE_DIR", tmp_path)
    return module
