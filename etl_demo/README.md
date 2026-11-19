# Demo «Python e VS Code nei flussi ETL»

Progetto dimostrativo per una demo di circa un'ora rivolta ai partecipanti di un corso Python in ambito bancario. Mostra come si costruisce, si esegue e si rende affidabile un flusso **ETL** scritto in Python, lavorando in **VS Code** avviato da un **ambiente conda**.

**ETL** è la sigla di *Extract, Transform, Load*: estrarre i dati dalle sorgenti, trasformarli, caricarli nella destinazione. È il lavoro che oggi in banca viene svolto con IBM DataStage.

I tre temi su cui la demo insiste sono:

1. **gli strumenti di VS Code**: avvio dall'ambiente conda, notebook, visualizzazione delle tabelle, debug, test, Git;
2. **la robustezza da produzione**: parametri, log, scarti, quadratura dei conteggi, rieseguibilità, test automatici, schedulazione;
3. **le prestazioni sui grandi volumi**: che cosa fare quando pandas non basta (Polars, DuckDB, formato Parquet).

La traccia da seguire durante la demo, minuto per minuto, è nel file [`SCALETTA_DEMO.md`](SCALETTA_DEMO.md).

---

## 1. Assunzioni

Il progetto è costruito su queste assunzioni. Se una non vale, la parte corrispondente va adattata.

1. **Prodotto IBM.** Con «Data Staging di IBM» si intende **IBM DataStage**, lo strumento grafico di IBM per i flussi ETL, in cui un flusso (*job*) si disegna collegando dei blocchi (*stage*) con delle frecce (*link*).
2. **Platea.** I partecipanti hanno seguito un corso Python di tre giorni e formano una platea mista: una parte si occupa di flussi ETL, gli altri di altro. Per questo ogni termine è spiegato e il codice usa solo costrutti di base (funzioni, dizionari, DataFrame).
3. **Durata.** La demo dura circa un'ora ed è mostrata dal docente: i partecipanti osservano, non eseguono.
4. **Macchina.** La demo gira sul PC del docente con Windows, VS Code e un ambiente conda creato con Miniconda dal solo canale conda-forge. Non serve alcun accesso ai sistemi della banca né a Internet durante la demo.
5. **Dati.** Tutti i dati sono **sintetici**, cioè inventati da uno script: nessun cliente, conto o movimento è reale. Anche i cambi sono verosimili ma inventati.
6. **Destinazione.** Il database di destinazione è **SQLite**: un database contenuto in un unico file, che non richiede alcun server e che Python gestisce con il modulo standard `sqlite3`. Fa le veci del database aziendale.
7. **Libreria principale.** Il flusso usa **pandas**, la libreria Python più diffusa per lavorare con tabelle di dati. Polars e DuckDB compaiono solo nel notebook sui grandi volumi.
8. **Forma del codice.** Il flusso vero e proprio è scritto in file `.py`, come si farebbe in produzione; i notebook servono per l'esplorazione dei dati e per il confronto delle prestazioni.
9. **Lingua e stile.** Materiali in italiano, nella forma «noi», con commenti abbondanti e ogni termine spiegato alla prima comparsa.
10. **Versioni.** Python 3.13, pandas 3.0, Polars 2.0, DuckDB 2.0. Il codice funziona da Python 3.11 in poi.

> **Una differenza rispetto alle assunzioni iniziali.** In un primo momento si era ipotizzato di raggiungere SQLite attraverso la libreria SQLAlchemy. Il progetto usa invece direttamente il modulo standard `sqlite3`: non richiede installazioni, lascia visibili i comandi SQL (cosa utile per chi viene dal mondo ETL) e ha permesso di collaudare per intero il caricamento. Il passaggio a un database aziendale è descritto nella sezione 8.

---

## 2. Lo scenario

Ogni giorno arriva un file con i **movimenti di conto corrente** della giornata. Il flusso deve controllarli, arricchirli con le anagrafiche, convertirli in euro e caricarli in un piccolo database di analisi, insieme a un riepilogo per filiale e causale.

```
 SORGENTI                       TRASFORMAZIONI                          DESTINAZIONI

 movimenti_AAAAMMGG.csv  --+
 (uno al giorno)           |    1. controllo di date e importi
                           |    2. eliminazione delle righe ripetute     datamart.db (SQLite)
 conti.csv  ---------------+--> 3. aggiunta di cliente, filiale,    -->    - movimenti
 clienti.csv  -------------+       segmento                               - riepilogo_giornaliero
                           |    4. conversione in euro                    - log_esecuzioni
 cambi.xlsx  --------------+    5. flag «rilevante»
 (file Excel)                   6. riepilogo per filiale e causale
                                        |
                                        +--> scarti_movimenti_AAAAMMGG.csv
                                             (righe scartate, con il motivo)
```

Nei file dei movimenti sono stati inseriti **di proposito** alcuni errori, perché un flusso serio deve saperli riconoscere:

| Problema | Esempio | Che cosa fa il flusso |
|---|---|---|
| Data non valida | `31/02/2026`, data vuota, `2026-11-17` | scarta la riga (`DATA_NON_VALIDA`) |
| Importo non valido | `n.d.`, importo vuoto, `1234.56` | scarta la riga (`IMPORTO_NON_VALIDO`) |
| Riga ripetuta | lo stesso `id_movimento` due volte | tiene la prima, scarta la ripetizione (`DUPLICATO`) |
| Conto inesistente | conto non presente in `conti.csv` | scarta la riga (`CONTO_INESISTENTE`) |
| Cambio mancante | movimento in yen, ma lo yen non è nella tabella dei cambi | scarta la riga (`CAMBIO_MANCANTE`) |
| Codice scritto in modo diverso | ` eur`, `pos  ` | ripulisce il codice e tiene la riga |

I file a disposizione coprono tre situazioni:

| Data di elaborazione | File | Che cosa succede | Codice di uscita |
|---|---|---|---|
| `2026-11-16` e `2026-11-17` | file normali | 20.100 righe lette, 310 scartate (1,5%), 19.790 caricate | `0` |
| `2026-11-18` | file volutamente corrotto | 6.310 righe scartate (31,4%): oltre la soglia del 5%, il flusso si ferma e non carica nulla | `1` |
| `2026-11-19` | il file non esiste | il flusso si ferma subito con un messaggio chiaro | `1` |

Il **codice di uscita** è il numero con cui un programma comunica l'esito a chi lo ha lanciato: `0` significa «tutto bene», un numero diverso da zero segnala un problema.

---

## 3. Contenuto della cartella

```
demo_etl_python/
│
├── README.md                    questo documento
├── SCALETTA_DEMO.md             la traccia della demo, minuto per minuto
├── environment.yml              descrizione dell'ambiente conda
├── config.toml                  parametri del flusso (cartelle, soglie)
├── esegui_etl.py                il programma da lanciare
├── pytest.ini                   configurazione dei test automatici
│
├── etl/                         il codice del flusso
│   ├── configurazione.py            lettura dei parametri
│   ├── log.py                       preparazione del log
│   ├── estrazione.py                E: lettura delle sorgenti
│   ├── trasformazione.py            T: controlli, pulizia, arricchimento, riepilogo
│   ├── controlli.py                 quadratura e soglia degli scarti
│   ├── caricamento.py               L: scrittura nel database
│   └── flusso.py                    i passi del flusso, uno dopo l'altro
│
├── tests/                       i test automatici
│   ├── test_trasformazione.py       una regola alla volta, su poche righe
│   ├── test_caricamento.py          il caricamento «o tutto o niente»
│   └── test_flusso_completo.py      l'intero flusso sui file veri
│
├── notebook/
│   ├── 01_esplorazione_sorgenti.ipynb    guardare i dati prima di costruire il flusso
│   └── 02_grandi_volumi.ipynb            pandas, Polars e DuckDB a confronto
│
├── strumenti/                   script di servizio
│   ├── verifica_ambiente.py         controllo da fare prima della demo
│   ├── genera_dati.py               crea i file di input
│   ├── genera_file_grande.py        crea il file da milioni di righe per il notebook 02
│   └── azzera_risultati.py          cancella database, scarti e log
│
├── schedulazione/
│   └── esegui_etl.bat               lancio del flusso da uno schedulatore
│
├── .vscode/                     impostazioni di VS Code per questa cartella
│   ├── launch.json                  configurazioni di avvio e debug
│   ├── settings.json                test, codifica dei file
│   └── extensions.json              estensioni consigliate
│
├── dati/
│   ├── input/                       i file sorgente (già presenti)
│   ├── output/                      il database, creato dal flusso
│   ├── scarti/                      i file degli scarti, creati dal flusso
│   └── grandi_volumi/               il file grande, da generare
│
└── log/                         i file di log, creati dal flusso
```

---

## 4. Preparazione (una volta sola)

### 4.1 Che cosa deve essere già installato

- **Miniconda**: il programma che crea e gestisce gli ambienti conda. Un *ambiente conda* è una cartella con una propria copia di Python e i soli pacchetti che servono a un progetto, isolati dal resto del computer.
- **VS Code** con le estensioni **Python**, **Jupyter** e **Data Wrangler** (tutte di Microsoft). Aprendo la cartella del progetto, VS Code propone da solo di installare quelle mancanti.

### 4.2 Creare l'ambiente conda

Aprire il **Prompt di Anaconda** (dal menu Start: *Anaconda Prompt*) ed eseguire i comandi seguenti. Tutti i pacchetti vengono presi dal solo canale conda-forge; l'opzione `--override-channels` fa ignorare qualunque altro canale configurato.

```
conda create -n etl_demo -c conda-forge --override-channels python=3.13
conda activate etl_demo
conda install -c conda-forge --override-channels pandas=3.0 openpyxl pyarrow polars python-duckdb pytest ipykernel
```

Tutti i pacchetti richiesti sono disponibili su conda-forge: non serve alcuna installazione con `pip`.

| Pacchetto | A che cosa serve |
|---|---|
| `pandas` | tabelle di dati: è la libreria principale del flusso |
| `openpyxl` | lettura dei file Excel (pandas la usa dietro le quinte) |
| `pyarrow` | formato Parquet e colonne di testo più efficienti in pandas |
| `polars` | motore alternativo per i grandi volumi (notebook 02) |
| `python-duckdb` | DuckDB, per interrogare i file con il linguaggio SQL (notebook 02) |
| `pytest` | test automatici |
| `ipykernel` | permette a VS Code di eseguire i notebook in questo ambiente |

In alternativa, lo stesso ambiente si crea con un solo comando a partire dal file `environment.yml`:

```
conda env create -f environment.yml
```

### 4.3 Avviare VS Code dall'ambiente conda

Sempre dal Prompt di Anaconda, con l'ambiente attivo:

```
conda activate etl_demo
cd /d C:\percorso\della\cartella\demo_etl_python
code .
```

Il comando `code .` apre VS Code sulla cartella corrente (il punto significa «questa cartella»).

**Perché avviarlo così.** Un ambiente conda non è fatto solo del programma `python.exe`: contiene anche le librerie di sistema di cui i pacchetti hanno bisogno. L'attivazione dell'ambiente dice a Windows dove trovarle. VS Code, avviato da un prompt in cui l'ambiente è già attivo, eredita queste impostazioni e riconosce l'ambiente da usare.

**Due controlli da fare sempre, appena aperto VS Code:**

1. **L'interprete selezionato.** Aprire un file `.py`: nella barra di stato in basso a destra deve comparire `etl_demo`. Se compare altro, aprire la *Command Palette* (la riga di comando di VS Code) con `Ctrl+Maiusc+P`, scrivere `Python: Select Interpreter` e scegliere `etl_demo`.
2. **Il Python del terminale.** Aprire un terminale dal menu *Terminal → New Terminal* ed eseguire:

   ```
   python -c "import sys; print(sys.executable)"
   ```

   Il percorso stampato deve contenere `etl_demo`.

> I nomi dei menu e dei comandi sono riportati in inglese, come compaiono in VS Code quando non è installato il pacchetto della lingua italiana.

### 4.4 Verificare che tutto funzioni

Dal terminale di VS Code:

```
python strumenti/verifica_ambiente.py
```

Lo script controlla la versione di Python, le librerie, i file di input e il funzionamento di ogni strumento usato nella demo. Deve terminare con la riga `TUTTO A POSTO`.

Poi eseguire i test automatici:

```
pytest
```

Devono risultare **17 test superati** (`17 passed`).

### 4.5 Generare il file grande per il notebook 02

```
python strumenti/genera_file_grande.py
```

Crea `dati/grandi_volumi/movimenti_grande.csv` con 5 milioni di righe (circa 210 MB). Per un confronto più marcato si può aumentare il numero di righe, ad esempio `--righe 20000000`.

### 4.6 Mettere il progetto sotto Git (per la parte della demo sulle differenze)

**Git** è il sistema che conserva la storia delle modifiche di un progetto. Dal terminale di VS Code:

```
git init
git add .
git commit -m "Versione iniziale della demo"
```

In alternativa, usare il pulsante **Initialize Repository** nella vista *Source Control* di VS Code.

---

## 5. Uso

### 5.1 Eseguire il flusso

Dal terminale di VS Code, nella cartella del progetto:

```
python esegui_etl.py --data 2026-11-17
```

L'argomento `--data` è la **data di elaborazione**, cioè il giorno a cui si riferiscono i dati da caricare: decide quale file leggere e con quale data vengono marcate le righe nel database. Per vedere tutte le opzioni: `python esegui_etl.py --help`.

Per leggere il codice di uscita subito dopo l'esecuzione:

| Terminale | Comando |
|---|---|
| PowerShell (quello predefinito di VS Code su Windows) | `echo $LASTEXITCODE` |
| Prompt dei comandi | `echo %ERRORLEVEL%` |

### 5.2 Dove guardare i risultati

| Che cosa | Dove |
|---|---|
| Il racconto dell'esecuzione | sul terminale e nel file `log/etl_AAAAMMGG.log` |
| Le righe scartate, con il motivo | `dati/scarti/scarti_movimenti_AAAAMMGG.csv` |
| I dati caricati | `dati/output/datamart.db`, tabelle `movimenti` e `riepilogo_giornaliero` |
| Lo storico di tutte le esecuzioni | `dati/output/datamart.db`, tabella `log_esecuzioni` |

Il modo più comodo per interrogare il database è l'ultima sezione del notebook `01_esplorazione_sorgenti.ipynb`.

### 5.3 Eseguire i test

Dal terminale con il comando `pytest`, oppure dalla vista **Testing** di VS Code (l'icona a forma di ampolla nella barra laterale).

### 5.4 Eseguire il flusso in debug

Il **debug** è l'esecuzione controllata di un programma: lo si ferma su una riga, si guarda il contenuto delle variabili e si prosegue un'istruzione alla volta.

1. Aprire `etl/trasformazione.py` e fare clic a sinistra del numero di una riga: compare un pallino rosso, il **punto di interruzione** (*breakpoint*).
2. Aprire la vista **Run and Debug** (`Ctrl+Maiusc+D`), scegliere `ETL: giorno normale (2026-11-17)` e premere `F5`.
3. Quando l'esecuzione si ferma: `F10` esegue una riga, `F5` riprende fino al prossimo punto di interruzione.

### 5.5 Ripartire da zero

```
python strumenti/azzera_risultati.py
```

Cancella database, scarti e log, senza toccare i file di input.

### 5.6 Rigenerare i file di input

```
python strumenti/genera_dati.py
```

Il generatore usa un seme fisso: produce sempre gli stessi dati, quindi i numeri citati in questo documento e nella scaletta restano validi.

Dopo una rigenerazione Git segnala come modificato il solo file `cambi.xlsx`, anche se il suo contenuto è identico: il formato Excel registra al proprio interno la data di creazione del file. La segnalazione si può annullare con **Discard Changes**.

---

## 6. Le parole usate nel progetto

| Termine | Significato |
|---|---|
| **ETL** | *Extract, Transform, Load*: estrarre i dati dalle sorgenti, trasformarli, caricarli nella destinazione. |
| **Flusso** | L'insieme ordinato dei passi che portano i dati dalle sorgenti alla destinazione. In DataStage si chiama *job*. |
| **Ambiente conda** | Una cartella con una propria copia di Python e i soli pacchetti necessari a un progetto. |
| **Canale** | L'archivio da cui conda scarica i pacchetti. Qui usiamo solo conda-forge, gestito dalla comunità. |
| **Interprete** | Il programma `python` che esegue il nostro codice. Ogni ambiente conda ha il proprio. |
| **Notebook** | Documento fatto di celle di testo e celle di codice eseguibili una alla volta. |
| **pandas** | La libreria Python più diffusa per lavorare con tabelle di dati. |
| **DataFrame** | La tabella di pandas: righe e colonne, come un foglio di calcolo. |
| **Scarto** | Riga che non supera un controllo: non viene caricata, ma viene conservata con il motivo. |
| **Quadratura** | Controllo che ogni riga letta sia stata o caricata o scartata: `lette = caricate + scartate`. |
| **Data di elaborazione** | Il giorno a cui si riferiscono i dati che stiamo caricando. |
| **Rieseguibilità** | La possibilità di rilanciare il flusso per la stessa data senza creare doppioni. |
| **Transazione** | Gruppo di comandi che il database tratta come un blocco unico: o riescono tutti, o non ne resta nessuno. |
| **Log** | Il diario di bordo del flusso: una riga per ogni fatto importante. |
| **Codice di uscita** | Il numero con cui un programma comunica l'esito a chi lo ha lanciato: `0` = tutto bene. |
| **Schedulatore** | Il programma che avvia i flussi a orari prestabiliti. |
| **Test automatico** | Piccola funzione che esegue un pezzo di codice su un caso noto e verifica che il risultato sia quello atteso. |
| **Debug** | Esecuzione controllata di un programma, con la possibilità di fermarlo e ispezionarlo. |
| **Git** | Il sistema che conserva la storia delle modifiche di un progetto. |
| **SQLite** | Database contenuto in un unico file, senza server, incluso in Python. |
| **Parquet** | Formato di file «a colonne», compatto e veloce da leggere, pensato per l'analisi dei dati. |

---

## 7. Per chi viene da DataStage

La tabella mette a fianco i concetti di DataStage, nella sua versione classica, e il loro corrispondente in questo progetto. Nella demo è usata solo in chiusura, come ponte per chi lavora già con i flussi ETL.

| In DataStage | In questo progetto |
|---|---|
| Job | la funzione `esegui_flusso` in `etl/flusso.py` |
| Stage Sequential File | `pd.read_csv` e `to_csv`, in `etl/estrazione.py` |
| Stage connettore verso un database | il modulo `sqlite3`, in `etl/caricamento.py` |
| Stage Transformer (derivazioni e vincoli) | le funzioni di `etl/trasformazione.py` |
| Stage Lookup e Join | il metodo `merge` dei DataFrame |
| Stage Remove Duplicates | il metodo `duplicated` |
| Stage Aggregator | `groupby` seguito da `agg` |
| Link di reject | la tabella degli scarti, con la colonna `motivo_scarto` |
| Parametri del job e Parameter Set | l'argomento `--data` e il file `config.toml` |
| Anteprima dei dati su un link | Data Wrangler, il notebook, il debug |
| Log del Director | il modulo `logging` e la tabella `log_esecuzioni` |
| Conteggi di righe sui link | le righe di log «valide / scartate» e la quadratura |
| Job Sequence e schedulazione | lo schedulatore che richiama `schedulazione/esegui_etl.bat` |
| Esportazione dei job | file di testo sotto Git, confrontabili riga per riga |

---

## 8. Dalla demo all'uso reale: che cosa manca

Il progetto è volutamente piccolo. Per sostituire in produzione uno strumento come DataStage servono anche gli elementi seguenti, che uno strumento commerciale offre già pronti e che con Python vanno scelti o costruiti.

- **Database aziendale.** Al posto di `sqlite3` si usa il driver del database: `ibm_db` per Db2, `oracledb` per Oracle, `pyodbc` per SQL Server. Tutti seguono lo stesso standard di Python (DB-API) e offrono gli stessi comandi (`connect`, `execute`, `executemany`, `commit`, `rollback`): la struttura di `etl/caricamento.py` resta la stessa. Cambiano la stringa di connessione e la forma dei segnaposto. In alternativa la libreria SQLAlchemy offre un'interfaccia unica verso database diversi.
- **Credenziali.** Utenti e password non vanno mai scritti nel codice né nei file sotto Git: si leggono da variabili d'ambiente o dal sistema aziendale di gestione dei segreti.
- **Importi.** Qui gli importi sono numeri con la virgola (`float`), per semplicità. In un flusso reale si usano il tipo `Decimal` oppure i centesimi interi, per evitare errori di arrotondamento.
- **Schedulazione e monitoraggio.** Il flusso va agganciato allo schedulatore aziendale, che ne legge il codice di uscita; servono inoltre gli avvisi in caso di errore e una vista d'insieme sullo stato dei flussi.
- **Standard di progetto.** Con molti flussi e molti sviluppatori servono regole comuni: una struttura di cartelle uguale per tutti, una libreria condivisa per log, scarti e controlli, la revisione del codice, il rilascio controllato fra gli ambienti.
- **Volumi.** Per i flussi più pesanti valgono le indicazioni del notebook 02: Polars, DuckDB, formato Parquet, oppure far eseguire il lavoro al database.
- **Governo del dato.** La tracciabilità dell'origine dei dati e la documentazione dei flussi, che uno strumento grafico in parte fornisce da sé, vanno previste esplicitamente.
- **Licenze di conda.** Per le organizzazioni con 200 o più dipendenti l'uso del canale predefinito di Anaconda (`defaults`) richiede una licenza a pagamento, mentre il canale conda-forge non rientra in questo obbligo ([domande frequenti di Anaconda sui termini di servizio](https://anaconda.com/pricing/terms-of-service-faqs)). Questo progetto usa solo conda-forge. È comunque un punto da far verificare alle funzioni competenti della banca prima di adottare conda in modo diffuso.

---

## 9. Che cosa è stato collaudato

| Parte | Stato |
|---|---|
| Generatori dei dati, flusso ETL in tutti gli scenari, codici di uscita | **eseguiti e verificati** con Python 3.13 e pandas 3.0.5; i conteggi degli scarti coincidono con gli errori inseriti dal generatore |
| Test automatici | **17 superati su 17**, anche trattando ogni avviso come un errore |
| Notebook 01 | **tutte le celle eseguite** in sequenza, fuori da VS Code |
| Notebook 02, parte pandas | **eseguita** su un file da 1,5 milioni di righe |
| Notebook 02, celle di Polars, DuckDB e Parquet | **scritte sulla documentazione delle versioni 2.0 ma non eseguite**: nell'ambiente in cui il progetto è stato preparato queste librerie non erano disponibili |
| `schedulazione/esegui_etl.bat` | **non eseguito**: è un file per Windows, il progetto è stato preparato su Linux |
| Configurazioni di VS Code (`.vscode`) | **verificate nella forma**, non provate dentro VS Code |

Le parti non eseguite vanno provate sulla macchina della demo. Lo script `strumenti/verifica_ambiente.py` contiene le stesse istruzioni Polars e DuckDB del notebook 02, applicate a un file di poche righe: se termina con `TUTTO A POSTO`, anche il notebook funzionerà.
