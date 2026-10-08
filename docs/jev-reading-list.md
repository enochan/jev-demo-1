# Jev と型安全な判断ツールのリーディングリスト

社内 Jev 勉強会向けの、共有用の読書リストです。

- **調査日**: 2026-10-08
- **対象**: TypeSafe AI の Jev（2026-09-15 公開の「System One Model」／判断モデル）と、構造化出力・制約付きデコーディング・ガードレール分類器・確信度の較正・LLM-as-a-Judge など、Jev の使いどころを考えるうえで比べておきたい技術
- **選定の基準**
  - **一次情報を優先**しています（公式ブログ、ドキュメント、PyPI、GitHub、論文の順）。その次に企業の技術ブログ、名前の分かる技術者の記事を選びました。
  - **ベンダー公表値**（速度・価格・ベンチマーク）には「ベンダー公表値」と書いています。たとえば「LLM の 40〜200 倍速い」「193.6 倍速く 444.6 倍安い」「ハルシネーションしない」は TypeSafe 自身の評価や主張で、独立した検証ではありません。
  - **確認の方法**: 調査環境のプロキシで多くのサイトの本文が開けなかったため、各エントリに確認方法を書いています。「本文確認済」は本文を取得して読んだもの、「検索スニペットのみ」は検索結果の抜粋だけで要約したものです。URL はすべて検索結果に出たもの、または取得できたページのものです。
  - Jev はアーリーアクセス中で、SDK のマイナーバージョンでも破壊的変更が報告されています。コードを書く前に公式ドキュメントの最新版を確認してください。

---

## まず読む3本

1. **[Introducing System One Models & Jev（TypeSafe AI Blog）](https://typesafe.ai/blog/introducing-system-one-models-and-jev)**: 公式
   リリース告知です。新しいアーキテクチャ・並列サンプラー・RLCD（Reinforcement Learning for Calibrated Decisions）の3点で「判断専用」のモデルを作った、という全体像が分かります。RLHF／RLVR との違いの表もあります。速度・価格・「ハルシネーションしない」はベンダーの主張です。（検索スニペットのみ）
2. **[Example use cases（TypeSafe Docs: Use-case map）](https://docs.typesafe.ai/concepts/use-case-map)**: 公式
   ルーティング、分類、スコアリング、検証、ガードレールなど、公式が想定する用途の一覧です。自社の業務に当てはめるときの出発点になります。（検索スニペットのみ）
3. **[緊急で社内Jev勉強会を開催したらアイデアがバンバン出て頭が柔らかくなった（LayerX エンジニアブログ, 2026-09-18）](https://tech.layerx.co.jp/entry/2026/09/18/185816)**: 企業技術ブログ
   国内企業が社内勉強会で用途を洗い出した記録です。メール分類の検証では、全体の精度は Gemini がやや上でした。一方で Jev は確信度が高い回答ほど正解しやすく、「高確信度は自動処理、低確信度は人か上位モデルへ回す」設計を提案しています。（検索スニペットのみ）

---

## 公式・一次情報

| # | リンク | 種別 | 内容 | 確認方法 |
|---|---|---|---|---|
| 1 | [TypeSafe AI ホーム](https://typesafe.ai/) | 公式 | 製品概要と主要な数値（193.6 倍速い、444.6 倍安い）。「自律で動かす閾値と人に確認する閾値を決めて使う」という説明もあります。数値は**ベンダー公表値**です。 | スニペットのみ |
| 2 | [How to build with TypeSafe](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) | 公式 Docs | state（入力）と型付きの質問（Choice / Score / Noul）を渡して判断を受け取る、という基本の組み立て方です。 | スニペットのみ |
| 3 | [Noul](https://docs.typesafe.ai/primitives/noul) | 公式 Docs | Yes/No 型の質問です。閾値は既定 0.5 で、誤った Yes のコストが高い場合は引き上げる、という指針があります。Choice や Score と違い、Noul には confidence 値がありません。 | スニペットのみ |
| 4 | [Confidence-gated routing](https://docs.typesafe.ai/patterns/confidence-routing) | 公式 Docs | 確信度で自動処理と人の確認を分けるパターンです。行動ごとに閾値を変える例（残高照会は 0.6、送金承認は 0.85 超）があります。福祉の現場のように誤判定のコストが高い業務では特に参考になります。 | スニペットのみ |
| 5 | [Guardrails for LLMs（Cookbook）](https://docs.typesafe.ai/cookbooks/llm_guardrails) | 公式 Docs | LLM の入力と出力を Jev で検査するガードレールの実装例です。review 閾値 0.35、action 閾値 0.70／0.85 の二段構えで判定します。 | スニペットのみ |
| 6 | [API reference](https://docs.typesafe.ai/api) | 公式 Docs | HTTP API の仕様です。直接 API は OpenAI 互換ではない点に注意してください。 | スニペットのみ |
| 7 | [typesafe-sdk（PyPI）](https://pypi.org/project/typesafe-sdk/) | 公式パッケージ | 公式 Python SDK です。調査時点の最新は 0.7.2（2026-09-26）。Python 3.10 以上、MIT ライセンス、HTTP/2 用の extra があります。 | 本文確認済 |
| 8 | [typesafe-ai/typesafe-sdk-python（GitHub）](https://github.com/typesafe-ai/typesafe-sdk-python) | 公式リポジトリ | README に `TypeSafeClient().system_one(state=..., questions=...)` でチケットを Choice 分類するクイックスタートがあります。認証は環境変数 `TYPESAFE_API_KEY` です。 | 本文確認済 |
| 9 | [Jev on OpenRouter（ガイド）](https://openrouter.ai/docs/guides/community/jev) | 提供元ドキュメント | OpenRouter 経由で呼ぶ方法です。decisions エンドポイントを使い、出力トークンは無料、入力トークンは従量課金です。TypeSafe の直接 API とスキーマが異なる点に注意してください。 | スニペットのみ |
| 10 | [Jev Latest（OpenRouter モデルページ）](https://openrouter.ai/~typesafe/jev-latest) | 提供元ページ | `jev-latest` は Jev ファミリーの最新版を指すエイリアスで、調査時点では 1.13 でした。コンテキスト長は 32k です。価格表示はページによって食い違いがあるため、利用時に確認してください。 | スニペットのみ |
| 11 | [Jev (typesafe)（Cloudflare AI docs）](https://developers.cloudflare.com/ai/models/typesafe/jev/) | 提供元ドキュメント | Workers AI では `env.AI.run('typesafe/jev', { state, questions })` で呼べます。コンテキスト長 32k、データ保持なし（zero data retention）、入力 $0.042/1M トークンと記載されています。 | スニペットのみ |

---

## 日本語の解説

| # | リンク | 種別 | 内容 | 確認方法・注意 |
|---|---|---|---|---|
| 1 | [高速判断に特化したAI - TypeSafe「Jev」と System One Model（npaka, note）](https://note.com/npaka/n/n6f8dd30a5fa4?hl=en) | 個人ブログ | System One Model の考え方と Jev の基本を日本語で整理した記事です。チーム内で共有済みの記事です。 | スニペットのみ。検索で見つかった URL に英語表示の `?hl=en` が付いています |
| 2 | [Jev はAIエージェントのハーネスをどう変えるか（npaka, note）](https://note.com/npaka/n/ne4547ea3c6f5?hl=en) | 個人ブログ | 同じ著者による続編で、エージェントの制御部分（ハーネス）に Jev を組み込む視点で書かれています。 | スニペットのみ。タイトルは英語表示から訳したものです |
| 3 | [今話題のAI「Jev」って何？ 宇宙最速で学ぶ会（minorun365, Speaker Deck）](https://speakerdeck.com/minorun365/konwadai-no-ai-jev-tte-nani-uchuu-saisoku-de-manabu-kai) | 登壇資料 | 勉強会のスライドです。Choice・Score・Noul の違い、苦手なこと（数を数える、日付の前後比較）、計算はコード側に任せる使い方がまとまっています。 | スニペットのみ |
| 4 | [Jevとは何か？ 従来型LLMやAIエージェントとの違いを理解する（nasuvitz, Qiita）](https://qiita.com/nasuvitz/items/44f20ed515b9734afb26) | 個人ブログ（AWS Ambassador） | Jev をルーティング用の部品として位置づけ、従来の LLM やエージェント基盤との役割の違いを整理しています。 | スニペットのみ。**共有時のタイトル「jevって何だろう」では見つかりませんでした**。同じ著者の Jev 解説記事はこれなので、該当記事かどうか確認してください |
| 5 | [メモ: System One Model / Jev （typesafe.ai）（kun432, Zenn スクラップ）](https://zenn.dev/kun432/scraps/7d699847974237) | 個人スクラップ | Playground、API、Python SDK を実際に触ったメモです。「本質は分類で、既存モデルでもかなりできるのでは」という冷静な見方もあります。 | スニペットのみ |
| 6 | [Jev（TypeSafe AI）とは ― 文字列ではなく「型付きの判定」を返す System One モデルの仕組み（Qiita）](https://qiita.com/y-morimatsu/items/b396064bf6f3d84ca200) | 個人ブログ | 「型付きの判定」を返す仕組みに絞った解説です。 | スニペットのみ |

---

## 実装・ハンズオン

| # | リンク | 種別 | 内容 | 確認方法 |
|---|---|---|---|---|
| 1 | [判断特化AI「Jev」入門──チケット振り分け・ガードレール実践例（Zenn, GIXo）](https://zenn.dev/gixo/articles/typesafe-jev-system-one-ai) | 企業技術ブログ | 問い合わせチケットの振り分けとガードレールの実装例です。社内の問い合わせ対応に応用しやすい内容です。 | スニペットのみ |
| 2 | [文章を書かない AI「Jev」を触って分かった、判定だけを返す API の使いどころ（Zenn, FLINTERS）](https://zenn.dev/flinters_blog/articles/466c8de3de417d) | 企業技術ブログ | 実際に試したうえでの、向いている用途と向いていない用途の整理です。 | スニペットのみ |
| 3 | [話題のJevを触ってみました。特徴、料金、活用事例など。（Zenn, GMO メディア）](https://zenn.dev/gmomedia/articles/2026-09-25-typesafe-jev) | 企業技術ブログ | 特徴、料金、活用事例を一通りまとめています。ベンダーの社内ベンチマーク（711 件で 67.8%、最良の比較モデルは 74.1%）と、公式が挙げる苦手分野も紹介しています。 | スニペットのみ |
| 4 | [約0.2秒で文章を判定するTypeSafe AIのJevを試してみる（Qiita）](https://qiita.com/hideki/items/895d9ef3a5adda972d47) | 個人ブログ | Python から呼び出してレイテンシを体感するハンズオンです。 | スニペットのみ |
| 5 | [選ぶ・採点する・確率を返す — Jevの使いどころ入門（Speaker Deck）](https://speakerdeck.com/hisuzuya/erabu-saiten-suru-kakuritsu-o-kaesu-jev-no-tsukaidokoro-nyuumon) | 登壇資料 | Choice・Score・確率の3つの観点から、使いどころを入門向けに整理しています。 | スニペットのみ |

---

## 関連する型安全な判断の技術・ツール

Jev は「決められた選択肢から選び、その確率を返す」専用モデルです。以下のツールは「LLM に型どおりの出力を書かせる」系統と、「判定や評価に特化する」系統に分かれます。

| # | リンク | 種別 | Jev との関係・違い | 確認方法 |
|---|---|---|---|---|
| 1 | [Introducing Structured Outputs in the API（OpenAI, 2024-08）](https://openai.com/index/introducing-structured-outputs-in-the-api/) | 公式 | JSON Schema に沿った出力を保証する機能です。スキーマに合っていることは保証されますが、中身が正しいかは別の話で、確率分布も返しません。Jev は1回の並列処理で選択肢ごとの確率を返す点が違います。 | スニペットのみ |
| 2 | [Structured outputs（Claude Platform Docs）](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | 公式 Docs | Claude の JSON 出力（`output_config.format`）と strict tool use です。要約や理由の説明など、文章も含めて返したい場合は LLM 側でこの機能を使うのが基本です。 | スニペットのみ |
| 3 | [Instructor（GitHub: 567-labs/instructor）](https://github.com/567-labs/instructor) | OSS | Pydantic モデルで LLM の出力を検証し、失敗したら再試行するライブラリです。対応プロバイダが多く、抽出タスク向きです。ただし再試行の分だけコストと遅延が増えるため、大量・高頻度の判断には Jev のような専用モデルの方が向く場合があります。 | 本文確認済 |
| 4 | [Outlines（GitHub: dottxt-ai/outlines）](https://github.com/dottxt-ai/outlines) | OSS | トークン生成の段階で出力を型・正規表現・文法に制約します（制約付きデコーディング）。ローカルモデルでも使えます。社外にデータを出せない場面では、Jev（クラウド API）の代わりになりえます。 | 本文確認済 |
| 5 | [Why BAML?（BoundaryML Docs）](https://docs.boundaryml.com/guide/introduction/why-baml) | 公式 Docs | 型付きのプロンプト関数を定義する DSL と、崩れた出力をスキーマに合わせて直すパーサー（SAP）です。ベンチマークは**ベンダー公表値**です。 | スニペットのみ |
| 6 | [Output（Pydantic AI Docs）](https://ai.pydantic.dev/output) | 公式 Docs | エージェントの出力型を `output_type` で指定する仕組みです。エージェントの中の分岐を LLM に任せるか、Jev に任せるかを比べる材料になります。 | スニペットのみ |
| 7 | [Llama Guard: LLM-based Input-Output Safeguard（arXiv:2312.06674）](https://arxiv.org/abs/2312.06674v1) | 論文（Meta） | 安全性の分類基準（タクソノミー）を入力として渡し、safe/unsafe を判定するガードレール分類器です。Jev のガードレール用途と比べる基準になります。重みが公開されていて手元で動かせる点が違います。 | スニペットのみ |
| 8 | [On Calibration of Modern Neural Networks（Guo et al., ICML 2017）](https://proceedings.mlr.press/v70/guo17a.html) | 論文 | 「確信度が実際の正答率と合っているか」という較正の古典的な論文で、温度スケーリングを提案しています。Jev の売りである「較正された確率」を評価するときの基礎知識です。 | スニペットのみ |
| 9 | [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena（arXiv:2306.05685）](https://arxiv.org/html/2306.05685v4) | 論文 | LLM に評価させる手法と、そのバイアス（回答の位置、冗長さ、自己贔屓）を分析しています。Score 型の質問で「採点」させる前に読んでおくと、同じ落とし穴に気づけます。 | スニペットのみ |
| 10 | [Introducing Clef: our open-source decision models（Cloudflare Blog）](https://blog.cloudflare.com/clef-decision-models/) | 公式（Cloudflare） | Cloudflare 自社の判断モデルです（Apache 2.0、Jev API 互換、2026-10-01）。Cloudflare は Jev より速く、TypeSafe の評価4領域のうち3つで上回ると主張しています（**ベンダー公表値**）。Jev への依存を避ける選択肢になります。 | スニペットのみ |

---

## 批判的な視点・限界

| # | リンク | 種別 | 要点 | 確認方法 |
|---|---|---|---|---|
| 1 | [jev-benchmarks（GitHub: AbdelStark）](https://github.com/AbdelStark/jev-benchmarks) | OSS・独立評価 | Jev と GLiNER2.5 を、正解率だけでなく較正・選択的リスク・レイテンシで比較しています。AG News と Banking77 では Jev が優勢でした。一方 DAIR Emotion では較正が悪く、正解ラベルに確率 0 を付けた例が 16% ありました。300 件のパイロット評価で、作者自身も結果は「意図的に混在」と書いています。 | 本文確認済 |
| 2 | [Evaluating and Benchmarking the System One Model Jev（arXiv:2609.37647）](https://arxiv.org/html/2609.37647v1) | 論文（プレプリント、査読前） | 22 データセットでの評価です。較正のずれはほぼ過信の方向で、正解率の低いタスクほど悪化すると報告しています。 | スニペットのみ |
| 3 | [Jev in Medicine: A Benchmark Evaluation. Preliminary results.（arXiv:2609.34024）](https://arxiv.org/html/2609.34024v1) | 論文（プレプリント、査読前） | 医療の設問での評価です。較正が良いセットがある一方、識別力が低いセットもあり、「分からない」を選ぶべき場面でほとんど選びませんでした。臨床で使う前にはタスクごとの検証が必要と結論づけています。福祉・医療に隣接する業務への示唆があります。 | スニペットのみ |
| 4 | [Jev After Eight Days of Independent Tests（DEV Community, AWS Builders）](https://dev.to/aws-builders/jev-after-eight-days-of-independent-tests-level-with-mid-price-llms-behind-the-frontier-1c60) | 個人ブログ | 公開後8日間の独立評価のまとめです。精度は中価格帯の LLM と同程度で、フロンティアモデルより 6.5〜11.5 ポイント低い結果でした。少量のラベル付きデータで温度を合わせるだけで、較正のずれの多くが直るとしています。 | スニペットのみ |
| 5 | [AWSの最軽量LLM「Amazon Nova Micro」がJevの代わりとなるか検証してみた（nasuvitz, Qiita）](https://qiita.com/nasuvitz/items/4d27833640ff36b5d8c5) | 個人ブログ | 意図分類（93.4%）と返金要求（91.2%）では両モデルの判定がよく一致しましたが、苛立ち度の判定は 29.7% しか一致しませんでした。主観的な Score 型の判定は、モデルによって結果が大きく変わることを示しています。 | スニペットのみ |

**共通する注意点**

- 「ハルシネーションしない」は「スキーマ外の値を返さない」という意味で、「常に正しい」という意味ではありません。
- 公表されている速度・コスト倍率は、TypeSafe が自社で作ったワークフローでの評価です。
- 自社のデータに少数のラベルを付けて、確信度と正解率の関係（較正）を確かめてから閾値を決めてください。
- クラウド API のため、個人情報や要配慮情報を送る前にデータ保持の条件を確認してください（Cloudflare 経由ではデータ保持なしと記載されています）。

---

## 避けた方がよいもの

検索では「Jev」というキーワードで上位を狙ったまとめサイトや非公式サイトが多数ヒットしました。一次情報との突き合わせができないため、リンクは載せていません。

- 非公式の「Jev セットアップ」「API アクセス」「ウェイトリストを抜ける方法」系のページ（例: openclawdatabase.com、opentweet.io の Jev 関連ページ、aisuccesslabjuliangoldie.com）
- ルーター事業者や AI ツール紹介サイトによる量産型の解説（例: orcarouter.ai の Jev 記事群、多言語で同じ内容を出しているニュースサイト）
- 「Jev で○○を自動化」系で、出典のない事例を並べるサイト

また、Jev の性能を「193 倍速い」などの見出しで紹介するメディア記事は、多くの場合ベンダーの公表値をそのまま転載しています。数値を引用するときは、出典が TypeSafe 自身であることを明記してください。
