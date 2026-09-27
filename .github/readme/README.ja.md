<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>コーディングエージェントのための、較正された確信度つきの型付き判断。</em><br>
  <em>150 を超えるコミュニティプロジェクトの先行事例を、形ごとに整理。</em>
</p>

<p align="center">
  <a href="../../LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href="../workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">LinkedIn でつながりましょう！</a>
</p>

<p align="center">
  <a href="../../README.md">English</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <strong>日本語</strong> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.it.md">Italiano</a>
</p>

> [!NOTE]
> これは非公式のコミュニティ製スキルです。TypeSafe AI が作成、レビュー、推奨したものではありません。TypeSafe は独自のスキルを [typesafe-ai/skills](https://github.com/typesafe-ai/skills) で公開しています。[公式スキルとの違い](#公式スキルとの違い) も参照してください。

コーディングエージェントは、Jev をチャットモデルの 1 つとして扱います。このスキルは、Jev に合わせた設計をエージェントに教えます。型付きの質問、較正された確信度、そして仕組みごとに整理した 150 を超えるコミュニティプロジェクトのライブラリです。Claude Code、Codex、Antigravity CLI にインストールできます。

[Jev](https://docs.typesafe.ai/introduction) は [System One](https://docs.typesafe.ai/concepts/system-one) モデルです。文章は書きません。コンテンツと型付きの質問のセットを送ると、Jev は各質問に値と較正された確率で答えます。通常は 100〜200 ms で返ります。

- **Choice** は、リストから選択肢を 1 つ選びます。例: チケットを請求、配送、サポートのいずれかに振り分けます。
- **Score** は、説明した尺度の上にコンテンツを位置づけます。例: プルリクエストを「仕様を無視している」から「仕様を満たしている」までの尺度で評価します。
- **Noul** は、はい/いいえで答える文が正しい確率を返します。例: 「このシェルコマンドはプロジェクト外のファイルを削除する」。

## インストール

<details>
<summary><strong>Claude Code</strong></summary>

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

Jev のコードを扱うと、スキルは自動で読み込まれます。手動で読み込むには、次のように入力します。

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
codex plugin add building-with-typesafe-jev@building-with-typesafe-jev
```

新しいスレッドを始めます。タスクが合えば、Codex がスキルを読み込みます。手動で読み込むには、次のように入力します。

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

インストールされたか確認します。

```bash
agy plugin list
```

新しいセッションを始めます。Antigravity CLI はタスクに合うときにスキルを読み込みます。手動で読み込むには、次のように入力します。

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Gemini CLI から移行しましたか？ `agy plugin import gemini` でこの拡張機能を移した場合も、上のインストールコマンドを実行してください。インポートしたコピーが最新のものに置き換わります。

</details>

<details>
<summary><strong>SKILL.md を読むその他のエージェント</strong></summary>

`skills/building-with-typesafe-jev/` フォルダを、エージェントのスキルフォルダにコピーします。フォルダは丸ごと残してください。`SKILL.md` は隣にあるファイルへリンクしています。

</details>

## API キーを設定する (任意、推奨)

このスキルはキーがなくても動きます。エージェントのシェルで `TYPESAFE_API_KEY` が設定されていれば、コードがプロジェクトに入る前に、エージェントが実際の API で設計を確認できます。これで、フィールド名の間違いや、Jev が意図と違う意味に読む質問を見つけられます。1 回の呼び出しは 1 セントにも満たない額です。

<details>
<summary><strong>キーを作成、保存、トラブルシューティングする</strong></summary>

<br>

<details>
<summary><strong>キーを作成する</strong> (TypeSafe コンソールでの 4 ステップ)</summary>

**ステップ 1.** [console.typesafe.ai](https://console.typesafe.ai/) にサインインし、サイドバーの **API Keys** を開きます。

<img src="../assets/api-key/step-1.png" alt="TypeSafe コンソールのホームページ。琥珀色の枠と矢印が、左サイドバーの API Keys を指しています。" width="100%">

**ステップ 2.** 右上の **Create key** をクリックします。

<img src="../assets/api-key/step-2.png" alt="API キーのページ。既存のキーはぼかされています。琥珀色の枠と矢印が、右上の Create key ボタンを指しています。" width="100%">

**ステップ 3.** マシン名やエージェント名など、キーを置く場所にちなんだ名前を付けます。続けて **Create key** をクリックします。

<img src="../assets/api-key/step-3.png" alt="Create API key ダイアログ。名前欄に my-coding-agent と入力されています。琥珀色の枠と矢印が、名前欄と Create key ボタンを指しています。" width="100%">

**ステップ 4.** 今すぐキーをコピーしてください。コンソールがキーを表示するのは 1 回だけです。なくした場合は新しいキーを作成し、古いキーを無効化します。

<img src="../assets/api-key/step-4.png" alt="API key created ダイアログ。キーの値は伏せられています。琥珀色の枠と矢印が、Copy ボタンを指しています。" width="100%">

</details>

<details>
<summary><strong>キーを保存する</strong> (macOS, Linux, Windows)</summary>

キーは、自分だけが読める専用のファイルに保存し、`TYPESAFE_API_KEY` としてエクスポートします。エージェントはターミナルなしでシェルを起動することが多いため、各セクションではそうしたシェルからも見える場所にキーを置きます。お使いのシステムを選んでください。

<details>
<summary><strong>macOS</strong> (zsh、デフォルトのシェル)</summary>

キーを非公開のファイルに保存します。

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

`~/.zshenv` から読み込みます。エージェントがターミナルなしで起動するシェルも含め、すべての zsh がこのファイルを読みます。`~/.zshrc` を読むのは対話シェルだけです。

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

新しいターミナルを開いて確認します。このコマンドはキーそのものではなく、キーの長さを表示します。

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux で bash</strong> (Ubuntu, Debian, Mint, Fedora, Arch)</summary>

キーを非公開のファイルに保存します。

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

`~/.bashrc` の**先頭**から読み込みます。Ubuntu、Debian、Mint、Arch の `~/.bashrc` は、ターミナルがつながっていないときに早めに処理を止める行で始まります。この判定より下の行は、エージェントのシェルでは実行されません。ファイルの先頭なら、どのディストリビューションでも安全です。

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

新しいターミナルを開いて確認します。

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux で zsh</strong></summary>

macOS の手順に従ってください。Linux でも zsh は同じように `~/.zshenv` を読みます。

</details>

<details>
<summary><strong>Linux で fish</strong></summary>

fish は、ターミナルの有無にかかわらず `~/.config/fish/conf.d/` 内のすべてのファイルを読みます。

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong> (PowerShell)</summary>

キーをユーザー環境変数として保存します。新しく開くターミナルやアプリからは見えますが、すでに開いているターミナルからは見えません。

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

新しいターミナルを開いて確認します。

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL:** 既定では、Windows の変数は WSL に届きません。WSL の中では、Linux で bash の手順に従ってください。

</details>

<details>
<summary><strong>デスクトップアプリと IDE 拡張機能</strong></summary>

Dock、スタートメニュー、デスクトップのランチャーから起動したアプリは、シェルのファイルを読みません。

- **Windows:** 上で設定したユーザー環境変数が、これらのアプリにもすでに有効です。
- **Linux (systemd):** `~/.config/environment.d/typesafe.conf` に `TYPESAFE_API_KEY=YOUR_KEY` という行を追加し、ログアウトしてから再度ログインします。
- **macOS:** アプリをターミナルから起動するか、アプリ自体の設定で変数を設定します。macOS には、デスクトップアプリが読むユーザーごとの簡単なファイルがありません。

</details>

</details>

<details>
<summary><strong>エージェントからキーが見えない場合</strong></summary>

エージェントに `echo ${#TYPESAFE_API_KEY}` (Windows では `$env:TYPESAFE_API_KEY.Length`) を実行させます。`0` と表示されるか何も表示されない場合は、次の順に確認してください。

- **キーを保存する前にエージェントを起動した。** エージェントのシェルは、起動したプログラムの環境をコピーします。エージェントを終了し、新しいターミナルから起動してください。
- **Dock、スタートメニュー、IDE からエージェントを起動した。** これらのアプリはシェルのファイルを読みません。上の「デスクトップアプリと IDE 拡張機能」を参照してください。
- **Codex が環境をフィルタしている。** `~/.codex/config.toml` の `[shell_environment_policy]` で `include_only` が設定されている場合は、そこに `TYPESAFE_API_KEY` を追加します。`ignore_default_excludes = false` が設定されている場合、Codex は名前に `KEY` を含む変数をすべて取り除きます。その行を削除してください。
- **WSL.** Windows の変数は WSL に届きません。WSL の中で、Linux の手順に従ってキーを保存してください。

</details>

</details>

## テストの方法

コーディングエージェントに Jev のタスクを 6 つ与えました。サポートチケットの振り分け関数や、シェルコマンドの承認ゲートなどです。各タスクを、このスキルあり、スキルなし、公式スキルありでそれぞれ 10 回実行し、各条件はそれぞれ専用の隔離されたコンテナで動かしました。エージェントはドキュメントを持っていましたが API キーは持っていなかったので、採点者はエージェントが書いたコードを確認しました。判断が必要なチェックは、3 つのプロバイダーの 3 つの LLM 採点者 (Claude Opus、GPT-6 Sol、Kimi K3) に送り、多数決で決めました。

| | スキルなし | このスキル | 公式スキル |
|---|---:|---:|---:|
| 平均スコア | 0.65 ± 0.05 | **0.96 ± 0.02** | 0.77 ± 0.04 |

スコアは合格したチェックの割合で、タスクごとに 10 回の実行で平均したものです。

**このスキルが差を生んだところ** (10 回中の合格した実行の数):

| エージェントのコードは… | スキルなし | このスキル | 公式スキル |
|---|---:|---:|---:|
| Jev に数を尋ねず、コードで数えた | 1 | 8 | 0 |
| 質問の中で入力のフィールドを名指しした | 0 | 10 | 1 |
| Jev のモデルのバージョンを固定または記録した | 0 | 10 | 0 |
| 部署のリストにその他の選択肢を加えた | 3 | 10 | 6 |
| 1,200 のカテゴリをたどる間、複数の経路を保った | 1 | 10 | 7 |
| 破壊的なコマンドに対するコードの安全策を残した | 7 | 10 | 2 |
| `score` を 0 から n-1 までの位置として読んだ | 9 | 10 | 5 |

[すべてのチェックを見る →](../../evals/docs/results.md#every-check)

これらの行はどれも、95% の検定で、スキルなし、公式スキル、またはその両方を偶然とは言えない差で上回っています。

**詳しくは:**

- [evals/README.md](../../evals/README.md): ケースごとの結果と、スイートの実行方法
- [evals/docs/results.md](../../evals/docs/results.md): すべてのチェック、各採点者のスコア、コスト、トークン、手法
- [evals/docs/cases.md](../../evals/docs/cases.md): 6 つのタスクと、各チェックが見ているもの
- [evals/docs/harness.md](../../evals/docs/harness.md): 実行の仕組み、隔離されたコンテナ、バッチを保存する方法
- [evals/docs/lessons.md](../../evals/docs/lessons.md): スイートを作る途中で壊れたこと

## 中身

スキルは層に分けて読み込まれます。エージェントはタスクに必要な部分だけを読みます。

| ファイル | 内容 | エージェントが読むタイミング |
|---|---|---|
| `SKILL.md` | どのプリミティブを選ぶか、11 の設計ルール、確率と確信度の使い方、よくある間違い | Jev のタスクのたび |
| `api-reference.md` | HTTP API、Python と JavaScript の SDK、制限、エラー、環境変数 | コードを書くとき |
| `patterns.md` | 4 つの公式パターンと 18 のクックブックのテクニック、そのしきい値 | ワークフローを設計するとき |
| `prior-art/INDEX.md` | 「作りたいもの」から形への地図と、失敗したアイデア | 新しいものを設計する前 |
| `prior-art/*.md` | 11 の形のファイル。コードのスケッチ、現場の教訓、リンク付きのプロジェクト | 1 つの設計につき 1〜2 個 |

先行事例ライブラリは、プロジェクトを業界ではなく仕組みで分類します。ゲームのボット、ドローン、トレーディングボットはどれも**制御ループ**なので、1 つのスケッチと 1 組の教訓を共有します。ほかの形は、候補から選ぶ、ゲート、ストリームフィルタ、ランキングとマッチング、ジャッジと評価、逐次処理とリアルタイム、エージェントのコンテキストとメモリ、LLM との組み合わせ、データとしての答え、インフラへの組み込みです。インデックスには、現場で失敗したアイデアも載っています。

## 公式スキルとの違い

[TypeSafe の公式スキル](https://github.com/typesafe-ai/skills) は短く、エージェントを最新のドキュメントへ誘導します。現在の API の詳細を知るには、それが正しい情報源です。両方をインストールすることもできます。

このスキルは、スキル自体により多くを持っています。正確な API の形、クックブックのしきい値、コミュニティで見つかった失敗パターン、そして先行事例ライブラリです。エージェントはネットワークの往復なしで設計でき、他の人が先に作ったものを見られます。

Jev は速く変わります。このスキルは、2026-09-25 時点の [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) とコミュニティのスナップショットで、食い違いがあれば最新のドキュメントが優先されるとエージェントに伝えます。事実が間違っていたら、出典へのリンクを添えて issue を開いてください。

## クレジット

API に関する事実は、TypeSafe AI の公開ドキュメントとクックブックに基づいています。先行事例は、プロジェクトを公開した作り手、Hacker News のコミュニティ、そして次のインデックスから集めました。[awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe)、[JevDirectory](https://www.jevdirectory.org/resources)、[awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases)、[awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)。各形のファイルは、元のプロジェクトにリンクしています。

TypeSafe、Jev、System One は TypeSafe AI の名称です。このプロジェクトは、スキルの用途を示すためだけにこれらを使っています。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。
