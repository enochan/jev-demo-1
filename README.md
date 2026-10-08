# Jev 勉強会：障害福祉 × 判断モデル デモ

[Jev](https://console.typesafe.ai/)（TypeSafe AI の判断モデル）を紹介する勉強会のデモ。データはすべてダミー。

| シナリオ | 中身 |
|---|---|
| 支援系：支援記録チェック | 放デイの支援記録16件 × 6問。事故・ヒヤリハット／虐待のサインを管理者確認へ回す |
| 運営系：問い合わせトリアージ | 問い合わせ14件 × 6問。confidence が高いものだけ担当へ自動で振り分ける |
| 開発系：AIチャットのガードレール | 就労相談チャットの入力12件 × 6問。LLM に渡す前の危機対応・インジェクション・個人情報・医療判断のチェック |

## デモの起動

```bash
pip install -r requirements.txt
export TYPESAFE_API_KEY=...        # console.typesafe.ai で発行
python demo/server.py              # → http://localhost:8000
```

画面右上のバッジに動作モードが出る。

- **LIVE**：Jev API を呼ぶ。結果は `demo/cache/` に保存される
- **OFFLINE**：API キーがないとき、または `JEV_OFFLINE=1` のとき。キャッシュがあればそれを再生し、なければモック（`mock` と表示）で動く。LIVE で呼んだ API が失敗したときも同じ順でフォールバックする

> 本番前に一度 LIVE で「全件判定」を両シナリオで実行しておくと、会場のネットワークが不安定でもキャッシュで同じ結果を見せられる。

## デモの見どころ

1. **全件判定**：全件 × 6問を並列で判定し、所要時間・トークン数・概算コストを表示する
2. **しきい値スライダー**：確率のしきい値を動かすと「管理者が読む件数／見逃し」または「自動振り分け率／正解率」が連動する。想定ラベルは `scenarios.json` の `expect` に入っている
3. **その場で入力**：参加者が考えた文章を判定する
4. **質問定義の編集**：画面下部の JSON を書き換えて再実行すると、学習なしで判定項目を増やせる。Python SDK で書いた場合のコードも表示する

シナリオ・質問・ダミーデータを変えるときは `demo/scenarios.json` を編集する。

## テスト

```bash
pip install -r requirements.txt -r requirements-dev.txt
JEV_OFFLINE=1 python -m pytest -q
```

API キーは不要（モックで動く）。`scenarios.json` の構造、モック応答が SDK のレスポンス型と `expect` に合うこと、HTTP API を確認する。node があれば `index.html` の script の構文もチェックする。push / PR ごとに GitHub Actions（`.github/workflows/ci.yml`）で Python 3.10 / 3.13 で実行される。
