<p align="center">
  <img src="../assets/hero.png" alt="Building with TypeSafe Jev: decisioni tipizzate con confidenza calibrata, per il tuo agente di coding. Esempi da oltre 150 progetti della community, ordinati per forma. Due pannelli. A sinistra, un LLM con Structured Outputs restituisce JSON valido: reparto fatturazione, gravità medium, rimborso false (in rosso) e confidenza 0.95, ma quella confidenza è generata, non calibrata. A destra, una sola chiamata a Jev restituisce tre risposte tipizzate: una Choice (reparto: fatturazione, confidenza 0.88), uno Score (gravità: 1.43 su 2) e un Noul (rimborso: 0.99)." width="100%">
</p>

<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>Decisioni tipizzate con confidenza calibrata, per il tuo agente di coding.</em><br>
  <em>Esempi da oltre 150 progetti della community, ordinati per forma.</em>
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
  <strong>Italiano</strong> ·
  <a href="README.en-x-aibro.md">AI Bro</a>
</p>

> [!NOTE]
> Questa è una skill non ufficiale, della community. Non è creata, verificata o approvata da TypeSafe AI. TypeSafe pubblica la propria skill su [typesafe-ai/skills](https://github.com/typesafe-ai/skills). Vedi [In cosa differisce dalla skill ufficiale](#in-cosa-differisce-dalla-skill-ufficiale).

Gli agenti di coding trattano Jev come l'ennesimo modello di chat. Questa skill insegna loro a progettare per Jev: domande tipizzate, confidenza calibrata e una libreria di oltre 150 progetti della community ordinati per come funzionano. Si installa in Claude Code, Codex e Antigravity CLI.

## Installazione

<details>
<summary><strong>Claude Code</strong></summary>

Esegui questi due comandi nel terminale:

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

L'installazione potrebbe dire che un'opzione del plugin non è ancora impostata. Si tratta del test live, che resta disattivato finché non lo attivi. Vedi [Configura una chiave API](#configura-una-chiave-api-facoltativa-consigliata).

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

Avvia una nuova sessione. Antigravity CLI carica la skill quando il compito corrisponde. Per caricarla a mano, digita:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Arrivi da Gemini CLI? Se `agy plugin import gemini` ha importato questa estensione, esegui comunque il comando di installazione qui sopra. Sostituisce la copia importata, il cui comando delle impostazioni non funziona in Antigravity CLI.

</details>

<details>
<summary><strong>Qualsiasi altro agente che legge SKILL.md</strong></summary>

Copia la cartella `skills/building-with-typesafe-jev/` nella cartella delle skill del tuo agente. Copia la cartella intera. `SKILL.md` rimanda ai file che le stanno accanto.

</details>

## Configura una chiave API (facoltativa, consigliata)

La skill funziona anche senza chiave. Sceglie comunque le primitive, scrive le domande e il codice e li verifica con il suo riferimento dell'API. Con una chiave, testa anche ogni design con chiamate API reali prima che il codice arrivi nel tuo progetto. Così trova i nomi di campo sbagliati e le domande che Jev legge in modo diverso da come le intendevi. Ogni chiamata costa una frazione di centesimo, quindi ti consigliamo vivamente una chiave.

Il test live è disattivato finché non lo attivi. Finché è disattivato, la skill non cerca mai una chiave. Quando è attivo, legge la chiave solo dalla variabile d'ambiente che indichi tu (`TYPESAFE_API_KEY` se non ne scegli un'altra), ti avvisa prima della prima chiamata e si limita a circa 10 chiamate di prova per attività. Tre passi: crea una chiave, salvala e attiva il test live.

<details>
<summary><strong>Crea una chiave</strong> (quattro passi nella console TypeSafe)</summary>

**Passo 1.** Accedi a [console.typesafe.ai](https://console.typesafe.ai/) e apri **API Keys** (chiavi API) nella barra laterale.

<img src="../assets/api-key/step-1.png" alt="La home page della console TypeSafe. Un riquadro e una freccia color ambra indicano API Keys nella barra laterale sinistra." width="100%">

**Passo 2.** Fai clic su **Create key** (crea chiave) in alto a destra.

<img src="../assets/api-key/step-2.png" alt="La pagina delle chiavi API. Le chiavi esistenti sono sfocate. Un riquadro e una freccia color ambra indicano il pulsante Create key in alto a destra." width="100%">

**Passo 3.** Dai alla chiave il nome del posto in cui verrà usata, per esempio il computer o l'agente. Poi fai clic su **Create key**.

<img src="../assets/api-key/step-3.png" alt="La finestra Create API key con il nome my-coding-agent inserito. Un riquadro e una freccia color ambra indicano il campo del nome e il pulsante Create key." width="100%">

**Passo 4.** Copia subito la chiave. La console la mostra una sola volta. Se la perdi, creane una nuova e revoca quella vecchia.

<img src="../assets/api-key/step-4.png" alt="La finestra API key created. Il valore della chiave è nascosto. Un riquadro e una freccia color ambra indicano il pulsante Copy." width="100%">

</details>

<details>
<summary><strong>Salva la chiave</strong> (macOS, Linux, Windows)</summary>

Tieni la chiave in un file dedicato, leggibile solo da te. La skill legge la chiave da una variabile d'ambiente, mai da un file, quindi la variabile deve essere impostata nelle shell che il tuo agente avvia. Gli agenti spesso avviano shell senza terminale, quindi ogni sezione mette la chiave dove quelle shell possono vederla. Scegli il tuo sistema.

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
<summary><strong>Attiva il test live</strong> (Claude Code, Codex, Antigravity CLI)</summary>

Ogni agente conserva due impostazioni: il test live (`on` o `off`, predefinito `off`) e il nome della variabile che contiene la tua chiave (predefinito `TYPESAFE_API_KEY`). Impostale una volta sola. Valgono dalla sessione successiva. Gli script di supporto richiedono Python 3; quello per Codex richiede la 3.11 o successiva.

**Claude Code.** Esegui questo comando nel terminale:

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev --config live_testing=on
```

Se la tua chiave è in una variabile con un altro nome, aggiungi `--config key_env_var=YOUR_VARIABLE`. In una sessione, `/plugin configure building-with-typesafe-jev@building-with-typesafe-jev` modifica le stesse impostazioni.

**Codex.** Codex non ha impostazioni per i plugin, quindi la skill le conserva in `~/.codex/config.toml`, che Codex passa a ogni shell avviata dall'agente. In una sessione, digita:

```
$building-with-typesafe-jev:jev-settings live on
```

Codex chiede di approvare la scrittura. Per fare la modifica a mano, aggiungi queste righe a `~/.codex/config.toml`:

```toml
[shell_environment_policy.set]
JEV_LIVE_TESTING = "on"
JEV_KEY_ENV_VAR = "TYPESAFE_API_KEY"
```

Codex chiede anche di approvare una volta l'hook di avvio sessione del plugin. All'inizio di ogni sessione, l'hook dice all'agente se il test dal vivo è attivo e se la variabile della chiave è impostata, mai la chiave stessa. In una sessione, digita `/hooks` e approvalo. Codex lo chiede di nuovo quando un aggiornamento cambia l'hook. Finché non lo approvi, l'hook non viene eseguito e la skill controlla comunque le impostazioni da sola.

**Antigravity CLI.** Antigravity CLI non ha impostazioni per i plugin, ma la shell dell'agente eredita l'ambiente del terminale che ha avviato `agy`. Quindi le impostazioni sono due variabili d'ambiente, da impostare dove hai salvato la chiave. Con la chiave in `~/.config/typesafe/env`, esegui questo comando, poi apri un nuovo terminale e riavvia `agy`:

```bash
echo 'export JEV_LIVE_TESTING=on' >> ~/.config/typesafe/env
```

Se la chiave è in una variabile con un altro nome, aggiungi `export JEV_KEY_ENV_VAR=YOUR_VARIABLE` allo stesso modo. Su fish o Windows, imposta `JEV_LIVE_TESTING` a `on` nello stesso modo in cui hai salvato la chiave.

**Verifica.** Avvia una nuova sessione ed esegui il comando delle impostazioni: `/building-with-typesafe-jev:jev-settings` in Claude Code, `$building-with-typesafe-jev:jev-settings` in Codex oppure `/building-with-typesafe-jev:jev-settings` in Antigravity CLI. Mostra entrambe le impostazioni e se la shell dell'agente vede la chiave. Stampa la lunghezza della chiave, mai la chiave.

**CI e container.** Le variabili d'ambiente `JEV_LIVE_TESTING` e `JEV_KEY_ENV_VAR` hanno la precedenza sulle impostazioni salvate in ogni agente.

</details>

<details>
<summary><strong>Se l'agente non vede la chiave</strong></summary>

Il comando delle impostazioni dice `key: not set in this shell` quando la shell dell'agente non ha quella variabile. Controlla questi punti in ordine:

- **Hai avviato l'agente prima di salvare la chiave.** Le shell degli agenti copiano l'ambiente del programma che le ha avviate. Chiudi l'agente e avvialo da un nuovo terminale.
- **Hai avviato l'agente dal dock, dal menu Start o da un IDE.** Quelle app non leggono i file della tua shell. Vedi "App desktop ed estensioni per IDE" sopra.
- **Codex filtra l'ambiente.** Se `~/.codex/config.toml` imposta `include_only` sotto `[shell_environment_policy]`, aggiungi la variabile della chiave, `JEV_LIVE_TESTING` e `JEV_KEY_ENV_VAR`. Se imposta `ignore_default_excludes = false`, Codex scarta ogni variabile che ha `KEY` nel nome. Rimuovi quella riga.
- **WSL.** Le variabili di Windows non arrivano a WSL. Salva la chiave dentro WSL con i passaggi per Linux.

</details>

La skill non stampa mai la chiave, non la registra nei log e non la scrive nel codice. Legge solo la variabile che indichi tu e passa la chiave a ogni comando di prova senza metterla su una riga di comando.

## Cosa fa

Un LLM può restituire JSON, e con Structured Outputs il JSON si analizza ogni volta. Può comunque essere sbagliato, e niente nell'output ti dice quanto spesso. Uno schema fissa la forma della risposta, non la risposta. Il campo del reparto dice "billing" sia che il modello lo sapesse, sia che abbia tirato a indovinare. Se aggiungi un campo di confidenza, il modello scrive quel numero nello stesso modo in cui scrive la risposta. Il numero non è calibrato rispetto a niente.

[Jev](https://docs.typesafe.ai/introduction) è un modello [System One](https://docs.typesafe.ai/concepts/system-one) di TypeSafe AI. Non scrive testo. Le sue probabilità sono ottimizzate rispetto ai risultati reali, non campionate da un decoder, e la maggior parte delle query risponde in 100-200 ms. Gli invii un contenuto, per esempio un ticket di assistenza, e un insieme di domande. Lui risponde a ogni domanda con un valore tipizzato e una probabilità calibrata. Non c'è testo da analizzare. Una domanda può essere di tre tipi:

- **Choice** sceglie un'opzione da un elenco che fornisci tu. Esempio: il prossimo passo di un agente, tra cercare nella documentazione, eseguire i test o chiedere all'utente. È routing dei tool senza un LLM nel ciclo.
- **Score** colloca il contenuto su una scala che descrivi passo per passo. Esempio: valutare la pull request di un agente sulla scala ignora la specifica → rispetta in parte la specifica → rispetta la specifica. Si posiziona a 1.6, quasi del tutto conforme alla specifica.
- **Noul** dà la probabilità che un'affermazione sì/no sia vera. Esempio: "questo comando di shell elimina file fuori dal progetto" restituisce 0.97, e un gate di approvazione ferma il comando prima che venga eseguito.

Leggere il riferimento dell'API è la parte facile. La parte difficile è progettare per un modello che non scrive testo. Un agente senza questa skill trova un tutorial, indovina il resto dell'API e porta le abitudini del "prompt e parsing" in un modello nato per sostituirle. Questa skill dà all'agente l'API, le regole di design, i casi di errore noti e una mappa di quello che altri hanno già costruito. La documentazione descrive il modello. La skill mostra come progettare per esso.

## Cosa cambia

Abbiamo dato a un agente di coding sei task Jev, per esempio una funzione di triage per i ticket di supporto e un gate di approvazione per i comandi di shell. L'agente aveva la documentazione ma nessuna chiave API, quindi i valutatori hanno controllato il codice che ha scritto, non ciò che quel codice faceva con Jev. Ogni task è stato eseguito 10 volte in ciascuna di tre configurazioni, tutto avviato insieme in un unico batch di eval.

| | Senza skill | Questa skill | Skill ufficiale |
|---|---:|---:|---:|
| Punteggio medio | 0.65 | 0.96 | 0.77 |

Un punteggio è la quota di controlli superati da un'esecuzione. Ogni media è precisa entro 0.05, con una confidenza del 95%.

### Dove questa skill ha fatto la differenza

Questi sono i controlli in cui il divario tra questa skill e nessuna skill è troppo ampio per essere un caso, secondo un test al 95% sui conteggi dei superamenti. Ogni numero indica quante esecuzioni su 10 hanno superato il controllo.

| Il codice dell'agente... | Senza skill | Questa skill | Skill ufficiale |
|---|---:|---:|---:|
| ha contato nel codice, invece di chiedere un numero a Jev | 1 | 8 | 0 |
| ha nominato un campo dell'input nelle sue domande | 0 | 10 | 1 |
| ha fissato o registrato la versione del modello Jev | 0 | 10 | 0 |
| ha tenuto più di un percorso mentre navigava tra 1,200 categorie | 1 | 10 | 7 |
| ha dato all'elenco dei reparti un'opzione generica | 3 | 10 | 6 |
| ha posto al gate sui comandi più di una domanda sì/no | 5 | 10 | 9 |
| ha posto una domanda per ogni voce della rubrica e ha calcolato il voto nel codice | 5 | 10 | 10 |

Un pattern match valuta tre di questi controlli. Gli altri quattro vanno a tre giudici LLM di tre fornitori diversi, Claude Opus, GPT-6 Sol e Kimi K3, e decide la maggioranza. L'agente è un modello Claude, quindi un giudice Claude non decide mai da solo.

### Rispetto alla skill ufficiale

Con lo stesso test, questa skill ha superato più spesso della skill ufficiale otto controlli. Quattro sono nella tabella: conteggi, nomi dei campi, versione del modello e opzione generica. Gli altri quattro:

- ha mantenuto una regola in semplice codice che blocca un comando distruttivo, o lo inoltra a una persona, qualunque cosa dica Jev: 10 esecuzioni contro 2
- ha letto le probabilità di gravità tramite le loro chiavi intere: 10 contro 4
- ha letto `score` come una posizione da 0 a n-1: 10 contro 5
- ha limitato l'etichettatore dei log a 8 richieste simultanee o meno: 10 contro 6

### Dove non ha fatto differenza

- Un controllo divide i giudici, quindi non è nella tabella. Con Opus e GPT-6 Sol, questa skill non ha lasciato che la motivazione dell'agente stesso approvasse un comando in 10 esecuzioni, contro 5 senza skill. Kimi K3 ha promosso 9 di quelle 10 esecuzioni senza skill.
- L'instradamento in base a `confidence` è stato superato in 2 esecuzioni su 10 con questa skill e in 2 su 10 senza skill. Il task non diceva mai dove mandare un ticket incerto, quindi la maggior parte degli agenti ha restituito il valore di confidenza e ha lasciato la decisione al chiamante. La skill stessa dice che va bene quando il codice sceglie solo l'opzione migliore. Ora il task indica un fallback, e il prossimo batch di eval lo metterà alla prova.
- Ogni altro controllo è stato superato in quasi tutte le esecuzioni in tutte e tre le configurazioni, oppure ha mostrato una differenza inferiore a quella attribuibile al caso.

Il [README degli eval](../../evals/README.md) riporta ogni controllo con il suo intervallo e come eseguire la suite.

## Cosa contiene

La skill si carica a livelli, così l'agente legge solo quello che serve al task. Un unico file grande costerebbe all'agente token e attenzione in ogni task, prima ancora di scrivere una riga di codice.

| File | Cosa contiene | Quando l'agente lo legge |
|---|---|---|
| `SKILL.md` | Quale primitiva scegliere, 11 regole di design, come usare probabilità e confidenza, cosa fare quando una risposta è sbagliata, errori comuni | In ogni task Jev |
| `api-reference.md` | API HTTP, SDK Python e JavaScript, limiti, errori, variabili d'ambiente | Quando scrive il codice |
| `patterns.md` | I 4 pattern ufficiali e le tecniche da 18 cookbook, con le relative soglie | Quando progetta un workflow |
| `prior-art/INDEX.md` | Una mappa da "cosa voglio costruire" a una forma, più le idee che non hanno funzionato | Prima di progettare qualcosa di nuovo |
| `prior-art/*.md` | 11 file di forma: uno sketch di codice, lezioni dal campo e progetti collegati | Uno o due per design |
| `scripts/jev_live.py` | Legge le impostazioni del test live ed esegue un comando di prova con la chiave | Prima di una chiamata di test live |
| `../jev-settings/` | Il comando delle impostazioni per Claude Code, Codex e Antigravity CLI | Quando lo esegui |

## La libreria di esempi

La maggior parte dei cataloghi ordina i progetti per settore. Questa libreria li ordina per forma di implementazione. Un bot per videogiochi, un drone e un bot di trading hanno la stessa forma: un ciclo di controllo. Ordinati così, i tre condividono uno sketch di codice e un insieme di lezioni dal campo. Le 11 forme:

- **Cicli di controllo**: giochi, droni, robot, mercati.
- **Scelta tra candidati**: agenti per browser e telefono, tool calling senza LLM, estrazione, router.
- **Gate**: approvazione delle chiamate ai tool, controlli di "fatto", CI, denaro, contenuti.
- **Filtri di stream**: filtri anti-slop, moderazione, email, log, etichettatura in blocco.
- **Ranking e matching**: reranker, entity matching, navigazione di grafi e tassonomie.
- **Giudici e valutazioni**: giudici con rubrica, valutazione delle tracce, code review come triage.
- **Incrementale e in tempo reale**: doppiaggio, voce, interfacce guidate dai tasti premuti.
- **Contesto e memoria dell'agente**: compattazione, gate sulla memoria, scadenza della memoria, controllo dello sforzo.
- **Abbinamento a un LLM**: pianificatore ed esecutore, verifica e poi escalation, distillazione.
- **Risposte come dati**: feature per modelli classici, strumenti di ricerca, benchmark.
- **Integrazione nell'infrastruttura**: funzioni SQL, database vettoriali, hook di CI, Home Assistant.

L'indice elenca anche le idee che sul campo non hanno funzionato: scacchi, code review come unico revisore, percezione e calibrazione presa sulla fiducia. Un tentativo fallito evita al prossimo di ripeterlo.

## Come è stata testata

Abbiamo testato la skill come si testa il codice: prima la si guarda fallire, poi la si corregge.

1. Abbiamo eseguito un task di triage senza skill e annotato ogni ipotesi e ogni errore.
2. Abbiamo scritto la skill per correggere quegli errori.
3. Un agente nuovo ha eseguito lo stesso task con la skill, poi ha elencato cosa non era chiaro. Abbiamo colmato sei lacune.
4. Abbiamo verificato i fatti sull'API contenuti nella skill con l'API live, usando l'SDK Python 0.7.1 e il modello `jev-1.13.0`.
5. Abbiamo eseguito tre degli sketch di codice della libreria di esempi con l'API live. Un'esecuzione ha mostrato che Jev legge i controlli sulle allucinazioni alla lettera, e questa lezione ora è nella skill.
6. Un agente nuovo ha provato tre nuovi design con il solo indice. Ha trovato la forma giusta per ciascuno e ha segnalato due lacune. Le abbiamo colmate entrambe.
7. Abbiamo installato il plugin in Claude Code, Codex e Antigravity CLI, e verificato che ognuno carichi la skill.
8. Abbiamo eseguito sei casi di eval dieci volte ciascuno con questa skill, senza skill e con la skill ufficiale, ogni configurazione nel proprio container isolato. Vedi [Cosa cambia](#cosa-cambia) e il [README degli eval](../../evals/README.md).

## Mantenerla aggiornata

Jev cambia in fretta. La skill è un'istantanea di [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) e della community al 2026-09-25. Dice all'agente che in caso di conflitto vale la documentazione live, e mostra come scaricarla in Markdown. Se un fatto nella skill è sbagliato, apri una issue con un link alla fonte.

## In cosa differisce dalla skill ufficiale

La [skill ufficiale di TypeSafe](https://github.com/typesafe-ai/skills) è breve e rimanda l'agente alla documentazione live. È la fonte giusta per i dettagli aggiornati dell'API. Se vuoi, installa anche quella.

Questa skill contiene di più al suo interno: le forme esatte dell'API, le soglie dei cookbook, i casi di errore raccolti dalla community e la libreria di esempi. Un agente può progettare senza passare dalla rete, e può trovare quello che altri hanno costruito prima di iniziare.

Sui sei task di eval, la skill ufficiale ha ottenuto 0.77 ± 0.04, contro 0.65 ± 0.05 senza skill e 0.96 ± 0.02 con questa. Vedi il [README degli eval](../../evals/README.md).

## Crediti

I fatti sull'API vengono dalla documentazione pubblica e dai cookbook di TypeSafe AI. Gli esempi vengono da chi ha pubblicato i propri progetti, dalla community di Hacker News e da questi indici: [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases) e [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). Ogni file di forma rimanda ai progetti originali.

TypeSafe, Jev e System One sono nomi di TypeSafe AI. Questo progetto li usa solo per dire a cosa serve la skill.

## Licenza

MIT. Vedi [LICENSE](../../LICENSE).
