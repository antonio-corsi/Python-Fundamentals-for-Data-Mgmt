# Scaletta della demo «Python e VS Code nei flussi ETL»

Durata: **60 minuti**. Platea: partecipanti al corso Python di tre giorni, con competenze miste.

Questa è la traccia per chi conduce la demo: che cosa mostrare, che cosa dire, quali comandi eseguire e in quanto tempo. Le istruzioni di preparazione dell'ambiente sono nel file [`README.md`](README.md).

**Come leggere la scaletta**

- **Mostrare** indica ciò che deve comparire sullo schermo.
- **Dire** riporta il messaggio da trasmettere, già nella forma «noi» da usare in aula.
- I blocchi di testo su sfondo grigio sono comandi da scrivere nel terminale.
- I nomi dei menu e dei comandi di VS Code sono in inglese, come compaiono senza il pacchetto della lingua italiana.

---

## Assunzioni della scaletta

1. La demo è condotta dal docente sul proprio PC Windows, con un solo schermo proiettato: i partecipanti osservano.
2. L'ambiente conda `etl_demo` esiste già e tutti i controlli della sezione «Preparazione» sono stati superati.
3. All'inizio della demo i risultati sono azzerati: il database non esiste ancora, le cartelle degli scarti e dei log sono vuote.
4. Il progetto è sotto Git e non ha modifiche in sospeso.
5. Il file grande per il notebook 02 è già stato generato.
6. I numeri citati (righe lette, scartate, caricate) sono quelli dei file forniti. Il generatore dei dati usa un seme fisso, quindi restano gli stessi anche rigenerando i file.
7. I tempi del notebook 02 dipendono dalla macchina: nella scaletta non compaiono numeri, vanno letti dallo schermo.

---

## I tre messaggi da lasciare

1. **VS Code è un ambiente di lavoro completo per i flussi ETL**: nello stesso posto esploriamo i dati, scriviamo il codice, lo eseguiamo passo passo, lo proviamo e ne seguiamo le modifiche.
2. **Un flusso in Python può essere robusto quanto uno costruito con uno strumento dedicato**, a condizione di progettarlo così: parametri fuori dal codice, log, scarti motivati, quadratura, rieseguibilità, test, codice di uscita.
3. **I grandi volumi non sono un ostacolo**: quando pandas non basta esistono strumenti che usano tutti i core del processore e che si affiancano a pandas senza sostituirlo.

---

## Tabella dei tempi

| Minuti | Blocco | Tema dominante |
|---|---|---|
| 0 – 5 | Apertura | Scenario, avvio di VS Code dall'ambiente conda |
| 5 – 17 | Blocco 1 · Guardare i dati | Notebook, Data Wrangler |
| 17 – 32 | Blocco 2 · Il flusso come progetto | Struttura, esecuzione, log, scarti, debug |
| 32 – 44 | Blocco 3 · La robustezza | Rieseguibilità, controlli, test, Git, schedulazione |
| 44 – 55 | Blocco 4 · I grandi volumi | pandas, Polars, DuckDB, Parquet |
| 55 – 60 | Chiusura | Sintesi, ponte verso DataStage, domande |

---

## Preparazione

### Il giorno prima

| N. | Che cosa fare | Esito atteso |
|---|---|---|
| 1 | Creare l'ambiente conda come indicato nel README, sezione 4.2 | ambiente `etl_demo` presente |
| 2 | Avviare VS Code dall'ambiente (README, sezione 4.3) ed eseguire i due controlli | `etl_demo` nella barra di stato e nel percorso stampato dal terminale |
| 3 | Eseguire `python strumenti/verifica_ambiente.py` | ultima riga: `TUTTO A POSTO` |
| 4 | Eseguire `pytest` | `17 passed` |
| 5 | Eseguire `python strumenti/genera_file_grande.py` | file da circa 210 MB in `dati/grandi_volumi` |
| 6 | Mettere il progetto sotto Git (README, sezione 4.6) | vista *Source Control* senza modifiche in sospeso |
| 7 | Aprire `schedulazione/esegui_etl.bat`, correggere se serve il percorso `CONDA_BAT` e provarlo: `schedulazione\esegui_etl.bat 2026-11-17` | ultima riga: `Flusso terminato con codice di uscita 0` |
| 8 | Aprire una volta Data Wrangler su un file: clic destro su `dati/input/conti.csv`, poi **Open in Data Wrangler** | alla prima apertura viene chiesto quale ambiente Python usare: scegliere `etl_demo` |
| 9 | Fare una prova generale completa seguendo questa scaletta, cronometro alla mano | durata vicina ai 60 minuti |
| 10 | Dopo la prova, salvare una copia del notebook 02 con i risultati visibili (ad esempio `02_grandi_volumi_eseguito.ipynb`) | copia di riserva da mostrare se una cella dovesse fallire dal vivo |

I punti 3, 7 e 9 sono i più importanti: le celle di Polars e DuckDB del notebook 02 e il file `.bat` non sono stati eseguiti durante la preparazione del progetto (vedere il README, sezione 9) e vanno quindi provati sulla macchina della demo.

### Un quarto d'ora prima

1. Chiudere posta, chat e ogni programma che possa mostrare notifiche.
2. Dal terminale di VS Code, azzerare i risultati della prova generale:

   ```
   python strumenti/azzera_risultati.py
   ```

3. Nei due notebook, usare il pulsante **Clear All Outputs** e salvare; poi controllare che la vista *Source Control* non mostri modifiche. Se ne mostra, annullarle con **Discard All Changes**.
4. Chiudere VS Code: l'avvio dall'ambiente conda fa parte della demo.
5. Aprire il Prompt di Anaconda e lasciarlo pronto, con un carattere abbastanza grande.
6. In VS Code ingrandire tutto con `Ctrl` e `+` finché il codice si legge dall'ultima fila. Facoltativo: dalla *Command Palette* attivare **Developer: Toggle Screencast Mode**, che mostra a schermo i tasti premuti.
7. Tenere questa scaletta su carta o su un secondo dispositivo: lo schermo è occupato dalla demo.

---

## Apertura (0 – 5)

**Obiettivo del blocco:** far capire che cosa vedremo e mostrare come si entra nell'ambiente di lavoro.

### Passo 1 · Lo scenario (2 minuti)

**Dire:**

- «Un flusso ETL prende i dati da una o più sorgenti, li controlla e li trasforma, e li carica in una destinazione. ETL sta per *Extract, Transform, Load*.»
- «Oggi questo lavoro si fa con IBM DataStage, dove il flusso si disegna. Vediamo come si fa lo stesso lavoro scrivendolo in Python, con VS Code.»
- «Il nostro caso: ogni giorno arriva un file con i movimenti di conto corrente. Dobbiamo controllarlo, arricchirlo con le anagrafiche, convertirlo in euro e caricarlo in un database.»
- «Vedremo tre cose: gli strumenti di VS Code, che cosa rende robusto un flusso, e che cosa fare quando i dati diventano tanti.»

### Passo 2 · Avvio di VS Code dall'ambiente conda (3 minuti)

**Mostrare:** il Prompt di Anaconda.

```
conda activate etl_demo
cd /d C:\percorso\della\cartella\demo_etl_python
code .
```

**Dire:**

- «Un ambiente conda è una cartella con il suo Python e i soli pacchetti che servono a questo progetto. Lo attiviamo e da qui lanciamo VS Code: in questo modo VS Code eredita l'ambiente e usa il Python giusto, con le sue librerie.»

**Mostrare in VS Code:**

1. Aprire `esegui_etl.py`: in basso a destra, nella barra di stato, compare `etl_demo`.
2. Menu *Terminal → New Terminal*, poi:

   ```
   python -c "import sys; print(sys.executable)"
   ```

3. Aprire `README.md` e premere `Ctrl+Maiusc+V` per vederlo impaginato: mostrare lo schema della sezione 2.

**Dire:** «Due controlli che conviene fare sempre: l'ambiente indicato nella barra di stato e il percorso del Python usato dal terminale. Devono indicare tutti e due `etl_demo`.»

**Se qualcosa non torna:** `Ctrl+Maiusc+P`, scrivere `Python: Select Interpreter`, scegliere `etl_demo`, poi aprire un terminale nuovo.

---

## Blocco 1 · Guardare i dati (5 – 17)

**Obiettivo del blocco:** mostrare che, prima di costruire un flusso, i dati si esplorano; presentare il notebook e Data Wrangler.

**Mostrare:** aprire `notebook/01_esplorazione_sorgenti.ipynb`. In alto a destra scegliere il kernel `etl_demo` (*Select Kernel → Python Environments → etl_demo*). Eseguire le celle una alla volta con `Maiusc+Invio`.

| Sezione del notebook | Minuti | Che cosa mostrare | Che cosa dire |
|---|---|---|---|
| Intestazione, assunzioni, glossario | 1 | Scorrere senza leggere tutto | «Un notebook alterna celle di testo e celle di codice. Ogni cella si esegue da sola e mostra subito il risultato.» |
| 1 e 2 · Preparazione e file | 1 | Il percorso dell'interprete; l'elenco dei file | «Abbiamo un file di movimenti al giorno, due anagrafiche e i cambi in Excel.» |
| 3 · Lettura come testo | 3 | La tabella; il pulsante **Open 'grezzi' in Data Wrangler**; in Data Wrangler la colonna `divisa` con i valori distinti; poi l'esempio dell'importo che diventa cento volte più grande | «Data Wrangler è l'anteprima dei dati: ordiniamo, filtriamo, vediamo valori distinti e mancanti senza scrivere codice.» E poi: «Se lasciamo fare la conversione automatica, 1234.56 diventa 123456 senza alcun avviso. Per questo leggiamo tutto come testo, controlliamo e solo dopo convertiamo.» |
| 4 · A caccia dei problemi | 3 | Eseguire in sequenza; soffermarsi sulla tabella finale di riepilogo | «Cinque tipi di errore da scartare e uno da ripulire. Abbiamo le regole del nostro flusso.» |
| 5 · Così com'è e idiomatico | 2 | I due tempi e il rapporto fra i due | «Stesso risultato. Nella prima versione scorriamo le righe una alla volta; nella seconda chiediamo a pandas di lavorare sull'intera colonna. In pandas si ragiona per colonne.» |
| 6 · Dal notebook al progetto | 2 | Le funzioni importate dal pacchetto `etl` e i conteggi | «Il notebook serve per capire. Le regole, una volta chiare, diventano funzioni del progetto: riutilizzabili e verificabili.» |

**Non eseguire la sezione 7:** richiede il database, che creeremo nel blocco 2.

**Se il tempo stringe:** nella sezione 4 eseguire solo 4.1, 4.2 e la tabella di riepilogo.

**Se Data Wrangler non si apre:** proseguire con le tabelle del notebook; i conteggi per valore (`value_counts`) mostrano le stesse informazioni.

---

## Blocco 2 · Il flusso come progetto (17 – 32)

**Obiettivo del blocco:** mostrare com'è fatto un flusso «da produzione» e come lo si esegue e lo si ispeziona.

### Passo 1 · La struttura del progetto (2 minuti)

**Mostrare:** l'elenco dei file nella barra laterale; aprire la cartella `etl`.

**Dire:** «Ogni file ha un compito: `estrazione` legge, `trasformazione` controlla e trasforma, `caricamento` scrive nel database, `flusso` mette in fila i passi. È la stessa divisione che in uno strumento grafico vediamo nel disegno del job.»

### Passo 2 · Il flusso si legge dall'alto verso il basso (3 minuti)

**Mostrare:** `etl/flusso.py`, funzione `esegui_passi`. Scorrere i blocchi ESTRAZIONE, TRASFORMAZIONE, SCARTI, CONTROLLI, CARICAMENTO.

**Dire:**

- «Ogni passo di trasformazione restituisce due cose: le righe valide, che proseguono, e gli scarti. Nessuna riga sparisce.»
- «Prima di caricare facciamo due controlli. Se uno fallisce, nel database non scriviamo nulla.»

**Mostrare:** `config.toml`.

**Dire:** «Cartelle e soglie stanno in un file di parametri, fuori dal codice. Per cambiare ambiente o cambiare una soglia non tocchiamo i programmi.»

### Passo 3 · Esecuzione da terminale (3 minuti)

```
python esegui_etl.py --data 2026-11-17
```

**Mostrare e leggere ad alta voce il log**, riga per riga:

| Riga del log | Che cosa dire |
|---|---|
| `Letto movimenti_20261117.csv: 20100 righe` | «Abbiamo letto 20.100 righe.» |
| le cinque righe `Controllo ...` | «A ogni controllo vediamo quante righe passano e quante vengono scartate: 60 per la data, 50 per l'importo, 100 ripetute, 70 su conti inesistenti, 30 senza cambio.» |
| `Quadratura superata: lette 20100 = buone 19790 + scartate 310` | «La quadratura: ogni riga letta è finita o fra le buone o fra gli scarti.» |
| `Scarti al 1.5% ... controllo superato` | «Gli scarti sono sotto la soglia del 5%: possiamo caricare.» |
| `Caricate 19790 righe ...` | «Solo adesso scriviamo nel database.» |

**Dire:** «La data di elaborazione la passiamo come parametro: lo stesso programma elabora qualunque giornata.»

### Passo 4 · Dove sono finiti i dati (3 minuti)

**Mostrare:**

1. `log/etl_20261117.log`: lo stesso racconto, conservato su file.
2. `dati/scarti/scarti_movimenti_20261117.csv`: clic destro, **Open in Data Wrangler** (se richiesto, indicare il punto e virgola come separatore). Far notare le colonne `riga_file` e `motivo_scarto`.
3. Tornare al notebook 01 ed eseguire la sezione 7: storico delle esecuzioni, movimenti per giornata, prime cinque filiali.

**Dire:** «Per ogni riga scartata sappiamo quale riga del file era, perché è stata scartata e com'era scritta. E il database si interroga con l'SQL che conosciamo già.»

### Passo 5 · Il debug (4 minuti)

**Mostrare:**

1. Aprire `etl/trasformazione.py`, funzione `controlla_formati`. Fare clic a sinistra del numero della riga che contiene `"IMPORTO_NON_VALIDO"`: compare il pallino rosso.
2. Vista *Run and Debug* (`Ctrl+Maiusc+D`), scegliere `ETL: giorno normale (2026-11-17)`, premere `F5`.
3. Quando l'esecuzione si ferma, nel pannello *Variables* aprire le variabili locali: compaiono `movimenti` e `formato_corretto`.
4. Clic destro su `movimenti` e scegliere **View Value in Data Viewer**: la tabella si apre in quel preciso momento del flusso.
5. Nella *Debug Console*, in basso, scrivere una alla volta:

   ```
   (~formato_corretto).sum()
   movimenti.loc[~formato_corretto, "importo"].value_counts()
   ```

6. Premere `F10` per eseguire una riga, poi `F5` per arrivare alla fine. Togliere il punto di interruzione con un clic sul pallino rosso.

**Dire:** «Abbiamo fermato il flusso a metà e abbiamo guardato i dati in quel punto: è l'equivalente di guardare i dati che passano su un collegamento del job. Possiamo anche fare domande ai dati, senza modificare il programma.»

**Se la voce *View Value in Data Viewer* non compare:** usare solo la *Debug Console* con le due espressioni qui sopra; in più `movimenti.head()` mostra le prime righe.

---

## Blocco 3 · La robustezza (32 – 44)

**Obiettivo del blocco:** mostrare i comportamenti che distinguono un flusso affidabile da uno script.

### Passo 1 · Rieseguire senza creare doppioni (2 minuti)

```
python esegui_etl.py --data 2026-11-17
```

**Mostrare:** nel notebook 01, sezione 7, rieseguire le celle dello storico e dei movimenti per giornata: le righe del 17 novembre sono sempre 19.790, mentre lo storico ha un'esecuzione in più.

**Dire:** «Se un flusso si interrompe o va rilanciato, non deve raddoppiare i dati. Il nostro, prima di inserire, toglie i dati della stessa giornata; e lo fa in una transazione: o tutto o niente.»

### Passo 2 · Un file corrotto (2 minuti)

```
python esegui_etl.py --data 2026-11-18
echo $LASTEXITCODE
```

(Nel Prompt dei comandi il secondo comando è `echo %ERRORLEVEL%`.)

**Mostrare:** la riga `FLUSSO FERMATO: Scarti al 31.4% ...` e il codice di uscita `1`. Aprire `dati/scarti/scarti_movimenti_20261118.csv`: quasi tutti gli scarti hanno motivo `IMPORTO_NON_VALIDO`.

**Dire:** «Un terzo delle righe è sbagliato: non è un problema di singole righe, è il file che ha qualcosa che non va. Il flusso si ferma e non carica nulla. Gli scarti però li scrive, perché sono loro a dirci che cosa è successo: qui un sistema a monte ha cambiato il formato degli importi.»

### Passo 3 · Un file che non c'è (1 minuto)

```
python esegui_etl.py --data 2026-11-19
```

**Dire:** «Messaggio chiaro, codice di uscita diverso da zero e una riga nello storico: anche l'esecuzione fallita lascia traccia.»

### Passo 4 · Test automatici e Git, insieme (5 minuti)

**Mostrare:**

1. Vista **Testing** (icona a forma di ampolla): premere **Run Tests**. Compaiono 17 segni verdi.
2. Aprire `tests/test_trasformazione.py` e leggere il test `test_importo_in_formato_sbagliato_viene_scartato`.

**Dire:** «Un test è un piccolo caso di cui conosciamo già il risultato. Li scriviamo una volta e li rieseguiamo a ogni modifica.»

3. Ora una modifica sbagliata, fatta di proposito. In `etl/trasformazione.py`, funzione `segna_rilevanti`, sostituire `>=` con `>` e salvare.
4. Rieseguire i test: uno diventa rosso, `test_il_flag_rilevante_non_dipende_dal_segno_e_la_soglia_e_compresa`.

**Dire:** «Abbiamo cambiato un solo carattere e una regola è saltata: un movimento esattamente pari alla soglia non verrebbe più segnalato. Il test se n'è accorto in un secondo.»

5. Vista **Source Control**: fare clic su `trasformazione.py`. Compaiono le due versioni affiancate, con la riga modificata in evidenza.

**Dire:** «Il codice è testo: Git ci mostra esattamente che cosa è cambiato, riga per riga, e conserva chi ha cambiato che cosa e quando.»

6. Clic destro sul file, **Discard Changes**: la modifica è annullata. Rieseguire i test: tutti verdi.

### Passo 5 · La schedulazione (2 minuti)

**Mostrare:** `schedulazione/esegui_etl.bat`, poi eseguirlo dal terminale:

```
schedulazione\esegui_etl.bat 2026-11-17
```

**Dire:** «In produzione il flusso non lo lancia una persona ma lo schedulatore, che gli passa la data e legge il codice di uscita: zero, tutto bene; diverso da zero, c'è un problema da segnalare. Questo piccolo file fa da ponte: entra nell'ambiente conda e lancia il flusso.»

**Se il file `.bat` dà errore:** mostrarne solo il contenuto e ricordare il codice di uscita visto al passo 2.

**Se il tempo stringe:** saltare il passo 3 e, nel passo 5, mostrare il file senza eseguirlo.

---

## Blocco 4 · I grandi volumi (44 – 55)

**Obiettivo del blocco:** rispondere alla domanda «e quando i dati sono tanti?».

**Mostrare:** aprire `notebook/02_grandi_volumi.ipynb`, scegliere il kernel `etl_demo`, eseguire le celle una alla volta.

| Sezione del notebook | Minuti | Che cosa mostrare | Che cosa dire |
|---|---|---|---|
| 1 · Ambiente e file | 1 | Dimensione del file e prime righe | «Non più ventimila righe ma alcuni milioni.» |
| 2 · La domanda | 1 | Il testo della domanda | «Filtrare, unire, raggruppare, aggregare: le operazioni di sempre. Le chiediamo a tre strumenti diversi.» |
| 3 · pandas | 2 | Il tempo misurato | «pandas carica i dati in memoria e usa un solo core del processore.» |
| 4 · Polars | 2 | Il tempo misurato | «Polars usa tutti i core. E prima descriviamo tutta la richiesta, poi la eseguiamo: così legge solo ciò che serve.» |
| 5 · DuckDB | 2 | Il comando SQL e il tempo misurato | «DuckDB interroga direttamente i file in SQL. Chi conosce l'SQL è già operativo.» |
| 6 · Stessa risposta | 1 | Le due righe con `True` | «Cambiano i tempi, non i risultati.» |
| 7 e 8 · Parquet e tabella finale | 2 | Dimensioni dei due file; la tabella dei tempi; la tabella delle indicazioni pratiche | «Spesso il guadagno più grande viene dal formato del file, prima ancora che dallo strumento.» |

**Dire in chiusura del blocco:** «Non è una scelta esclusiva: i tre strumenti convivono. Usiamo il motore più veloce nel passo più pesante e lasciamo il resto in pandas.»

**Se una cella fallisce dal vivo:** aprire la copia di riserva `02_grandi_volumi_eseguito.ipynb` preparata durante la prova generale e commentare i risultati salvati.

**Se il tempo stringe:** saltare la sezione 7 e andare direttamente alla tabella finale, che mostrerà i soli tempi sul file CSV.

---

## Chiusura (55 – 60)

### Passo 1 · Sintesi (2 minuti)

**Dire**, riprendendo i tre messaggi iniziali:

- «In VS Code abbiamo esplorato i dati, eseguito il flusso, fermato l'esecuzione a metà, lanciato i test e visto le differenze fra due versioni.»
- «Il flusso ha parametri fuori dal codice, log, scarti motivati, quadratura, rieseguibilità, test e codice di uscita: sono queste cose a renderlo affidabile, più che il linguaggio.»
- «Sui grandi volumi abbiamo strumenti che si affiancano a pandas.»

### Passo 2 · Il ponte verso DataStage (1 minuto)

**Mostrare:** `README.md`, sezione 7, tabella di corrispondenza.

**Dire:** «Chi lavora con DataStage ritrova qui gli stessi concetti con altri nomi: lo stage diventa una funzione, il link di reject la tabella degli scarti, i parametri del job il file dei parametri.»

### Passo 3 · Che cosa serve per farlo davvero (2 minuti)

**Mostrare:** `README.md`, sezione 8.

**Dire:** «Uno strumento come DataStage offre già pronte molte cose: connettori, console operativa, schedulazione, supporto del fornitore. Con Python queste cose si scelgono o si costruiscono: servono regole comuni di progetto, una libreria condivisa, l'aggancio allo schedulatore e al monitoraggio. Il costo si sposta dalle licenze alle competenze e alla disciplina di sviluppo.»

---

## Domande probabili

| Domanda | Traccia di risposta |
|---|---|
| Python può davvero sostituire DataStage? | Per i flussi su file e di media complessità sì, come abbiamo visto. La sostituzione non riguarda solo il linguaggio: vanno previsti schedulazione, monitoraggio, standard di sviluppo e gestione delle credenziali. Conviene procedere per gradi: i flussi nuovi e quelli più semplici per primi, con un periodo in cui vecchio e nuovo flusso girano in parallelo e i risultati vengono confrontati. |
| E le prestazioni? | Dipendono dai volumi. Fino a qualche milione di righe pandas è sufficiente; oltre, Polars e DuckDB usano tutti i core. Per i volumi maggiori conviene far lavorare il database e usare Python per orchestrare. |
| Come si schedula un flusso Python? | Con lo schedulatore già in uso: lancia un comando, passa la data, legge il codice di uscita. Esistono anche orchestratori nati per Python, da valutare quando i flussi diventano molti e dipendono l'uno dall'altro. |
| Dove si mettono utenti e password? | Mai nel codice né nei file sotto Git. Si leggono da variabili d'ambiente o dal sistema aziendale di gestione dei segreti. |
| Chi non sa programmare come fa? | Data Wrangler aiuta a esplorare e genera il codice delle operazioni di pulizia, ma un flusso va comunque scritto e capito. Servono formazione e revisione del codice fra colleghi; i test proteggono dagli errori. |
| Il notebook può andare in produzione? | È lo strumento per esplorare e spiegare. In produzione va il codice dei file `.py`, che si prova con i test e si segue con Git. |
| Perché conda e non il Python scaricato dal sito ufficiale? | Perché l'ambiente conda isola il progetto e porta con sé anche le librerie di sistema di cui i pacchetti hanno bisogno. Per le licenze vedere il README, sezione 8. |
