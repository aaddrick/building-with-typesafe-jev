<p align="center">
  <img src="../assets/hero.png" alt="Building with TypeSafe Jev: 코딩 에이전트를 위한, 보정된 신뢰도를 갖춘 타입 있는 결정. 150개가 넘는 커뮤니티 프로젝트의 선행 사례를 형태별로 정리했습니다. 패널 두 개. 왼쪽에서는 Structured Outputs를 쓰는 LLM이 유효한 JSON을 반환한다. 부서: billing, 심각도: medium, 환불: false(빨간색), 신뢰도 0.95. 하지만 이 신뢰도는 생성된 값이며 보정되지 않았다. 오른쪽에서는 Jev 호출 한 번이 타입 있는 답 세 개를 반환한다. Choice(부서: billing, 신뢰도 0.88), Score(심각도: 2 중 1.43), Noul(환불: 0.99)." width="100%">
</p>

<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>코딩 에이전트를 위한, 보정된 신뢰도를 갖춘 타입 있는 결정.</em><br>
  <em>150개가 넘는 커뮤니티 프로젝트의 선행 사례를 형태별로 정리했습니다.</em>
</p>

<p align="center">
  <a href="../../LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href="../workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">LinkedIn에서 연결해요!</a>
</p>

<p align="center">
  <a href="../../README.md">English</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <strong>한국어</strong> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.it.md">Italiano</a> ·
  <a href="README.en-x-aibro.md">AI Bro</a>
</p>

> [!NOTE]
> 이 스킬은 비공식 커뮤니티 스킬입니다. TypeSafe AI가 만들거나 검토하거나 보증한 것이 아닙니다. TypeSafe는 자체 스킬을 [typesafe-ai/skills](https://github.com/typesafe-ai/skills)에 공개하고 있습니다. [공식 스킬과 다른 점](#공식-스킬과-다른-점)을 참고하세요.

코딩 에이전트는 Jev를 채팅 모델 하나쯤으로 다룹니다. 이 스킬은 에이전트가 Jev에 맞게 설계하도록 가르칩니다. 타입 있는 질문, 보정된 신뢰도, 그리고 동작 방식별로 정리한 150개가 넘는 커뮤니티 프로젝트 라이브러리를 담았습니다. Claude Code, Codex, Antigravity CLI에 설치할 수 있습니다.

## 설치

<details>
<summary><strong>Claude Code</strong></summary>

터미널에서 다음 두 명령을 실행하세요.

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

Jev 코드를 작업하면 스킬이 알아서 로드됩니다. 직접 로드하려면 다음을 입력하세요.

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

설치 중에 플러그인 옵션이 아직 설정되지 않았다는 메시지가 나올 수 있습니다. 이는 실시간 테스트 설정이며, 직접 켜기 전까지는 꺼져 있습니다. [API 키 설정](#api-키-설정-선택-권장)을 참고하세요.

</details>

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
codex plugin add building-with-typesafe-jev@building-with-typesafe-jev
```

새 스레드를 시작하세요. 작업이 맞으면 Codex가 스킬을 로드합니다. 직접 로드하려면 다음을 입력하세요.

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

설치되었는지 확인하세요.

```bash
agy plugin list
```

새 세션을 시작하세요. 작업이 맞으면 Antigravity CLI가 스킬을 로드합니다. 직접 로드하려면 다음을 입력하세요.

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Gemini CLI에서 옮겨 오셨나요? `agy plugin import gemini`로 이 확장을 가져왔더라도 위의 설치 명령을 실행하세요. 가져온 복사본을 대체합니다. 그 복사본의 설정 명령은 Antigravity CLI에서 동작하지 않습니다.

</details>

<details>
<summary><strong>SKILL.md를 읽는 다른 에이전트</strong></summary>

`skills/building-with-typesafe-jev/` 폴더를 에이전트의 스킬 폴더에 복사하세요. 폴더 전체를 유지하세요. `SKILL.md`는 옆에 있는 파일들을 링크합니다.

</details>

## API 키 설정 (선택, 권장)

이 스킬은 키 없이도 작동합니다. 키가 없어도 기본 요소를 고르고, 질문과 코드를 작성하고, 자체 API 레퍼런스와 대조해 확인합니다. 키가 있으면 코드가 프로젝트에 들어가기 전에 각 설계를 실제 API 호출로 시험하기도 합니다. 그 과정에서 잘못된 필드 이름이나, 의도와 다르게 Jev가 읽는 질문을 잡아냅니다. 호출 한 번의 비용은 1센트도 되지 않으므로 키를 쓰기를 강력히 권장합니다.

실시간 테스트는 직접 켜기 전까지 꺼져 있습니다. 꺼져 있는 동안 스킬은 키를 전혀 찾지 않습니다. 켜져 있으면 지정한 환경 변수(다른 이름을 고르지 않으면 `TYPESAFE_API_KEY`)에서만 키를 읽고, 첫 호출 전에 알려 주며, 작업당 약 10회의 테스트 호출만 합니다. 세 단계입니다. 키를 만들고, 저장하고, 실시간 테스트를 켜세요.

<details>
<summary><strong>키 만들기</strong> (TypeSafe 콘솔에서 네 단계)</summary>

**1단계.** [console.typesafe.ai](https://console.typesafe.ai/)에 로그인한 뒤 사이드바에서 **API Keys**(API 키)를 여세요.

<img src="../assets/api-key/step-1.png" alt="TypeSafe 콘솔 홈 화면. 주황색 상자와 화살표가 왼쪽 사이드바의 API Keys를 가리킵니다." width="100%">

**2단계.** 오른쪽 위의 **Create key**(키 만들기)를 클릭하세요.

<img src="../assets/api-key/step-2.png" alt="API 키 페이지. 기존 키는 흐리게 처리되어 있습니다. 주황색 상자와 화살표가 오른쪽 위의 Create key 버튼을 가리킵니다." width="100%">

**3단계.** 키가 쓰일 곳, 예를 들어 컴퓨터나 에이전트 이름으로 키 이름을 정하세요. 그런 다음 **Create key**(키 만들기)를 클릭하세요.

<img src="../assets/api-key/step-3.png" alt="이름 칸에 my-coding-agent가 입력된 Create API key 대화 상자. 주황색 상자와 화살표가 이름 칸과 Create key 버튼을 가리킵니다." width="100%">

**4단계.** 지금 키를 복사하세요. 콘솔은 키를 한 번만 보여 줍니다. 키를 잃어버리면 새 키를 만들고 이전 키를 폐기하세요.

<img src="../assets/api-key/step-4.png" alt="API key created 대화 상자. 키 값은 가려져 있습니다. 주황색 상자와 화살표가 Copy 버튼을 가리킵니다." width="100%">

</details>

<details>
<summary><strong>키 저장하기</strong> (macOS, Linux, Windows)</summary>

키는 본인만 읽을 수 있는 별도 파일에 보관하세요. 스킬은 파일이 아니라 환경 변수에서 키를 읽으므로, 에이전트가 시작하는 셸에 그 변수가 설정되어 있어야 합니다. 에이전트는 터미널 없이 셸을 시작하는 경우가 많으므로, 각 항목은 그런 셸에서도 보이는 곳에 키를 둡니다. 사용하는 시스템을 고르세요.

<details>
<summary><strong>macOS</strong> (zsh, 기본 셸)</summary>

키를 비공개 파일에 저장하세요.

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

`~/.zshenv`에서 로드하세요. 에이전트가 터미널 없이 시작하는 셸을 포함해 모든 zsh가 이 파일을 읽습니다. `~/.zshrc`는 대화형 셸만 읽습니다.

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

새 터미널을 열어 확인하세요. 이 명령은 키가 아니라 키의 길이를 출력합니다.

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux와 bash</strong> (Ubuntu, Debian, Mint, Fedora, Arch)</summary>

키를 비공개 파일에 저장하세요.

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

`~/.bashrc`의 **맨 위**에서 로드하세요. Ubuntu, Debian, Mint, Arch는 터미널이 연결되지 않으면 일찍 멈추는 줄로 `~/.bashrc`를 시작합니다. 그 보호 줄 아래에 있는 줄은 에이전트 셸에서 절대 실행되지 않습니다. 파일 맨 위는 모든 배포판에서 안전합니다.

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

새 터미널을 열어 확인하세요.

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux와 zsh</strong></summary>

macOS 단계를 따르세요. zsh는 Linux에서도 `~/.zshenv`를 똑같이 읽습니다.

</details>

<details>
<summary><strong>Linux와 fish</strong></summary>

fish는 터미널 유무와 관계없이 `~/.config/fish/conf.d/` 안의 모든 파일을 읽습니다.

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong> (PowerShell)</summary>

키를 사용자 환경 변수로 저장하세요. 새 터미널과 앱은 이 값을 봅니다. 이미 열려 있는 터미널은 보지 못합니다.

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

새 터미널을 열어 확인하세요.

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL:** Windows 변수는 기본적으로 WSL에 전달되지 않습니다. WSL 안에서는 Linux와 bash 단계를 따르세요.

</details>

<details>
<summary><strong>데스크톱 앱과 IDE 확장</strong></summary>

Dock, 시작 메뉴, 데스크톱 런처에서 시작한 앱은 셸 파일을 읽지 않습니다.

- **Windows:** 위의 사용자 환경 변수가 이미 이런 앱까지 적용됩니다.
- **Linux (systemd):** `~/.config/environment.d/typesafe.conf`에 `TYPESAFE_API_KEY=YOUR_KEY` 줄을 추가한 뒤, 로그아웃했다가 다시 로그인하세요.
- **macOS:** 터미널에서 앱을 시작하거나, 앱 자체 설정에서 변수를 지정하세요. macOS에는 데스크톱 앱이 읽는 간단한 사용자별 파일이 없습니다.

</details>

</details>

<details>
<summary><strong>실시간 테스트 켜기</strong> (Claude Code, Codex, Antigravity CLI)</summary>

각 에이전트는 두 가지 설정을 보관합니다. 실시간 테스트(`on` 또는 `off`, 기본값 `off`)와 키가 담긴 변수의 이름(기본값 `TYPESAFE_API_KEY`)입니다. 한 번만 설정하면 됩니다. 설정은 다음 세션부터 적용됩니다. 도우미 스크립트에는 Python 3가 필요하며, Codex용은 3.11 이상이 필요합니다.

**Claude Code.** 터미널에서 다음을 실행하세요.

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev --config live_testing=on
```

키가 다른 이름의 변수에 있다면 `--config key_env_var=YOUR_VARIABLE`을 추가하세요. 세션 안에서는 `/plugin configure building-with-typesafe-jev@building-with-typesafe-jev`로 같은 설정을 바꿀 수 있습니다.

**Codex.** Codex에는 플러그인 설정이 없으므로, 스킬은 설정을 `~/.codex/config.toml`에 보관합니다. Codex는 에이전트가 시작하는 모든 셸에 이 값을 전달합니다. 세션에서 다음을 입력하세요.

```
$building-with-typesafe-jev:jev-settings live on
```

Codex가 쓰기 승인을 요청합니다. 직접 바꾸려면 `~/.codex/config.toml`에 다음 줄을 추가하세요.

```toml
[shell_environment_policy.set]
JEV_LIVE_TESTING = "on"
JEV_KEY_ENV_VAR = "TYPESAFE_API_KEY"
```

Codex는 플러그인의 세션 시작 훅을 한 번 신뢰하라고도 요청합니다. 이 훅은 세션이 시작될 때마다 라이브 테스트가 켜져 있는지, 키 변수가 설정되어 있는지를 에이전트에게 알려 줍니다. 키 자체는 알려 주지 않습니다. 세션에서 `/hooks`를 입력하고 훅을 신뢰하세요. 업데이트로 훅이 바뀌면 Codex가 다시 묻습니다. 신뢰하기 전까지 훅은 실행되지 않으며, 스킬은 여전히 스스로 설정을 확인합니다.

**Antigravity CLI.** Antigravity CLI에는 플러그인 설정이 없지만, 에이전트의 셸은 `agy`를 시작한 터미널의 환경을 물려받습니다. 그래서 설정은 두 개의 환경 변수이고, 키를 저장한 곳에 둡니다. 키가 `~/.config/typesafe/env`에 있다면 다음을 실행한 뒤, 새 터미널을 열고 `agy`를 다시 시작하세요.

```bash
echo 'export JEV_LIVE_TESTING=on' >> ~/.config/typesafe/env
```

키가 다른 이름의 변수에 있다면 같은 방법으로 `export JEV_KEY_ENV_VAR=YOUR_VARIABLE`을 추가하세요. fish나 Windows에서는 키를 저장한 방법대로 `JEV_LIVE_TESTING`을 `on`으로 설정하세요.

**확인하기.** 새 세션을 시작하고 설정 명령을 실행하세요. Claude Code에서는 `/building-with-typesafe-jev:jev-settings`, Codex에서는 `$building-with-typesafe-jev:jev-settings`, Antigravity CLI에서는 `/building-with-typesafe-jev:jev-settings`입니다. 두 설정과 함께 에이전트의 셸이 키를 볼 수 있는지 보여 줍니다. 키 자체는 출력하지 않고 키의 길이만 출력합니다.

**CI와 컨테이너.** 환경 변수 `JEV_LIVE_TESTING`과 `JEV_KEY_ENV_VAR`는 모든 에이전트에서 저장된 설정보다 우선합니다.

</details>

<details>
<summary><strong>에이전트가 키를 보지 못할 때</strong></summary>

에이전트의 셸에 해당 변수가 없으면 설정 명령이 `key: not set in this shell`이라고 표시합니다. 다음을 순서대로 확인하세요.

- **키를 저장하기 전에 에이전트를 시작했습니다.** 에이전트 셸은 자신을 시작한 프로그램의 환경을 복사합니다. 에이전트를 종료하고 새 터미널에서 다시 시작하세요.
- **Dock, 시작 메뉴, IDE에서 에이전트를 시작했습니다.** 이런 앱은 셸 파일을 읽지 않습니다. 위의 "데스크톱 앱과 IDE 확장"을 참고하세요.
- **Codex가 환경을 걸러 냅니다.** `~/.codex/config.toml`의 `[shell_environment_policy]` 아래에 `include_only`가 설정되어 있다면, 키 변수와 `JEV_LIVE_TESTING`, `JEV_KEY_ENV_VAR`를 거기에 추가하세요. `ignore_default_excludes = false`가 설정되어 있다면 Codex는 이름에 `KEY`가 들어간 변수를 모두 버립니다. 그 줄을 지우세요.
- **WSL.** Windows 변수는 WSL에 전달되지 않습니다. Linux 단계를 따라 WSL 안에 키를 저장하세요.

</details>

이 스킬은 키를 출력하거나, 로그에 남기거나, 하드코딩하지 않습니다. 지정한 변수만 읽고, 키를 명령줄에 넣지 않은 채 각 테스트 명령에 전달합니다.

## 하는 일

LLM은 JSON을 반환할 수 있고, Structured Outputs를 쓰면 그 JSON은 매번 파싱됩니다. 그래도 답은 틀릴 수 있으며, 얼마나 자주 틀리는지는 출력 어디에도 나오지 않습니다. 스키마는 답의 형태를 고정할 뿐, 답 자체를 고정하지는 않습니다. 모델이 알았든 추측했든 부서 필드에는 "billing"이 들어갑니다. 신뢰도 필드를 추가해도 모델은 답을 쓰는 것과 같은 방식으로 그 숫자를 씁니다. 그 숫자는 어떤 기준에도 보정되어 있지 않습니다.

[Jev](https://docs.typesafe.ai/introduction)는 TypeSafe AI의 [System One](https://docs.typesafe.ai/concepts/system-one) 모델입니다. 글을 쓰지 않습니다. 확률은 디코더에서 샘플링한 값이 아니라 실제 결과에 맞춰 최적화된 값이며, 대부분의 쿼리는 100~200ms 안에 돌아옵니다. 지원 티켓 같은 콘텐츠와 질문 몇 개를 보내면, 각 질문에 타입 있는 값과 보정된 확률로 답합니다. 파싱할 텍스트가 없습니다. 질문은 세 가지 타입 중 하나입니다.

- **Choice**는 주어진 목록에서 선택지 하나를 고릅니다. 예: 문서 검색, 테스트 실행, 사용자에게 질문하기 중 에이전트의 다음 단계. 루프 안에 LLM이 없는 도구 라우팅입니다.
- **Score**는 단계별로 설명한 척도 위에 콘텐츠를 놓습니다. 예: 사양 무시 → 사양 일부 충족 → 사양 충족 척도로 에이전트의 풀 리퀘스트를 평가합니다. 결과는 1.6으로, 사양 충족에 거의 다가갔습니다.
- **Noul**은 예/아니요 진술이 참일 확률을 알려 줍니다. 예: "이 셸 명령은 프로젝트 밖의 파일을 삭제한다"는 0.97로 돌아오고, 승인 게이트가 명령이 실행되기 전에 막습니다.

API 레퍼런스를 읽는 것은 쉬운 부분입니다. 어려운 부분은 글을 쓰지 않는 모델에 맞게 설계하는 일입니다. 이 스킬이 없는 에이전트는 튜토리얼 하나를 찾고, 나머지 API는 추측하고, 프롬프트를 쓰고 출력을 파싱하던 습관을 바로 그 습관을 대체하려고 만든 모델에 그대로 가져옵니다. 이 스킬은 에이전트에게 API, 설계 규칙, 알려진 실패 유형, 그리고 다른 사람들이 이미 만든 것의 지도를 줍니다. 문서는 모델을 설명합니다. 스킬은 그 모델에 맞게 설계하는 법을 보여 줍니다.

## 무엇이 달라지나

코딩 에이전트에게 Jev 작업 여섯 개를 줬습니다. 지원 티켓 분류 함수, 셸 명령 승인 게이트 같은 작업입니다. 에이전트는 문서는 있었지만 API 키는 없었습니다. 그래서 채점자는 그 코드가 Jev에서 실제로 무엇을 했는지가 아니라, 에이전트가 쓴 코드를 확인했습니다. 각 작업을 세 가지 설정에서 각각 열 번씩 실행했고, 모두 하나의 평가 배치로 한꺼번에 시작했습니다.

| | 스킬 없음 | 이 스킬 | 공식 스킬 |
|---|---:|---:|---:|
| 평균 점수 | 0.65 | 0.96 | 0.77 |

점수는 한 번의 실행이 통과한 확인 항목의 비율입니다. 각 평균은 95% 신뢰도에서 0.05 이내로 정확합니다.

### 이 스킬이 차이를 만든 곳

아래는 통과 횟수에 대한 95% 검정으로 볼 때, 이 스킬과 스킬 없음의 차이가 우연이라고 보기에는 너무 큰 확인 항목입니다. 각 숫자는 10번 중 통과한 실행 수입니다.

| 에이전트의 코드가... | 스킬 없음 | 이 스킬 | 공식 스킬 |
|---|---:|---:|---:|
| Jev에 숫자를 묻지 않고 코드에서 셌습니다 | 1 | 8 | 0 |
| 질문에서 입력의 필드를 이름으로 가리켰습니다 | 0 | 10 | 1 |
| Jev 모델 버전을 고정하거나 기록했습니다 | 0 | 10 | 0 |
| 1,200개 카테고리를 탐색하는 동안 경로를 둘 이상 유지했습니다 | 1 | 10 | 7 |
| 부서 목록에 기타 선택지를 두었습니다 | 3 | 10 | 6 |
| 명령 게이트에 예/아니요 질문을 둘 이상 물었습니다 | 5 | 10 | 9 |
| 루브릭 항목마다 질문을 하나씩 묻고 등급은 코드에서 계산했습니다 | 5 | 10 | 10 |

이 중 세 개는 패턴 매칭으로 채점합니다. 나머지 네 개는 세 제공사의 LLM 채점 모델 세 개, Claude Opus, GPT-6 Sol, Kimi K3가 채점하고, 다수결로 정합니다. 에이전트가 Claude 모델이므로 Claude 채점 모델 혼자서 결정하는 일은 없습니다.

### 공식 스킬과 비교하면

같은 검정으로 보면, 이 스킬은 확인 항목 여덟 개에서 공식 스킬보다 더 자주 통과했습니다. 네 개는 표에 있습니다. 개수 세기, 필드 이름, 모델 버전, 기타 선택지입니다. 나머지 네 개는 다음과 같습니다.

- Jev가 뭐라고 하든 파괴적인 명령을 막거나 사람에게 넘기는 일반 코드 규칙을 두었습니다: 10번 대 2번
- 심각도 확률을 정수 키로 읽었습니다: 10번 대 4번
- `score`를 0부터 n-1까지의 위치로 읽었습니다: 10번 대 5번
- 로그 라벨러의 동시 요청을 8개 이하로 유지했습니다: 10번 대 6번

### 차이가 없었던 곳

- 확인 항목 하나는 채점 모델끼리 판정이 갈려서 표에 넣지 않았습니다. Opus와 GPT-6 Sol로 채점하면, 이 스킬은 에이전트가 직접 댄 이유로 명령이 승인되지 않게 한 실행이 10번이었고, 스킬 없음은 5번이었습니다. Kimi K3는 그 스킬 없음 실행 10번 중 9번을 통과시켰습니다.
- `confidence`로 라우팅하는 항목은 이 스킬로 10번 중 2번, 스킬 없이 10번 중 2번 통과했습니다. 작업에는 불확실한 티켓을 어디로 보낼지가 나와 있지 않았기 때문에, 대부분의 에이전트는 신뢰도 값을 반환하고 결정을 호출자에게 맡겼습니다. 코드가 가장 좋은 선택지를 고르기만 한다면 그래도 괜찮다고 스킬 자체도 말합니다. 이제 작업에 폴백이 명시되어 있고, 다음 평가 배치에서 이를 검증합니다.
- 다른 확인 항목은 모두 세 설정 모두에서 거의 모든 실행이 통과했거나, 차이가 우연의 범위 안이었습니다.

범위를 포함한 모든 확인 항목과 스위트 실행 방법은 [evals README](../../evals/README.md)에 있습니다.

## 안에 든 것

스킬은 여러 층으로 로드됩니다. 그래서 에이전트는 작업에 필요한 것만 읽습니다. 큰 파일 하나로 만들면 에이전트는 코드 한 줄을 쓰기도 전에 매 작업마다 토큰과 주의력을 써야 합니다.

| 파일 | 담긴 내용 | 에이전트가 읽는 때 |
|---|---|---|
| `SKILL.md` | 어떤 기본 요소를 고를지, 설계 규칙 11개, 확률과 신뢰도 쓰는 법, 답이 틀렸을 때 할 일, 흔한 실수 | 모든 Jev 작업 |
| `api-reference.md` | HTTP API, Python과 JavaScript SDK, 제한, 오류, 환경 변수 | 코드를 작성할 때 |
| `patterns.md` | 공식 패턴 4개와 쿡북 18개의 기법, 그리고 각 임곗값 | 워크플로를 설계할 때 |
| `prior-art/INDEX.md` | "만들고 싶은 것"에서 형태로 가는 지도, 그리고 실패한 아이디어 | 새로운 것을 설계하기 전 |
| `prior-art/*.md` | 형태 파일 11개: 코드 스케치, 현장의 교훈, 링크된 프로젝트 | 설계마다 한두 개 |
| `scripts/jev_live.py` | 실시간 테스트 설정을 읽고, 키와 함께 테스트 명령을 실행 | 실시간 테스트 호출 전 |
| `../jev-settings/` | Claude Code, Codex, Antigravity CLI용 설정 명령 | 사용자가 실행할 때 |

## 선행 사례 라이브러리

대부분의 카탈로그는 프로젝트를 산업별로 나눕니다. 이 라이브러리는 구현 형태로 나눕니다. 게임 봇, 드론, 트레이딩 봇은 같은 형태를 공유합니다. 바로 제어 루프입니다. 이렇게 나누면 세 프로젝트가 코드 스케치 하나와 현장의 교훈 한 묶음을 공유합니다. 형태 11개는 다음과 같습니다.

- **제어 루프**: 게임, 드론, 로봇, 시장.
- **후보 중 선택**: 브라우저와 휴대폰 에이전트, LLM 없는 도구 호출, 추출, 라우터.
- **게이트**: 도구 호출 승인, "완료" 확인, CI, 돈, 콘텐츠.
- **스트림 필터**: 저품질 콘텐츠 필터, 모더레이션, 이메일, 로그, 대량 라벨.
- **순위와 매칭**: 리랭커, 엔티티 매칭, 그래프와 분류 체계 탐색.
- **심사와 평가**: 루브릭 심사, 트레이스 채점, 분류 작업으로서의 코드 리뷰.
- **점진적 처리와 실시간**: 더빙, 음성, 키 입력으로 움직이는 인터페이스.
- **에이전트 컨텍스트와 메모리**: 압축, 메모리 게이트, 메모리 만료, 노력 수준 조절.
- **LLM과 짝짓기**: 계획자와 실행자, 검증 후 에스컬레이션, 증류.
- **데이터로서의 답**: 고전 모델용 특징, 연구 도구, 벤치마크.
- **인프라에 넣기**: SQL 함수, 벡터 데이터베이스, CI 훅, Home Assistant.

인덱스에는 현장에서 실패한 아이디어도 있습니다. 체스, 유일한 리뷰어로서의 코드 리뷰, 인식, 그리고 믿고 받아들인 보정입니다. 실패한 시도는 다음 빌더가 같은 실수를 반복하지 않게 해 줍니다.

## 테스트 방법

코드를 테스트하듯이 스킬을 테스트했습니다. 먼저 실패하는 것을 확인하고, 그다음 고쳤습니다.

1. 스킬 없이 분류 작업을 실행하고, 모든 추측과 실수를 적어 두었습니다.
2. 그 실수를 고치도록 스킬을 작성했습니다.
3. 새 에이전트가 스킬을 가지고 같은 작업을 실행한 뒤, 불분명한 점을 나열했습니다. 빈틈 여섯 개를 고쳤습니다.
4. 스킬 속 API 사실을 실제 API와 대조했습니다. Python SDK 0.7.1과 모델 `jev-1.13.0`을 썼습니다.
5. 선행 사례 코드 스케치 세 개를 실제 API로 실행했습니다. 한 실행에서 Jev가 환각 검사를 글자 그대로 읽는다는 것이 드러났고, 그 교훈은 이제 스킬에 들어 있습니다.
6. 새 에이전트가 인덱스만 가지고 새 설계 세 개를 시도했습니다. 각각에 맞는 형태를 찾았고 빈틈 두 개를 보고했습니다. 둘 다 고쳤습니다.
7. Claude Code, Codex, Antigravity CLI에 플러그인을 설치하고, 각각 스킬을 로드하는지 확인했습니다.
8. 평가 케이스 여섯 개를 이 스킬과 함께, 스킬 없이, 공식 스킬과 함께 각각 열 번씩 실행했습니다. 조건마다 별도의 격리된 컨테이너를 썼습니다. [무엇이 달라지나](#무엇이-달라지나)와 [evals README](../../evals/README.md)를 참고하세요.

## 최신 상태 유지

Jev는 빠르게 바뀝니다. 이 스킬은 2026-09-25 기준 [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt)와 커뮤니티의 스냅샷입니다. 스킬은 에이전트에게 충돌이 있으면 실시간 문서가 우선한다고 알려 주고, 문서를 Markdown으로 가져오는 법도 보여 줍니다. 스킬 속 사실이 틀렸다면 출처 링크와 함께 이슈를 열어 주세요.

## 공식 스킬과 다른 점

[공식 TypeSafe 스킬](https://github.com/typesafe-ai/skills)은 짧고, 에이전트를 실시간 문서로 안내합니다. 현재 API 세부 사항을 볼 때는 그쪽이 맞는 출처입니다. 원하면 함께 설치하세요.

이 스킬은 스킬 안에 더 많은 것을 담고 있습니다. 정확한 API 형태, 쿡북의 임곗값, 커뮤니티에서 모은 실패 유형, 그리고 선행 사례 라이브러리입니다. 에이전트는 네트워크 왕복 없이 설계할 수 있고, 시작하기 전에 다른 사람들이 만든 것을 찾을 수 있습니다.

평가 작업 여섯 개에서 공식 스킬은 0.77 ± 0.04점을 받았습니다. 스킬 없이는 0.65 ± 0.05점, 이 스킬로는 0.96 ± 0.02점이었습니다. [evals README](../../evals/README.md)를 참고하세요.

## 크레딧

API에 관한 사실은 TypeSafe AI의 공개 문서와 쿡북에서 왔습니다. 선행 사례는 프로젝트를 공개한 빌더들, Hacker News 커뮤니티, 그리고 다음 인덱스에서 왔습니다. [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases), [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). 각 형태 파일은 원래 프로젝트를 링크합니다.

TypeSafe, Jev, System One은 TypeSafe AI의 이름입니다. 이 프로젝트는 스킬의 용도를 설명할 때만 이 이름들을 씁니다.

## 라이선스

MIT. [LICENSE](../../LICENSE)를 참고하세요.
