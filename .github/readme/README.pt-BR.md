<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>Decisões tipadas com confiança calibrada, para o seu agente de código.</em><br>
  <em>Referências de mais de 150 projetos da comunidade, organizadas por formato.</em>
</p>

<p align="center">
  <a href="../../LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href="../workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">Conecte-se no LinkedIn!</a>
</p>

<p align="center">
  <a href="../../README.md">English</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <strong>Português (BR)</strong> ·
  <a href="README.it.md">Italiano</a>
</p>

> [!NOTE]
> Esta é uma skill não oficial, feita pela comunidade. A TypeSafe AI não criou, não revisou e não endossa este projeto. A TypeSafe publica a própria skill em [typesafe-ai/skills](https://github.com/typesafe-ai/skills). Veja [Como ela difere da skill oficial](#como-ela-difere-da-skill-oficial).

Os agentes de código tratam o Jev como mais um modelo de chat. Esta skill ensina o agente a projetar para ele: perguntas tipadas, confiança calibrada e uma biblioteca de mais de 150 projetos da comunidade, organizados pela forma como funcionam. Ela se instala no Claude Code, no Codex e no Antigravity CLI.

O [Jev](https://docs.typesafe.ai/introduction) é um modelo [System One](https://docs.typesafe.ai/concepts/system-one). Ele não escreve texto. Você envia um conteúdo e um conjunto de perguntas tipadas, e ele responde a cada uma com um valor e uma probabilidade calibrada, normalmente em 100 a 200 ms:

- **Choice** escolhe uma opção de uma lista. Exemplo: encaminhar um ticket para cobrança, envio ou suporte.
- **Score** posiciona o conteúdo numa escala que você descreve. Exemplo: avaliar um pull request de "ignora a especificação" a "atende a especificação".
- **Noul** dá a probabilidade de uma afirmação de sim ou não ser verdadeira. Exemplo: "este comando de shell apaga arquivos fora do projeto."

## Instalação

<details>
<summary><strong>Claude Code</strong></summary>

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

A skill carrega sozinha quando você trabalha com código do Jev. Para carregá-la manualmente, digite:

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

Abra uma nova thread. O Codex carrega a skill quando a tarefa combina com ela. Para carregá-la manualmente, digite:

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

Confira se ela foi instalada:

```bash
agy plugin list
```

Abra uma nova sessão. O Antigravity CLI carrega a skill quando a tarefa combina. Para carregá-la manualmente, digite:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Vindo do Gemini CLI? Se o `agy plugin import gemini` trouxe esta extensão, rode o comando de instalação acima mesmo assim, para que a cópia atual substitua a importada.

</details>

<details>
<summary><strong>Qualquer outro agente que leia SKILL.md</strong></summary>

Copie a pasta `skills/building-with-typesafe-jev/` para a pasta de skills do seu agente. Mantenha a pasta inteira. O `SKILL.md` aponta para os arquivos ao lado dele.

</details>

## Configure uma chave de API (opcional, recomendado)

A skill funciona sem chave. Com `TYPESAFE_API_KEY` definida no shell do agente, o agente pode conferir o design contra a API ao vivo antes de o código chegar ao seu projeto. Isso pega nomes de campo errados e perguntas que o Jev lê de um jeito diferente do que você queria. Cada chamada custa uma fração de centavo.

<details>
<summary><strong>Crie, guarde e resolva problemas com uma chave</strong></summary>

<br>

<details>
<summary><strong>Crie uma chave</strong> (quatro passos no console da TypeSafe)</summary>

**Passo 1.** Entre em [console.typesafe.ai](https://console.typesafe.ai/) e abra **API Keys** (chaves de API) na barra lateral.

<img src="../assets/api-key/step-1.png" alt="A página inicial do console da TypeSafe. Uma caixa e uma seta âmbar apontam para API Keys na barra lateral esquerda." width="100%">

**Passo 2.** Clique em **Create key** (criar chave) no canto superior direito.

<img src="../assets/api-key/step-2.png" alt="A página de chaves de API. As chaves existentes estão desfocadas. Uma caixa e uma seta âmbar apontam para o botão Create key no canto superior direito." width="100%">

**Passo 3.** Dê à chave o nome do lugar onde ela vai ficar, como a máquina ou o agente. Depois clique em **Create key**.

<img src="../assets/api-key/step-3.png" alt="A caixa de diálogo Create API key com o nome my-coding-agent digitado. Uma caixa e uma seta âmbar apontam para o campo de nome e para o botão Create key." width="100%">

**Passo 4.** Copie a chave agora. O console a mostra uma única vez. Se você a perder, crie uma nova e revogue a antiga.

<img src="../assets/api-key/step-4.png" alt="A caixa de diálogo de chave de API criada. O valor da chave está mascarado. Uma caixa e uma seta âmbar apontam para o botão Copy." width="100%">

</details>

<details>
<summary><strong>Guarde a chave</strong> (macOS, Linux, Windows)</summary>

Mantenha a chave num arquivo próprio, que só você possa ler, e exporte-a como `TYPESAFE_API_KEY`. Os agentes costumam abrir shells sem terminal, então cada seção coloca a chave onde esses shells conseguem vê-la. Escolha o seu sistema.

<details>
<summary><strong>macOS</strong> (zsh, o shell padrão)</summary>

Salve a chave num arquivo privado:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Carregue-a a partir do `~/.zshenv`. Todo zsh lê esse arquivo, inclusive os shells que os agentes abrem sem terminal. O `~/.zshrc` só é lido por shells interativos.

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

Abra um novo terminal e confira. O comando imprime o tamanho da chave, não a chave:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux com bash</strong> (Ubuntu, Debian, Mint, Fedora, Arch)</summary>

Salve a chave num arquivo privado:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Carregue-a a partir do **topo** do `~/.bashrc`. Ubuntu, Debian, Mint e Arch começam o `~/.bashrc` com uma linha que encerra o script cedo quando não há terminal conectado. Uma linha abaixo dessa proteção nunca roda nos shells dos agentes. O topo do arquivo é seguro em todas as distribuições:

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

Abra um novo terminal e confira:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux com zsh</strong></summary>

Siga os passos do macOS. O zsh lê o `~/.zshenv` da mesma forma no Linux.

</details>

<details>
<summary><strong>Linux com fish</strong></summary>

O fish lê todos os arquivos em `~/.config/fish/conf.d/`, com ou sem terminal:

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong> (PowerShell)</summary>

Guarde a chave como variável de ambiente do usuário. Novos terminais e aplicativos a enxergam. Terminais que já estão abertos não:

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

Abra um novo terminal e confira:

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL:** por padrão, as variáveis do Windows não chegam ao WSL. Dentro do WSL, siga os passos de Linux com bash.

</details>

<details>
<summary><strong>Aplicativos de desktop e extensões de IDE</strong></summary>

Um aplicativo que você abre pelo dock, pelo menu Iniciar ou por um atalho da área de trabalho não lê os seus arquivos de shell.

- **Windows:** a variável de ambiente do usuário acima já cobre esses aplicativos.
- **Linux (systemd):** adicione a linha `TYPESAFE_API_KEY=YOUR_KEY` em `~/.config/environment.d/typesafe.conf` e depois saia da sessão e entre de novo.
- **macOS:** abra o aplicativo a partir de um terminal ou defina a variável nas configurações do próprio aplicativo. O macOS não tem um arquivo simples por usuário que os aplicativos de desktop leiam.

</details>

</details>

<details>
<summary><strong>Se o agente não consegue ver a chave</strong></summary>

Peça ao agente para rodar `echo ${#TYPESAFE_API_KEY}` (ou `$env:TYPESAFE_API_KEY.Length` no Windows). Se ele imprimir `0` ou nada, verifique estes pontos, nesta ordem:

- **Você abriu o agente antes de guardar a chave.** Os shells do agente copiam o ambiente do programa que os abriu. Feche o agente e abra-o a partir de um novo terminal.
- **Você abriu o agente pelo dock, pelo menu Iniciar ou por uma IDE.** Esses aplicativos não leem os seus arquivos de shell. Veja "Aplicativos de desktop e extensões de IDE" acima.
- **O Codex filtra o ambiente.** Se o `~/.codex/config.toml` define `include_only` em `[shell_environment_policy]`, adicione `TYPESAFE_API_KEY` a ele. Se ele define `ignore_default_excludes = false`, o Codex descarta toda variável com `KEY` no nome. Remova essa linha.
- **WSL.** As variáveis do Windows não chegam ao WSL. Guarde a chave dentro do WSL com os passos de Linux.

</details>

</details>

## Como foi testada

Demos a um agente de código seis tarefas com o Jev, como uma função de triagem de tickets de suporte e um portão de aprovação para comandos de shell. Cada tarefa rodou 10 vezes com esta skill, sem nenhuma skill e com a skill oficial, cada lado no seu próprio contêiner isolado. O agente tinha a documentação, mas nenhuma chave de API, então os avaliadores conferiram o código que ele escreveu. As verificações que exigem julgamento foram para três avaliadores LLM de três provedores (Claude Opus, GPT-6 Sol, Kimi K3), e a maioria decidiu.

| | Sem skill | Esta skill | Skill oficial |
|---|---:|---:|---:|
| Pontuação média | 0.65 ± 0.05 | **0.96 ± 0.02** | 0.77 ± 0.04 |

A pontuação é a fração das verificações aprovadas, na média de 10 execuções por tarefa.

**Onde a skill fez a diferença** (execuções aprovadas, de 10):

| O código do agente... | Sem skill | Esta skill | Skill oficial |
|---|---:|---:|---:|
| contou no código, em vez de pedir um número ao Jev | 1 | 8 | 0 |
| citou um campo da entrada nas suas perguntas | 0 | 10 | 1 |
| fixou ou registrou a versão do modelo do Jev | 0 | 10 | 0 |
| deu à lista de departamentos uma opção genérica | 3 | 10 | 6 |
| manteve mais de um caminho ao percorrer 1,200 categorias | 1 | 10 | 7 |
| manteve uma proteção em código simples para comandos destrutivos | 7 | 10 | 2 |
| leu `score` como uma posição de 0 a n-1 | 9 | 10 | 5 |

[Veja todas as verificações →](../../evals/docs/results.md#every-check)

Cada uma dessas linhas supera a ausência de skill, a skill oficial ou as duas por mais do que o acaso explicaria, a 95%.

**Mais detalhes:**

- [evals/README.md](../../evals/README.md): resultados por caso e como rodar a suíte
- [evals/docs/results.md](../../evals/docs/results.md): todas as verificações, as notas de cada avaliador, custo, tokens e método
- [evals/docs/cases.md](../../evals/docs/cases.md): as seis tarefas e o que cada verificação procura
- [evals/docs/harness.md](../../evals/docs/harness.md): como uma execução funciona, os contêineres isolados e como guardar um lote
- [evals/docs/lessons.md](../../evals/docs/lessons.md): o que quebrou enquanto a suíte era construída

## O que tem dentro

A skill carrega em camadas, então o agente lê só o que a tarefa pede.

| Arquivo | O que contém | Quando o agente lê |
|---|---|---|
| `SKILL.md` | Qual primitiva escolher, 11 regras de design, como usar probabilidades e confiança, erros comuns | Em toda tarefa com o Jev |
| `api-reference.md` | API HTTP, SDKs de Python e JavaScript, limites, erros, variáveis de ambiente | Quando escreve o código |
| `patterns.md` | Os 4 padrões oficiais e as técnicas de 18 cookbooks, com seus limiares | Quando projeta um fluxo |
| `prior-art/INDEX.md` | Um mapa de "o que eu quero construir" para um formato, mais as ideias que falharam | Antes de projetar algo novo |
| `prior-art/*.md` | 11 arquivos de formato: um esboço de código, lições de campo e projetos com link | Um ou dois por design |

A biblioteca de referências organiza os projetos pela forma como funcionam, não por setor. Um bot de jogo, um drone e um bot de trading são todos **loops de controle**, então compartilham um esboço e um conjunto de lições. Os outros formatos: seleção entre candidatos, portões, filtros de fluxo, ranqueamento e correspondência, juízes e avaliações, incremental e em tempo real, contexto e memória de agentes, parceria com um LLM, respostas como dados e embutido na infraestrutura. O índice também lista as ideias que falharam na prática.

## Como ela difere da skill oficial

A [skill oficial da TypeSafe](https://github.com/typesafe-ai/skills) é um único arquivo de orientações de design. Para os detalhes da API, ela manda o agente para a documentação ao vivo em toda tarefa. As duas skills têm nomes diferentes e não entram em conflito, então você pode instalar as duas, embora as avaliações não as tenham testado juntas.

Esta skill guarda mais coisa dentro dela mesma: os formatos exatos da API, os limiares dos cookbooks, as falhas relatadas pela comunidade e a biblioteca de referências. O agente consegue projetar sem ir à rede e ver o que outros já construíram antes.

O Jev muda rápido. A skill é um retrato de [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) e da comunidade em 2026-09-25, e ela diz ao agente que a documentação ao vivo prevalece em qualquer conflito. Se algum fato estiver errado, abra uma issue com um link para a fonte.

## Créditos

Os fatos sobre a API vêm da documentação pública e dos cookbooks da TypeSafe AI. As referências vêm das pessoas que publicaram seus projetos, da comunidade do Hacker News e destes índices: [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases) e [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). Cada arquivo de formato aponta para os projetos originais.

TypeSafe, Jev e System One são nomes da TypeSafe AI. Este projeto os usa só para dizer para que serve a skill.

## Licença

MIT. Veja [LICENSE](../../LICENSE).
