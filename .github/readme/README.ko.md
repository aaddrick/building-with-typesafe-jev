<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>코딩 에이전트를 위한, 보정된 신뢰도를 갖춘 타입 있는 결정.</em><br>
  <em>150개가 넘는 커뮤니티 프로젝트 링크를 형태별로 정리하고, 형태마다 코드 스케치를 담았습니다.</em>
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
  <a href="README.it.md">Italiano</a>
</p>

> [!NOTE]
> 이 스킬은 비공식 커뮤니티 스킬입니다. TypeSafe AI가 만들거나 검토하거나 보증한 것이 아닙니다. TypeSafe는 자체 스킬을 [typesafe-ai/skills](https://github.com/typesafe-ai/skills)에 공개하고 있습니다. [공식 스킬과 다른 점](#공식-스킬과-다른-점)을 참고하세요.

코딩 에이전트는 Jev를 채팅 모델 하나쯤으로 다룹니다. 이 스킬은 에이전트가 Jev에 맞게 설계하도록 가르칩니다. 타입 있는 질문, 보정된 신뢰도, 그리고 동작 방식별로 정리한 150개가 넘는 커뮤니티 프로젝트 링크와 패턴별 코드 스케치를 담았습니다. Claude Code, Codex, Antigravity CLI에 설치할 수 있습니다.

[Jev](https://docs.typesafe.ai/introduction)는 [System One](https://docs.typesafe.ai/concepts/system-one) 모델입니다. 글을 쓰지 않습니다. 콘텐츠와 타입 있는 질문 몇 개를 보내면, 각 질문에 값과 보정된 확률로 답합니다. 보통 100~200ms가 걸립니다.

- **Choice**는 목록에서 선택지 하나를 고릅니다. 예: 티켓을 billing, shipping, support 중 한 곳으로 보냅니다.
- **Score**는 설명한 척도 위에 콘텐츠를 놓습니다. 예: 풀 리퀘스트를 "사양 무시"부터 "사양 충족"까지의 척도로 평가합니다.
- **Noul**은 예/아니요 진술이 참일 확률을 알려 줍니다. 예: "이 셸 명령은 프로젝트 밖의 파일을 삭제한다."

## 설치

<details>
<summary><strong>Claude Code</strong></summary>

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

</details>

<details>
<summary><strong>Claude Desktop, Cowork, claude.ai</strong></summary>

**Customize > Plugins > Add > Add marketplace**을 열고 `https://github.com/aaddrick/building-with-typesafe-jev`를 붙여넣으세요. 그런 다음 그 마켓플레이스에서 플러그인을 설치하세요.

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

Gemini CLI에서 옮겨 오셨나요? `agy plugin import gemini`로 이 확장을 가져왔더라도 위의 설치 명령을 실행해서 현재 복사본이 가져온 복사본을 대체하게 하세요.

</details>

<details>
<summary><strong>SKILL.md를 읽는 다른 에이전트</strong></summary>

`skills/building-with-typesafe-jev/` 폴더를 에이전트의 스킬 폴더에 복사하세요. 폴더 전체를 유지하세요. `SKILL.md`는 옆에 있는 파일들을 링크합니다.

</details>

## API 키 설정 (선택, 권장)

이 스킬은 키 없이도 작동합니다. 에이전트의 셸에 `TYPESAFE_API_KEY`가 설정되어 있으면, 에이전트는 코드가 프로젝트에 들어가기 전에 설계를 실제 API로 확인할 수 있습니다. 그 과정에서 잘못된 필드 이름이나, 의도와 다르게 Jev가 읽는 질문을 잡아냅니다. 호출 한 번의 비용은 1센트도 되지 않습니다.

<details>
<summary><strong>키 만들기, 저장하기, 문제 해결</strong></summary>

<br>

<details>
<summary><strong>키 만들기</strong> (TypeSafe 콘솔에서 네 단계)</summary>

**1단계.** [console.typesafe.ai](https://console.typesafe.ai/)에 로그인한 뒤 사이드바에서 **API Keys**를 여세요.

<img src="../assets/api-key/step-1.png" alt="TypeSafe 콘솔 홈 화면. 주황색 상자와 화살표가 왼쪽 사이드바의 API Keys를 가리킵니다." width="100%">

**2단계.** 오른쪽 위의 **Create key**를 클릭하세요.

<img src="../assets/api-key/step-2.png" alt="API 키 페이지. 기존 키는 흐리게 처리되어 있습니다. 주황색 상자와 화살표가 오른쪽 위의 Create key 버튼을 가리킵니다." width="100%">

**3단계.** 키가 쓰일 곳, 예를 들어 컴퓨터나 에이전트 이름으로 키 이름을 정하세요. 그런 다음 **Create key**를 클릭하세요.

<img src="../assets/api-key/step-3.png" alt="이름 칸에 my-coding-agent가 입력된 Create API key 대화 상자. 주황색 상자와 화살표가 이름 칸과 Create key 버튼을 가리킵니다." width="100%">

**4단계.** 지금 키를 복사하세요. 콘솔은 키를 한 번만 보여 줍니다. 키를 잃어버리면 새 키를 만들고 이전 키를 폐기하세요.

<img src="../assets/api-key/step-4.png" alt="API key created 대화 상자. 키 값은 가려져 있습니다. 주황색 상자와 화살표가 Copy 버튼을 가리킵니다." width="100%">

</details>

<details>
<summary><strong>키 저장하기</strong> (macOS, Linux, Windows)</summary>

키는 본인만 읽을 수 있는 별도 파일에 보관하고, `TYPESAFE_API_KEY`로 내보내세요. 에이전트는 터미널 없이 셸을 시작하는 경우가 많으므로, 각 항목은 그런 셸에서도 보이는 곳에 키를 둡니다. 사용하는 시스템을 고르세요.

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
<summary><strong>에이전트가 키를 보지 못할 때</strong></summary>

에이전트에게 `echo ${#TYPESAFE_API_KEY}`(Windows에서는 `$env:TYPESAFE_API_KEY.Length`)를 실행하라고 하세요. `0`이 나오거나 아무것도 나오지 않으면 다음을 순서대로 확인하세요.

- **키를 저장하기 전에 에이전트를 시작했습니다.** 에이전트 셸은 자신을 시작한 프로그램의 환경을 복사합니다. 에이전트를 종료하고 새 터미널에서 다시 시작하세요.
- **Dock, 시작 메뉴, IDE에서 에이전트를 시작했습니다.** 이런 앱은 셸 파일을 읽지 않습니다. 위의 "데스크톱 앱과 IDE 확장"을 참고하세요.
- **Codex가 환경을 걸러 냅니다.** `~/.codex/config.toml`의 `[shell_environment_policy]` 아래에 `include_only`가 설정되어 있다면, 거기에 `TYPESAFE_API_KEY`를 추가하세요. `ignore_default_excludes = false`가 설정되어 있다면 Codex는 이름에 `KEY`가 들어간 변수를 모두 버립니다. 그 줄을 지우세요.
- **WSL.** Windows 변수는 WSL에 전달되지 않습니다. Linux 단계를 따라 WSL 안에 키를 저장하세요.

</details>

</details>

## 테스트 방법

코딩 에이전트에게 Jev 작업 여섯 개를 줬습니다. 지원 티켓 분류 함수, 셸 명령 승인 게이트 같은 작업입니다. 각 작업을 이 스킬과 함께, 스킬 없이, 공식 스킬과 함께 각각 10번씩 실행했고, 조건마다 별도의 격리된 컨테이너를 썼습니다. 에이전트는 문서는 있었지만 API 키는 없었기 때문에, 채점자는 에이전트가 쓴 코드를 확인했습니다. 판단이 필요한 확인 항목은 세 제공사의 LLM 채점 모델 세 개(Claude Opus, GPT-6 Sol, Kimi K3)에 맡겼고, 다수결로 정했습니다.

| | 스킬 없음 | 이 스킬 | 공식 스킬 |
|---|---:|---:|---:|
| 평균 점수 | 0.65 ± 0.05 | **0.96 ± 0.02** | 0.77 ± 0.04 |

점수는 통과한 확인 항목의 비율을 작업당 10번의 실행에 걸쳐 평균한 값입니다.

**이 스킬이 차이를 만든 곳** (10번 중 통과한 실행 수):

| 에이전트의 코드가... | 스킬 없음 | 이 스킬 | 공식 스킬 |
|---|---:|---:|---:|
| Jev에 숫자를 묻지 않고 코드에서 셌습니다 | 1 | 8 | 0 |
| 질문에서 입력의 필드를 이름으로 가리켰습니다 | 0 | 10 | 1 |
| Jev 모델 버전을 고정하거나 기록했습니다 | 0 | 10 | 0 |
| 부서 목록에 기타 선택지를 두었습니다 | 3 | 10 | 6 |
| 1,200개 카테고리를 탐색하는 동안 경로를 둘 이상 유지했습니다 | 1 | 10 | 7 |
| 파괴적인 명령에 대한 일반 코드 안전장치를 유지했습니다 | 7 | 10 | 2 |
| `score`를 0부터 n-1까지의 위치로 읽었습니다 | 9 | 10 | 5 |

[모든 확인 항목 보기 →](../../evals/docs/results.md#every-check)

위의 각 행은 95% 수준에서 우연 이상의 차이로 스킬 없음, 공식 스킬, 또는 둘 다를 앞섭니다.

**자세한 내용:**

- [evals/README.md](../../evals/README.md): 케이스별 결과와 스위트 실행 방법
- [evals/docs/results.md](../../evals/docs/results.md): 모든 확인 항목, 채점 모델별 점수, 비용, 토큰, 방법
- [evals/docs/cases.md](../../evals/docs/cases.md): 작업 여섯 개와 각 확인 항목이 보는 것
- [evals/docs/harness.md](../../evals/docs/harness.md): 실행 방식, 격리된 컨테이너, 배치를 보존하는 방법
- [evals/docs/lessons.md](../../evals/docs/lessons.md): 스위트를 만드는 동안 깨졌던 것들

## 안에 든 것

스킬은 여러 층으로 로드됩니다. 그래서 에이전트는 작업에 필요한 것만 읽습니다.

| 파일 | 담긴 내용 | 에이전트가 읽는 때 |
|---|---|---|
| `SKILL.md` | 어떤 기본 요소를 고를지, 설계 규칙 11개, 확률과 신뢰도 쓰는 법, 흔한 실수 | 모든 Jev 작업 |
| `api-reference.md` | HTTP API, Python과 JavaScript SDK, 제한, 오류, 환경 변수 | 코드를 작성할 때 |
| `patterns.md` | 공식 패턴 4개와 쿡북 18개의 기법, 그리고 각 임곗값 | 워크플로를 설계할 때 |
| `prior-art/INDEX.md` | "만들고 싶은 것"에서 형태로 가는 지도, 그리고 실패한 아이디어 | 새로운 것을 설계하기 전 |
| `prior-art/*.md` | 형태 파일 11개: 코드 스케치, 현장의 교훈, 링크된 프로젝트 | 설계마다 한두 개 |

## 선행 사례 라이브러리

대부분의 카탈로그는 프로젝트를 산업별로 나눕니다. 이 라이브러리는 구현 형태로 나눕니다. 게임 봇, 드론, 트레이딩 봇은 같은 형태를 공유합니다. 바로 제어 루프입니다. 이렇게 나누면 세 프로젝트가 코드 스케치 하나와 현장의 교훈 한 묶음을 공유합니다. 형태 11개는 다음과 같습니다.

- **[제어 루프](../../skills/building-with-typesafe-jev/prior-art/control-loops.md)**: 게임, 드론, 로봇, 시장.
- **[후보 중 선택](../../skills/building-with-typesafe-jev/prior-art/select-from-candidates.md)**: 브라우저와 휴대폰 에이전트, LLM 없는 도구 호출, 추출, 라우터.
- **[게이트](../../skills/building-with-typesafe-jev/prior-art/gates.md)**: 도구 호출 승인, "완료" 확인, CI, 돈, 콘텐츠.
- **[스트림 필터](../../skills/building-with-typesafe-jev/prior-art/stream-filters.md)**: 저품질 콘텐츠 필터, 모더레이션, 이메일, 로그, 대량 라벨.
- **[순위와 매칭](../../skills/building-with-typesafe-jev/prior-art/ranking-and-matching.md)**: 리랭커, 엔티티 매칭, 그래프와 분류 체계 탐색.
- **[심사와 평가](../../skills/building-with-typesafe-jev/prior-art/judges-and-evals.md)**: 루브릭 심사, 트레이스 채점, 분류 작업으로서의 코드 리뷰.
- **[점진적 처리와 실시간](../../skills/building-with-typesafe-jev/prior-art/incremental-realtime.md)**: 더빙, 음성, 키 입력으로 움직이는 인터페이스.
- **[에이전트 컨텍스트와 메모리](../../skills/building-with-typesafe-jev/prior-art/agent-context-memory.md)**: 압축, 메모리 게이트, 메모리 만료, 노력 수준 조절.
- **[LLM과 짝짓기](../../skills/building-with-typesafe-jev/prior-art/llm-pairing.md)**: 계획자와 실행자, 검증 후 에스컬레이션, 증류.
- **[데이터로서의 답](../../skills/building-with-typesafe-jev/prior-art/research-and-features.md)**: 고전 모델용 특징, 연구 도구, 벤치마크.
- **[인프라에 넣기](../../skills/building-with-typesafe-jev/prior-art/embedding-in-infrastructure.md)**: SQL 함수, 벡터 데이터베이스, CI 훅, Home Assistant.

인덱스에는 현장에서 실패한 아이디어도 있습니다. 체스, 유일한 리뷰어로서의 코드 리뷰, 인식, 그리고 믿고 받아들인 보정입니다. 실패한 시도는 다음 빌더가 같은 실수를 반복하지 않게 해 줍니다.

## 공식 스킬과 다른 점

[공식 TypeSafe 스킬](https://github.com/typesafe-ai/skills)은 설계 지침을 담은 파일 하나입니다. API 세부 사항은 작업마다 에이전트를 실시간 문서로 보냅니다. 두 스킬은 이름이 다르고 서로 충돌하지 않으므로 둘 다 설치할 수 있습니다. 다만 둘을 함께 설치한 상태는 평가에서 테스트하지 않았습니다.

이 스킬은 스킬 안에 더 많은 것을 담고 있습니다. 정확한 API 형태, 쿡북의 임곗값, 커뮤니티에서 모은 실패 유형, 그리고 선행 사례 라이브러리입니다. 에이전트는 네트워크 왕복 없이 설계할 수 있고, 다른 사람들이 먼저 만든 것을 볼 수 있습니다.

Jev는 빠르게 바뀝니다. 이 스킬은 2026-09-25 기준 [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt)와 커뮤니티의 스냅샷이며, 충돌이 있으면 실시간 문서가 우선한다고 에이전트에게 알려 줍니다. 사실이 틀렸다면 출처 링크와 함께 이슈를 열어 주세요.

## 크레딧

API에 관한 사실은 TypeSafe AI의 공개 문서와 쿡북에서 왔습니다. 선행 사례는 프로젝트를 공개한 빌더들, Hacker News 커뮤니티, 그리고 다음 인덱스에서 왔습니다. [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases), [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). 각 형태 파일은 원래 프로젝트를 링크합니다.

TypeSafe, Jev, System One은 TypeSafe AI의 이름입니다. 이 프로젝트는 스킬의 용도를 설명할 때만 이 이름들을 씁니다.

## 라이선스

MIT. [LICENSE](../../LICENSE)를 참고하세요.
