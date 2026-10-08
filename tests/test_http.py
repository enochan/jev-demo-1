"""HTTP 経由の結合テスト（オフライン）。実際にサーバーを立てて叩く。"""

import json
import re
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from conftest import BATCH_IDS, DEMO_DIR, SCENARIOS


@pytest.fixture(scope="module")
def base_url(tmp_path_factory):
    import server

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(server, "CACHE_DIR", tmp_path_factory.mktemp("cache"))
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
        httpd.shutdown()
        httpd.server_close()


def request(url: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_index_html(base_url):
    with urllib.request.urlopen(base_url + "/", timeout=10) as res:
        assert res.headers["Content-Type"].startswith("text/html")
        assert b"<html" in res.read().lower()


def test_config(base_url):
    status, body = request(base_url + "/api/config")
    assert status == 200
    assert body["live"] is False
    assert body["scenarios"] == SCENARIOS


@pytest.mark.parametrize("sid", BATCH_IDS)
def test_judge(base_url, sid):
    status, body = request(base_url + "/api/judge", {"scenario": sid, "text": "今日は落ち着いて過ごせた。"})
    assert status == 200
    [result] = body["results"]
    assert set(result["answers"]) == set(SCENARIOS[sid]["questions"])
    assert result["source"] == "mock"


@pytest.mark.parametrize("sid", BATCH_IDS)
def test_batch(base_url, sid):
    status, body = request(base_url + "/api/batch", {"scenario": sid})
    assert status == 200
    assert len(body["results"]) == len(SCENARIOS[sid]["records"])
    assert body["wall_ms"] >= 0


def test_custom_questions(base_url):
    questions = {"greeting": {"type": "noul", "instructions": "あいさつが含まれているか"}}
    status, body = request(base_url + "/api/judge", {"scenario": BATCH_IDS[0], "questions": questions, "text": "こんにちは"})
    assert status == 200
    assert list(body["results"][0]["answers"]) == ["greeting"]


def test_unknown_scenario(base_url):
    status, body = request(base_url + "/api/judge", {"scenario": "no_such_scenario", "text": "x"})
    assert status == 400
    assert "error" in body


def test_index_script_parses(tmp_path):
    """index.html のインライン script が JS として構文エラーにならないこと（node がなければスキップ）。"""
    node = shutil.which("node")
    if not node:
        pytest.skip("node が見つからない")
    html = (DEMO_DIR / "static" / "index.html").read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    assert scripts
    path = tmp_path / "index.js"
    path.write_text("\n".join(scripts), encoding="utf-8")
    proc = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_password_required_when_set(base_url, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "secret")
    import base64

    def get(auth: str | None) -> int:
        req = urllib.request.Request(base_url + "/api/config")
        if auth:
            req.add_header("Authorization", "Basic " + base64.b64encode(auth.encode()).decode())
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                return res.status
        except urllib.error.HTTPError as error:
            return error.code

    assert get(None) == 401
    assert get("anyone:wrong") == 401
    assert get("anyone:secret") == 200

    try:
        urllib.request.urlopen(urllib.request.Request(base_url + "/api/judge", data=b"{}"), timeout=10)
        post_status = 200
    except urllib.error.HTTPError as error:
        post_status = error.code
    assert post_status == 401
