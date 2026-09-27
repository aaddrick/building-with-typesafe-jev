<p align="center">
  <img src="../assets/hero.png" alt="Building with TypeSafe Jev: コーディングエージェントのための、較正された確信度つきの型付き判断。150 を超えるコミュニティプロジェクトの先行事例を、形ごとに整理。2 枚のパネル。左では、Structured Outputs を使う LLM が有効な JSON を返す。department: billing、severity: medium、refund: false (赤字)、確信度 0.95。ただしこの確信度は生成されたもので、較正されていない。右では、1 回の Jev 呼び出しが 3 つの型付きの答えを返す。Choice (department: billing、確信度 0.88)、Score (severity: 2 のうち 1.43)、Noul (refund: 0.99)。" width="100%">
</p>

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

## インストール

<details>
<summary><strong>Claude Code</strong></summary>

ターミナルで次の 2 つのコマンドを実行します。

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

インストール時に、プラグインのオプションがまだ設定されていないと表示されることがあります。これはライブテストのことで、有効にするまではオフのままです。[API キーを設定する](#api-キーを設定する-任意推奨) を参照してください。

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

Gemini CLI から移行しましたか？ `agy plugin import gemini` でこの拡張機能を移した場合も、上のインストールコマンドを実行してください。インポートしたコピーが置き換わります。そのコピーの設定コマンドは Antigravity CLI では動きません。

</details>

<details>
<summary><strong>SKILL.md を読むその他のエージェント</strong></summary>

`skills/building-with-typesafe-jev/` フォルダを、エージェントのスキルフォルダにコピーします。フォルダは丸ごと残してください。`SKILL.md` は隣にあるファイルへリンクしています。

</details>

## API キーを設定する (任意、推奨)

このスキルはキーがなくても動きます。その場合も、プリミティブを選び、質問とコードを書き、API リファレンスと照らし合わせて確認します。キーがあれば、コードがプロジェクトに入る前に、実際の API 呼び出しで各設計を試すこともできます。これで、フィールド名の間違いや、Jev が意図と違う意味に読む質問を見つけられます。1 回の呼び出しは 1 セントにも満たない額なので、キーの用意を強くおすすめします。

ライブテストは、有効にするまでオフです。オフの間、スキルはキーを探しません。オンにすると、指定した環境変数 (別の名前を選ばない限り `TYPESAFE_API_KEY`) からだけキーを読み、最初の呼び出しの前にそれを伝え、テスト呼び出しを 1 タスクあたり約 10 回に抑えます。手順は 3 つです。キーを作成し、保存し、ライブテストを有効にします。

<details>
<summary><strong>キーを作成する</strong> (TypeSafe コンソールでの 4 ステップ)</summary>

**ステップ 1.** [console.typesafe.ai](https://console.typesafe.ai/) にサインインし、サイドバーの **API Keys** を開きます。

<img src="../assets/api-key/step-1.png" alt="TypeSafe コンソールのホームページ。琥珀色の枠と矢印が、左サイドバーの API Keys を指しています。" width="100%">

**ステップ 2.** 右上の **Create key** (キーを作成) をクリックします。

<img src="../assets/api-key/step-2.png" alt="API キーのページ。既存のキーはぼかされています。琥珀色の枠と矢印が、右上の Create key ボタンを指しています。" width="100%">

**ステップ 3.** マシン名やエージェント名など、キーを置く場所にちなんだ名前を付けます。続けて **Create key** をクリックします。

<img src="../assets/api-key/step-3.png" alt="Create API key ダイアログ。名前欄に my-coding-agent と入力されています。琥珀色の枠と矢印が、名前欄と Create key ボタンを指しています。" width="100%">

**ステップ 4.** 今すぐキーをコピーしてください。コンソールがキーを表示するのは 1 回だけです。なくした場合は新しいキーを作成し、古いキーを無効化します。

<img src="../assets/api-key/step-4.png" alt="API key created ダイアログ。キーの値は伏せられています。琥珀色の枠と矢印が、Copy ボタンを指しています。" width="100%">

</details>

<details>
<summary><strong>キーを保存する</strong> (macOS, Linux, Windows)</summary>

キーは、自分だけが読める専用のファイルに保存します。スキルはキーをファイルからではなく環境変数から読むので、エージェントが起動するシェルでその変数が設定されている必要があります。エージェントはターミナルなしでシェルを起動することが多いため、各セクションではそうしたシェルからも見える場所にキーを置きます。お使いのシステムを選んでください。

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
<summary><strong>ライブテストを有効にする</strong> (Claude Code, Codex, Antigravity CLI)</summary>

各エージェントは 2 つの設定を持ちます。ライブテスト (`on` または `off`、デフォルトは `off`) と、キーを保持する変数の名前 (デフォルトは `TYPESAFE_API_KEY`) です。一度設定すれば、次のセッションから有効になります。補助スクリプトには Python 3 が必要です。Codex 用のものは 3.11 以降が必要です。

**Claude Code.** ターミナルで次を実行します。

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev --config live_testing=on
```

キーが別の名前の変数に入っている場合は、`--config key_env_var=YOUR_VARIABLE` を追加します。セッション内では、`/plugin configure building-with-typesafe-jev@building-with-typesafe-jev` で同じ設定を変更できます。

**Codex.** Codex にはプラグインの設定がないため、スキルは設定を `~/.codex/config.toml` に保存します。Codex は、エージェントが起動するすべてのシェルにこの設定を渡します。セッション内で次のように入力します。

```
$building-with-typesafe-jev:jev-settings live on
```

Codex が書き込みの承認を求めます。手動で変更するには、`~/.codex/config.toml` に次の行を追加します。

```toml
[shell_environment_policy.set]
JEV_LIVE_TESTING = "on"
JEV_KEY_ENV_VAR = "TYPESAFE_API_KEY"
```

Codex では、プラグインのセッション開始フックを一度だけ信頼する必要もあります。このフックは各セッションの開始時に、ライブテストがオンかどうかと、キーの変数が設定されているかどうかをエージェントに伝えます。キーそのものは伝えません。セッション内で `/hooks` と入力し、フックを信頼してください。更新でフックが変わると、Codex は再び確認を求めます。信頼するまでフックは実行されませんが、スキルは引き続き自分で設定を確認します。

**Antigravity CLI.** Antigravity CLI にはプラグインの設定がありません。ただし、エージェントのシェルは `agy` を起動したターミナルの環境を引き継ぎます。そのため、設定は 2 つの環境変数で、キーを保存した場所に書きます。キーが `~/.config/typesafe/env` にあるなら、次を実行してから、新しいターミナルを開いて `agy` を再起動します。

```bash
echo 'export JEV_LIVE_TESTING=on' >> ~/.config/typesafe/env
```

キーが別の名前の変数にある場合は、同じ方法で `export JEV_KEY_ENV_VAR=YOUR_VARIABLE` を追加します。fish や Windows では、キーを保存したのと同じ方法で `JEV_LIVE_TESTING` を `on` に設定します。

**確認する.** 新しいセッションを始めて、設定コマンドを実行します。Claude Code では `/building-with-typesafe-jev:jev-settings`、Codex では `$building-with-typesafe-jev:jev-settings`、Antigravity CLI では `/building-with-typesafe-jev:jev-settings` です。両方の設定と、エージェントのシェルからキーが見えるかどうかを表示します。表示するのはキーの長さで、キーそのものは表示しません。

**CI とコンテナ.** 環境変数 `JEV_LIVE_TESTING` と `JEV_KEY_ENV_VAR` は、どのエージェントでも保存された設定より優先されます。

</details>

<details>
<summary><strong>エージェントからキーが見えない場合</strong></summary>

エージェントのシェルにその変数がないと、設定コマンドは `key: not set in this shell` と表示します。次の順に確認してください。

- **キーを保存する前にエージェントを起動した。** エージェントのシェルは、起動したプログラムの環境をコピーします。エージェントを終了し、新しいターミナルから起動してください。
- **Dock、スタートメニュー、IDE からエージェントを起動した。** これらのアプリはシェルのファイルを読みません。上の「デスクトップアプリと IDE 拡張機能」を参照してください。
- **Codex が環境をフィルタしている。** `~/.codex/config.toml` の `[shell_environment_policy]` で `include_only` が設定されている場合は、キーの変数、`JEV_LIVE_TESTING`、`JEV_KEY_ENV_VAR` をそこに追加します。`ignore_default_excludes = false` が設定されている場合、Codex は名前に `KEY` を含む変数をすべて取り除きます。その行を削除してください。
- **WSL.** Windows の変数は WSL に届きません。WSL の中で、Linux の手順に従ってキーを保存してください。

</details>

このスキルはキーを表示、記録、ハードコードしません。指定した変数だけを読み、キーをコマンドラインに載せずに各テストコマンドへ渡します。

## 何をするのか

LLM は JSON を返せます。Structured Outputs を使えば、その JSON は毎回パースできます。それでも中身は間違うことがあり、どのくらいの頻度で間違うのかは出力のどこにも表れません。スキーマが固定するのは答えの形であって、答えそのものではありません。department フィールドは、モデルが知っていても当て推量でも "billing" と書かれます。確信度のフィールドを足しても、モデルはその数値を答えと同じように書くだけです。その数値は何とも較正されていません。

[Jev](https://docs.typesafe.ai/introduction) は TypeSafe AI の [System One](https://docs.typesafe.ai/concepts/system-one) モデルです。文章は書きません。確率はデコーダーからサンプリングしたものではなく、結果に対して最適化されています。ほとんどのクエリは 100〜200 ms で返ります。サポートチケットなどのコンテンツと、質問のセットを送ります。Jev は各質問に、型付きの値と較正された確率で答えます。パースするテキストはありません。質問の型は次の 3 種類のいずれかです。

- **Choice** は、指定したリストから選択肢を 1 つ選びます。例: エージェントの次の一手を、ドキュメントを検索する、テストを実行する、ユーザーに尋ねる、の中から選びます。LLM を介さないツールルーティングです。
- **Score** は、段階ごとに説明した尺度の上にコンテンツを位置づけます。例: エージェントのプルリクエストを、仕様を無視している → 仕様を一部満たしている → 仕様を満たしている という尺度で評価します。結果は 1.6 で、仕様を満たす段階の近くまで来ています。
- **Noul** は、はい/いいえで答える文が正しい確率を返します。例: 「このシェルコマンドはプロジェクト外のファイルを削除する」は 0.97 と返り、承認ゲートがコマンドを実行前に止めます。

API リファレンスを読むのは簡単な部分です。難しいのは、文章を書かないモデルに合わせて設計することです。このスキルがないエージェントは、チュートリアルを 1 つ見つけ、残りの API を推測し、プロンプトを書いて出力をパースする習慣を、それを置き換えるために作られたモデルに持ち込みます。このスキルは、API、設計ルール、既知の失敗パターン、そして他の人がすでに作ったものの地図をエージェントに渡します。ドキュメントはモデルを説明します。スキルは、そのモデルに合わせた設計の仕方を示します。

## 何が変わるのか

コーディングエージェントに Jev のタスクを 6 つ与えました。サポートチケットの振り分け関数や、シェルコマンドの承認ゲートなどです。エージェントはドキュメントを持っていましたが API キーは持っていなかったので、採点者が確認したのは、そのコードが Jev に対して何をしたかではなく、エージェントが書いたコードそのものです。各タスクを 3 つの条件でそれぞれ 10 回実行し、すべてを 1 つの評価バッチでまとめて開始しました。

| | スキルなし | このスキル | 公式スキル |
|---|---:|---:|---:|
| 平均スコア | 0.65 | 0.96 | 0.77 |

スコアは、1 回の実行が合格したチェックの割合です。各平均の誤差は、95% の信頼度で 0.05 以内です。

### このスキルが差を生んだところ

以下は、合格回数に対する 95% の検定で、このスキルとスキルなしの差が偶然とは言えないほど大きいチェックです。各数値は、10 回中の合格した実行の数です。

| エージェントのコードは… | スキルなし | このスキル | 公式スキル |
|---|---:|---:|---:|
| Jev に数を尋ねず、コードで数えた | 1 | 8 | 0 |
| 質問の中で入力のフィールドを名指しした | 0 | 10 | 1 |
| Jev のモデルのバージョンを固定または記録した | 0 | 10 | 0 |
| 1,200 のカテゴリをたどる間、複数の経路を保った | 1 | 10 | 7 |
| 部署のリストにその他の選択肢を加えた | 3 | 10 | 6 |
| コマンドのゲートに複数のはい/いいえの質問をした | 5 | 10 | 9 |
| ルーブリックの項目ごとに 1 つの質問をし、評価はコードで計算した | 5 | 10 | 10 |

このうち 3 つのチェックはパターンマッチで採点します。残りの 4 つは、3 つのプロバイダーの 3 つの LLM 採点者、Claude Opus、GPT-6 Sol、Kimi K3 が採点し、多数決で決めます。エージェントは Claude のモデルなので、Claude の採点者だけで決まることはありません。

もう 1 つのチェックでも差がつきましたが、採点者 3 つのうち 2 つの判定によるものなので、表には入れていません。Opus と GPT-6 Sol では、このスキルはエージェント自身の理由でコマンドが承認されないようにできた実行が 10 回で、スキルなしでは 5 回でした。Kimi K3 は、そのスキルなしの 10 回のうち 9 回を合格としました。

### 公式スキルとの比較

同じ検定で、このスキルは 8 つのチェックで公式スキルより多く合格しました。そのうち 4 つは表にあります。数え上げ、フィールド名、モデルのバージョン、その他の選択肢です。残りの 4 つは次のとおりです。

- Jev の答えにかかわらず、破壊的なコマンドを止めるか人に回すコードのルールを残した: 10 回対 2 回
- 重大度の確率を整数のキーで読んだ: 10 回対 4 回
- `score` を 0 から n-1 までの位置として読んだ: 10 回対 5 回
- ログのラベル付けで、同時に送るリクエストを 8 以下に抑えた: 10 回対 6 回

### 差が出なかったところ

- `confidence` での振り分けは、このスキルありで 10 回中 2 回、スキルなしで 10 回中 2 回の合格でした。タスクには不確かなチケットをどこに回すかが書かれていなかったため、ほとんどのエージェントは信頼度の値を返し、判断を呼び出し側に任せました。コードが最善の選択肢を選ぶだけなら、それで問題ないとスキル自身も述べています。現在はタスクでフォールバック先を指定しており、次の評価バッチでそれを検証します。
- ほかのチェックはすべて、3 つの条件のどれでもほぼすべての実行で合格したか、差が偶然の範囲に収まりました。

すべてのチェックは [evals/docs/results.md](../../evals/docs/results.md) にあります。スイートの実行方法は [evals README](../../evals/README.md) にあります。

## 中身

スキルは層に分けて読み込まれます。エージェントはタスクに必要な部分だけを読みます。1 つの大きなファイルにすると、エージェントはコードを 1 行書く前から、タスクのたびにトークンと注意を費やすことになります。

| ファイル | 内容 | エージェントが読むタイミング |
|---|---|---|
| `SKILL.md` | どのプリミティブを選ぶか、11 の設計ルール、確率と確信度の使い方、答えが間違っているときの対処、よくある間違い | Jev のタスクのたび |
| `api-reference.md` | HTTP API、Python と JavaScript の SDK、制限、エラー、環境変数 | コードを書くとき |
| `patterns.md` | 4 つの公式パターンと 18 のクックブックのテクニック、そのしきい値 | ワークフローを設計するとき |
| `prior-art/INDEX.md` | 「作りたいもの」から形への地図と、失敗したアイデア | 新しいものを設計する前 |
| `prior-art/*.md` | 11 の形のファイル。コードのスケッチ、現場の教訓、リンク付きのプロジェクト | 1 つの設計につき 1〜2 個 |
| `scripts/jev_live.py` | ライブテストの設定を読み、キーを使ってテストコマンドを実行する | ライブのテスト呼び出しの前 |
| `../jev-settings/` | Claude Code、Codex、Antigravity CLI 用の設定コマンド | あなたが実行するとき |

## 先行事例ライブラリ

多くのカタログは、プロジェクトを業界で分類します。このライブラリは実装の形で分類します。ゲームのボット、ドローン、トレーディングボットは同じ形を共有します。制御ループです。こう分類すると、3 つは 1 つのコードスケッチと 1 組の現場の教訓を共有できます。11 の形は次のとおりです。

- **制御ループ**: ゲーム、ドローン、ロボット、市場。
- **候補から選ぶ**: ブラウザやスマートフォンのエージェント、LLM なしのツール呼び出し、抽出、ルーター。
- **ゲート**: ツール呼び出しの承認、「完了」チェック、CI、お金、コンテンツ。
- **ストリームフィルタ**: 低品質コンテンツのフィルタ、モデレーション、メール、ログ、一括ラベル付け。
- **ランキングとマッチング**: リランカー、エンティティマッチング、グラフや分類体系の探索。
- **ジャッジと評価**: ルーブリックによるジャッジ、トレースの採点、トリアージとしてのコードレビュー。
- **逐次処理とリアルタイム**: 吹き替え、音声、キー入力で動くインターフェース。
- **エージェントのコンテキストとメモリ**: コンパクション、メモリのゲート、メモリの期限切れ、労力の制御。
- **LLM との組み合わせ**: プランナーとアクター、検証してからエスカレーション、蒸留。
- **データとしての答え**: 古典的なモデルの特徴量、研究用の測定器、ベンチマーク。
- **インフラへの組み込み**: SQL 関数、ベクトルデータベース、CI フック、Home Assistant。

インデックスには、現場で失敗したアイデアも載っています。チェス、唯一のレビュアーとしてのコードレビュー、知覚、そして鵜呑みにした較正です。失敗の記録があれば、次の作り手は同じ失敗を繰り返さずに済みます。

## テストの方法

コードをテストするのと同じ方法でスキルをテストしました。まず失敗するのを確かめ、それから直します。

1. スキルなしで振り分けタスクを実行し、すべての推測と間違いを書き留めました。
2. それらの間違いを直すようにスキルを書きました。
3. 新しいエージェントがスキルありで同じタスクを実行し、わかりにくい点を挙げました。6 つの抜けを直しました。
4. スキル内の API の事実を、Python SDK 0.7.1 とモデル `jev-1.13.0` で、実際の API と照らし合わせました。
5. 先行事例のコードスケッチのうち 3 つを、実際の API で実行しました。ある実行で、Jev がハルシネーションのチェックを文字どおりに読むことがわかりました。その教訓は今スキルに入っています。
6. 新しいエージェントが、インデックスだけを使って 3 つの新しい設計を試しました。どれにも正しい形を見つけ、2 つの抜けを報告しました。両方とも直しました。
7. Claude Code、Codex、Antigravity CLI にプラグインをインストールし、それぞれがスキルを読み込むことを確認しました。
8. 6 つの評価ケースを、このスキルあり、スキルなし、公式スキルありでそれぞれ 10 回ずつ実行しました。各条件はそれぞれ専用の隔離されたコンテナで動かしました。[何が変わるのか](#何が変わるのか) と [evals README](../../evals/README.md) を参照してください。

## 最新に保つ

Jev は速く変わります。このスキルは、2026-09-25 時点の [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) とコミュニティのスナップショットです。食い違いがあれば最新のドキュメントが優先されるとエージェントに伝え、それを Markdown で取得する方法も示します。スキル内の事実が間違っていたら、出典へのリンクを添えて issue を開いてください。

## 公式スキルとの違い

[TypeSafe の公式スキル](https://github.com/typesafe-ai/skills) は短く、エージェントを最新のドキュメントへ誘導します。現在の API の詳細を知るには、それが正しい情報源です。必要なら、あわせてインストールしてください。

このスキルは、スキル自体により多くを持っています。正確な API の形、クックブックのしきい値、コミュニティで見つかった失敗パターン、そして先行事例ライブラリです。エージェントはネットワークの往復なしで設計でき、作り始める前に他の人が作ったものを見つけられます。

6 つの評価タスクで、公式スキルのスコアは 0.77 ± 0.04 でした。スキルなしは 0.65 ± 0.05、このスキルは 0.96 ± 0.02 です。[evals README](../../evals/README.md) を参照してください。

## クレジット

API に関する事実は、TypeSafe AI の公開ドキュメントとクックブックに基づいています。先行事例は、プロジェクトを公開した作り手、Hacker News のコミュニティ、そして次のインデックスから集めました。[awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe)、[JevDirectory](https://www.jevdirectory.org/resources)、[awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases)、[awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)。各形のファイルは、元のプロジェクトにリンクしています。

TypeSafe、Jev、System One は TypeSafe AI の名称です。このプロジェクトは、スキルの用途を示すためだけにこれらを使っています。

## ライセンス

MIT。[LICENSE](../../LICENSE) を参照してください。
