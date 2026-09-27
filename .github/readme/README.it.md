<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>Decisioni tipizzate con confidenza calibrata, per il tuo agente di coding.</em><br>
  <em>Link a oltre 150 progetti della community, ordinati per forma, con uno schema di codice per ciascuna.</em>
</p>

<p align="center">
  <a href="../../LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href="../workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">Seguimi su LinkedIn!</a>
</p>

<p align="center">
  <a href="../../README.md">English</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <strong>Italiano</strong>
</p>

> [!NOTE]
> Questa è una skill non ufficiale, della community. Non è creata, verificata o approvata da TypeSafe AI. TypeSafe pubblica la propria skill su [typesafe-ai/skills](https://github.com/typesafe-ai/skills). Vedi [In cosa differisce dalla skill ufficiale](#in-cosa-differisce-dalla-skill-ufficiale).

Gli agenti di coding trattano Jev come l'ennesimo modello di chat. Questa skill insegna loro a progettare per Jev: domande tipizzate, confidenza calibrata e link a oltre 150 progetti della community, ordinati per come funzionano, con uno schema di codice per ogni pattern. Si installa in Claude Code, Codex e Antigravity CLI.

[Jev](https://docs.typesafe.ai/introduction) è un modello [System One](https://docs.typesafe.ai/concepts/system-one). Non scrive testo. Gli invii un contenuto e un insieme di domande tipizzate, e lui risponde a ogni domanda con un valore e una probabilità calibrata, di solito in 100-200 ms:

- **Choice** sceglie un'opzione da un elenco. Esempio: instradare un ticket a fatturazione, spedizioni o assistenza.
- **Score** colloca il contenuto su una scala che descrivi tu. Esempio: valutare una pull request da "ignora la specifica" a "rispetta la specifica".
- **Noul** dà la probabilità che un'affermazione sì/no sia vera. Esempio: "questo comando di shell elimina file fuori dal progetto."

## Installazione

<details>
<summary><strong>Claude Code</strong></summary>

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

La skill si carica da sola quando lavori su codice Jev. Per caricarla a mano, digita:

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

Apri un nuovo thread. Codex carica la skill quando il task corrisponde. Per caricarla a mano, digita:

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

Verifica che sia stata installata:

```bash
agy plugin list
```

Avvia una nuova sessione. Antigravity CLI carica la skill quando il task corrisponde. Per caricarla a mano, digita:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Arrivi da Gemini CLI? Se `agy plugin import gemini` ha importato questa estensione, esegui comunque il comando di installazione qui sopra, così la copia attuale sostituisce quella importata.

</details>

<details>
<summary><strong>Qualsiasi altro agente che legge SKILL.md</strong></summary>

Copia la cartella `skills/building-with-typesafe-jev/` nella cartella delle skill del tuo agente. Copia la cartella intera. `SKILL.md` rimanda ai file che le stanno accanto.

</details>

## Configura una chiave API (facoltativa, consigliata)

La skill funziona anche senza chiave. Con `TYPESAFE_API_KEY` impostata nella shell dell'agente, l'agente può verificare il suo design con l'API live prima che il codice arrivi nel tuo progetto. Così trova i nomi di campo sbagliati e le domande che Jev legge in modo diverso da come le intendevi. Ogni chiamata costa una frazione di centesimo.

<details>
<summary><strong>Crea, salva e risolvi i problemi di una chiave</strong></summary>

<br>

<details>
<summary><strong>Crea una chiave</strong> (quattro passi nella console TypeSafe)</summary>

**Passo 1.** Accedi a [console.typesafe.ai](https://console.typesafe.ai/) e apri **API Keys** nella barra laterale.

<img src="../assets/api-key/step-1.png" alt="La home page della console TypeSafe. Un riquadro e una freccia color ambra indicano API Keys nella barra laterale sinistra." width="100%">

**Passo 2.** Fai clic su **Create key** in alto a destra.

<img src="../assets/api-key/step-2.png" alt="La pagina delle chiavi API. Le chiavi esistenti sono sfocate. Un riquadro e una freccia color ambra indicano il pulsante Create key in alto a destra." width="100%">

**Passo 3.** Dai alla chiave il nome del posto in cui verrà usata, per esempio il computer o l'agente. Poi fai clic su **Create key**.

<img src="../assets/api-key/step-3.png" alt="La finestra Create API key con il nome my-coding-agent inserito. Un riquadro e una freccia color ambra indicano il campo del nome e il pulsante Create key." width="100%">

**Passo 4.** Copia subito la chiave. La console la mostra una sola volta. Se la perdi, creane una nuova e revoca quella vecchia.

<img src="../assets/api-key/step-4.png" alt="La finestra API key created. Il valore della chiave è nascosto. Un riquadro e una freccia color ambra indicano il pulsante Copy." width="100%">

</details>

<details>
<summary><strong>Salva la chiave</strong> (macOS, Linux, Windows)</summary>

Tieni la chiave in un file dedicato, leggibile solo da te, ed esportala come `TYPESAFE_API_KEY`. Gli agenti spesso avviano shell senza terminale, quindi ogni sezione mette la chiave dove quelle shell possono vederla. Scegli il tuo sistema.

<details>
<summary><strong>macOS</strong> (zsh, la shell predefinita)</summary>

Salva la chiave in un file privato:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Caricala da `~/.zshenv`. Ogni zsh legge quel file, comprese le shell che gli agenti avviano senza terminale. `~/.zshrc` viene letto solo dalle shell interattive.

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

Apri un nuovo terminale e controlla. Il comando stampa la lunghezza della chiave, non la chiave:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux con bash</strong> (Ubuntu, Debian, Mint, Fedora, Arch)</summary>

Salva la chiave in un file privato:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Caricala dall'**inizio** di `~/.bashrc`. Ubuntu, Debian, Mint e Arch iniziano `~/.bashrc` con una riga che si ferma subito quando non c'è un terminale collegato. Una riga sotto quel controllo non viene mai eseguita per le shell degli agenti. L'inizio del file è sicuro su ogni distribuzione:

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

Apri un nuovo terminale e controlla:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux con zsh</strong></summary>

Segui i passaggi per macOS. zsh legge `~/.zshenv` allo stesso modo su Linux.

</details>

<details>
<summary><strong>Linux con fish</strong></summary>

fish legge ogni file in `~/.config/fish/conf.d/`, con o senza terminale:

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong> (PowerShell)</summary>

Salva la chiave come variabile d'ambiente utente. I nuovi terminali e le nuove app la vedono. I terminali già aperti no:

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

Apri un nuovo terminale e controlla:

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL:** per impostazione predefinita le variabili di Windows non arrivano a WSL. Dentro WSL, segui i passaggi per Linux con bash.

</details>

<details>
<summary><strong>App desktop ed estensioni per IDE</strong></summary>

Un'app avviata dal dock, dal menu Start o da un launcher del desktop non legge i file della tua shell.

- **Windows:** la variabile d'ambiente utente vista sopra copre già queste app.
- **Linux (systemd):** aggiungi la riga `TYPESAFE_API_KEY=YOUR_KEY` a `~/.config/environment.d/typesafe.conf`, poi esci e rientra nella sessione.
- **macOS:** avvia l'app da un terminale, oppure imposta la variabile nelle impostazioni dell'app stessa. macOS non ha un semplice file per utente che le app desktop leggono.

</details>

</details>

<details>
<summary><strong>Se l'agente non vede la chiave</strong></summary>

Chiedi all'agente di eseguire `echo ${#TYPESAFE_API_KEY}` (oppure `$env:TYPESAFE_API_KEY.Length` su Windows). Se stampa `0` o niente, controlla questi punti in ordine:

- **Hai avviato l'agente prima di salvare la chiave.** Le shell degli agenti copiano l'ambiente del programma che le ha avviate. Chiudi l'agente e avvialo da un nuovo terminale.
- **Hai avviato l'agente dal dock, dal menu Start o da un IDE.** Quelle app non leggono i file della tua shell. Vedi "App desktop ed estensioni per IDE" sopra.
- **Codex filtra l'ambiente.** Se `~/.codex/config.toml` imposta `include_only` sotto `[shell_environment_policy]`, aggiungi `TYPESAFE_API_KEY`. Se imposta `ignore_default_excludes = false`, Codex scarta ogni variabile che ha `KEY` nel nome. Rimuovi quella riga.
- **WSL.** Le variabili di Windows non arrivano a WSL. Salva la chiave dentro WSL con i passaggi per Linux.

</details>

</details>

## Come è stata testata

Abbiamo dato a un agente di coding sei task Jev, per esempio una funzione di triage per i ticket di supporto e un gate di approvazione per i comandi di shell. Ogni task è stato eseguito 10 volte con questa skill, senza skill e con la skill ufficiale, ogni configurazione nel proprio container isolato. L'agente aveva la documentazione ma nessuna chiave API, quindi i valutatori hanno controllato il codice che ha scritto. I controlli che richiedono giudizio sono andati a tre giudici LLM di tre fornitori diversi (Claude Opus, GPT-6 Sol, Kimi K3), e ha deciso la maggioranza.

| | Senza skill | Questa skill | Skill ufficiale |
|---|---:|---:|---:|
| Punteggio medio | 0.65 ± 0.05 | **0.96 ± 0.02** | 0.77 ± 0.04 |

Il punteggio è la quota di controlli superati, in media su 10 esecuzioni per task.

**Dove la skill ha fatto la differenza** (esecuzioni su 10 che hanno superato il controllo):

| Il codice dell'agente... | Senza skill | Questa skill | Skill ufficiale |
|---|---:|---:|---:|
| ha contato nel codice, invece di chiedere un numero a Jev | 1 | 8 | 0 |
| ha nominato un campo dell'input nelle sue domande | 0 | 10 | 1 |
| ha fissato o registrato la versione del modello Jev | 0 | 10 | 0 |
| ha dato all'elenco dei reparti un'opzione generica | 3 | 10 | 6 |
| ha tenuto più di un percorso mentre navigava tra 1,200 categorie | 1 | 10 | 7 |
| ha mantenuto una protezione in semplice codice per i comandi distruttivi | 7 | 10 | 2 |
| ha letto `score` come una posizione da 0 a n-1 | 9 | 10 | 5 |

[Vedi ogni controllo →](../../evals/docs/results.md#every-check)

Ognuna di queste righe supera l'assenza di skill, la skill ufficiale o entrambe con un margine superiore al caso, al 95%.

**Altri dettagli:**

- [evals/README.md](../../evals/README.md): risultati per caso e come eseguire la suite
- [evals/docs/results.md](../../evals/docs/results.md): ogni controllo, i punteggi di ciascun giudice, costi, token e metodo
- [evals/docs/cases.md](../../evals/docs/cases.md): i sei task e cosa verifica ogni controllo
- [evals/docs/harness.md](../../evals/docs/harness.md): come funziona un'esecuzione, i container isolati e come conservare un batch
- [evals/docs/lessons.md](../../evals/docs/lessons.md): cosa si è rotto mentre la suite veniva costruita

## Cosa contiene

La skill si carica a livelli, così l'agente legge solo quello che serve al task.

| File | Cosa contiene | Quando l'agente lo legge |
|---|---|---|
| `SKILL.md` | Quale primitiva scegliere, 11 regole di design, come usare probabilità e confidenza, errori comuni | In ogni task Jev |
| `api-reference.md` | API HTTP, SDK Python e JavaScript, limiti, errori, variabili d'ambiente | Quando scrive il codice |
| `patterns.md` | I 4 pattern ufficiali e le tecniche da 18 cookbook, con le relative soglie | Quando progetta un workflow |
| `prior-art/INDEX.md` | Una mappa da "cosa voglio costruire" a una forma, più le idee che non hanno funzionato | Prima di progettare qualcosa di nuovo |
| `prior-art/*.md` | 11 file di forma: uno sketch di codice, lezioni dal campo e progetti collegati | Uno o due per design |

## La libreria di esempi

La maggior parte dei cataloghi ordina i progetti per settore. Questa libreria li ordina per forma di implementazione. Un bot per videogiochi, un drone e un bot di trading hanno la stessa forma: un ciclo di controllo. Ordinati così, i tre condividono uno sketch di codice e un insieme di lezioni dal campo. Le 11 forme:

- **[Cicli di controllo](../../skills/building-with-typesafe-jev/prior-art/control-loops.md)**: giochi, droni, robot, mercati.
- **[Scelta tra candidati](../../skills/building-with-typesafe-jev/prior-art/select-from-candidates.md)**: agenti per browser e telefono, tool calling senza LLM, estrazione, router.
- **[Gate](../../skills/building-with-typesafe-jev/prior-art/gates.md)**: approvazione delle chiamate ai tool, controlli di "fatto", CI, denaro, contenuti.
- **[Filtri di stream](../../skills/building-with-typesafe-jev/prior-art/stream-filters.md)**: filtri anti-slop, moderazione, email, log, etichettatura in blocco.
- **[Ranking e matching](../../skills/building-with-typesafe-jev/prior-art/ranking-and-matching.md)**: reranker, entity matching, navigazione di grafi e tassonomie.
- **[Giudici e valutazioni](../../skills/building-with-typesafe-jev/prior-art/judges-and-evals.md)**: giudici con rubrica, valutazione delle tracce, code review come triage.
- **[Incrementale e in tempo reale](../../skills/building-with-typesafe-jev/prior-art/incremental-realtime.md)**: doppiaggio, voce, interfacce guidate dai tasti premuti.
- **[Contesto e memoria dell'agente](../../skills/building-with-typesafe-jev/prior-art/agent-context-memory.md)**: compattazione, gate sulla memoria, scadenza della memoria, controllo dello sforzo.
- **[Abbinamento a un LLM](../../skills/building-with-typesafe-jev/prior-art/llm-pairing.md)**: pianificatore ed esecutore, verifica e poi escalation, distillazione.
- **[Risposte come dati](../../skills/building-with-typesafe-jev/prior-art/research-and-features.md)**: feature per modelli classici, strumenti di ricerca, benchmark.
- **[Integrazione nell'infrastruttura](../../skills/building-with-typesafe-jev/prior-art/embedding-in-infrastructure.md)**: funzioni SQL, database vettoriali, hook di CI, Home Assistant.

L'indice elenca anche le idee che sul campo non hanno funzionato: scacchi, code review come unico revisore, percezione e calibrazione presa sulla fiducia. Un tentativo fallito evita al prossimo di ripeterlo.

## In cosa differisce dalla skill ufficiale

La [skill ufficiale di TypeSafe](https://github.com/typesafe-ai/skills) è un unico file di indicazioni di design. Per i dettagli dell'API, rimanda l'agente alla documentazione live in ogni task. Le due skill hanno nomi diversi e non vanno in conflitto, quindi puoi installarle entrambe, anche se le valutazioni non le hanno testate insieme.

Questa skill contiene di più al suo interno: le forme esatte dell'API, le soglie dei cookbook, i casi di errore raccolti dalla community e la libreria di esempi. L'agente può progettare senza passare dalla rete e vedere quello che altri hanno costruito prima.

Jev cambia in fretta. La skill è un'istantanea di [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) e della community al 2026-09-25, e dice all'agente che in caso di conflitto vale la documentazione live. Se un fatto è sbagliato, apri una issue con un link alla fonte.

## Crediti

I fatti sull'API vengono dalla documentazione pubblica e dai cookbook di TypeSafe AI. Gli esempi vengono da chi ha pubblicato i propri progetti, dalla community di Hacker News e da questi indici: [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases) e [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). Ogni file di forma rimanda ai progetti originali.

TypeSafe, Jev e System One sono nomi di TypeSafe AI. Questo progetto li usa solo per dire a cosa serve la skill.

## Licenza

MIT. Vedi [LICENSE](../../LICENSE).
