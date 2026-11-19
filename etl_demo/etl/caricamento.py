"""
L di ETL: CARICAMENTO (in inglese "Load").

Qui scriviamo i risultati nel database di destinazione.

In questa demo il database è SQLite: un database contenuto in un unico file,
che non richiede alcun server. Python lo gestisce con il modulo standard
"sqlite3", quindi non serve installare nulla.

Tre idee importanti di questo modulo:

1) TRANSAZIONE. Una transazione è un gruppo di comandi che il database tratta
   come un blocco unico: o vanno a buon fine tutti, o non ne resta nessuno.
   Se il flusso si interrompe a metà caricamento, il database torna com'era.

2) RIESEGUIBILITÀ. Prima di inserire i dati di una giornata cancelliamo quelli
   della stessa giornata eventualmente già presenti. Così possiamo rilanciare
   il flusso quante volte vogliamo senza creare doppioni.

3) SEGNAPOSTO. I valori non vengono mai "incollati" dentro il testo del comando
   SQL: al loro posto scriviamo dei punti interrogativi e passiamo i valori a
   parte. Ci pensa il database a inserirli nel modo corretto e sicuro.

Per chi viene da DataStage: questo modulo corrisponde agli stage di scrittura
su database (i connettori Db2, Oracle, ODBC).

NOTA PER L'USO REALE. Con Db2, Oracle o SQL Server la struttura resta la stessa:
si sostituisce sqlite3 con il driver del database (ibm_db, oracledb, pyodbc).
Tutti questi driver seguono lo stesso standard di Python, chiamato DB-API, e
offrono quindi gli stessi comandi: connect, execute, executemany, commit,
rollback. Cambiano la stringa di connessione e la forma dei segnaposto.
"""

import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd

registro = logging.getLogger(__name__)

# Struttura delle tabelle di destinazione, scritta in SQL.
# "IF NOT EXISTS" fa sì che le tabelle vengano create solo la prima volta.
# La PRIMARY KEY (chiave primaria) è l'ultima linea di difesa: è il database
# stesso a rifiutare due righe con la stessa chiave.
CREAZIONE_TABELLE = """
CREATE TABLE IF NOT EXISTS movimenti (
    data_elaborazione  TEXT    NOT NULL,
    id_movimento       TEXT    NOT NULL,
    id_conto           TEXT    NOT NULL,
    id_cliente         TEXT    NOT NULL,
    codice_filiale     TEXT    NOT NULL,
    segmento           TEXT,
    data_operazione    TEXT    NOT NULL,
    codice_causale     TEXT,
    descrizione        TEXT,
    divisa             TEXT    NOT NULL,
    importo            REAL    NOT NULL,
    cambio             REAL    NOT NULL,
    importo_eur        REAL    NOT NULL,
    flag_rilevante     INTEGER NOT NULL,
    PRIMARY KEY (data_elaborazione, id_movimento)
);

CREATE TABLE IF NOT EXISTS riepilogo_giornaliero (
    data_elaborazione  TEXT    NOT NULL,
    codice_filiale     TEXT    NOT NULL,
    codice_causale     TEXT    NOT NULL,
    numero_movimenti   INTEGER NOT NULL,
    totale_eur         REAL    NOT NULL,
    PRIMARY KEY (data_elaborazione, codice_filiale, codice_causale)
);

CREATE TABLE IF NOT EXISTS log_esecuzioni (
    id_esecuzione      INTEGER PRIMARY KEY AUTOINCREMENT,
    avvio              TEXT    NOT NULL,
    data_elaborazione  TEXT    NOT NULL,
    esito              TEXT    NOT NULL,
    righe_lette        INTEGER,
    righe_caricate     INTEGER,
    righe_scartate     INTEGER,
    durata_secondi     REAL,
    messaggio          TEXT
);
"""

COLONNE_MOVIMENTI = [
    "data_elaborazione",
    "id_movimento",
    "id_conto",
    "id_cliente",
    "codice_filiale",
    "segmento",
    "data_operazione",
    "codice_causale",
    "descrizione",
    "divisa",
    "importo",
    "cambio",
    "importo_eur",
    "flag_rilevante",
]

COLONNE_RIEPILOGO = ["data_elaborazione", "codice_filiale", "codice_causale", "numero_movimenti", "totale_eur"]


def apri_database(file_database: Path) -> sqlite3.Connection:
    """Apre il database (se il file non esiste viene creato) e crea le tabelle che mancano."""
    file_database.parent.mkdir(parents=True, exist_ok=True)
    connessione = sqlite3.connect(file_database)
    connessione.executescript(CREAZIONE_TABELLE)
    return connessione


def prepara_movimenti(movimenti: pd.DataFrame, data_elaborazione: date) -> pd.DataFrame:
    """Porta la tabella dei movimenti nella forma esatta della tabella di destinazione."""
    pronti = movimenti.copy()
    pronti["data_elaborazione"] = data_elaborazione.isoformat()  # testo nel formato AAAA-MM-GG
    pronti["data_operazione"] = pronti["data_operazione"].dt.strftime("%Y-%m-%d")
    pronti["flag_rilevante"] = pronti["flag_rilevante"].astype(int)  # Vero/Falso -> 1/0
    return pronti[COLONNE_MOVIMENTI]


def prepara_riepilogo(riepilogo: pd.DataFrame, data_elaborazione: date) -> pd.DataFrame:
    """Porta il riepilogo nella forma esatta della tabella di destinazione."""
    pronto = riepilogo.copy()
    pronto["data_elaborazione"] = data_elaborazione.isoformat()
    return pronto[COLONNE_RIEPILOGO]


def inserisci(connessione: sqlite3.Connection, tabella: str, dati: pd.DataFrame) -> None:
    """
    Inserisce tutte le righe di un DataFrame in una tabella del database.

    I nomi della tabella e delle colonne arrivano dal nostro codice; i VALORI
    passano invece dai segnaposto "?", uno per colonna.
    """
    elenco_colonne = ", ".join(dati.columns)
    segnaposto = ", ".join("?" for _ in dati.columns)
    comando = f"INSERT INTO {tabella} ({elenco_colonne}) VALUES ({segnaposto})"

    # itertuples restituisce le righe una alla volta sotto forma di tuple di
    # valori; executemany esegue il comando una volta per ogni riga.
    connessione.executemany(comando, dati.itertuples(index=False, name=None))


def carica_risultati(
    connessione: sqlite3.Connection, movimenti: pd.DataFrame, riepilogo: pd.DataFrame, data_elaborazione: date
) -> None:
    """
    Carica movimenti e riepilogo della giornata in un'unica transazione.

    "with connessione:" apre la transazione. Se tutte le istruzioni al suo
    interno vanno a buon fine le modifiche vengono confermate (commit); se una
    qualsiasi fallisce vengono annullate tutte (rollback).
    """
    giorno = data_elaborazione.isoformat()
    movimenti_pronti = prepara_movimenti(movimenti, data_elaborazione)
    riepilogo_pronto = prepara_riepilogo(riepilogo, data_elaborazione)

    with connessione:
        # Rieseguibilità: via i dati della stessa giornata, se ci sono già
        connessione.execute("DELETE FROM movimenti WHERE data_elaborazione = ?", (giorno,))
        connessione.execute("DELETE FROM riepilogo_giornaliero WHERE data_elaborazione = ?", (giorno,))

        inserisci(connessione, "movimenti", movimenti_pronti)
        inserisci(connessione, "riepilogo_giornaliero", riepilogo_pronto)

    registro.info(
        "Caricate %d righe in 'movimenti' e %d righe in 'riepilogo_giornaliero'",
        len(movimenti_pronti),
        len(riepilogo_pronto),
    )


def registra_esecuzione(
    connessione: sqlite3.Connection,
    avvio: datetime,
    data_elaborazione: date,
    esito: str,
    conteggi: dict,
    durata_secondi: float,
    messaggio: str,
) -> None:
    """
    Scrive una riga nella tabella log_esecuzioni: è il registro storico di tutte
    le esecuzioni, comprese quelle fallite. Chi gestisce il flusso può
    interrogarlo con una semplice SELECT.
    """
    with connessione:
        connessione.execute(
            """
            INSERT INTO log_esecuzioni
                (avvio, data_elaborazione, esito,
                 righe_lette, righe_caricate, righe_scartate,
                 durata_secondi, messaggio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                avvio.isoformat(sep=" ", timespec="seconds"),
                data_elaborazione.isoformat(),
                esito,
                conteggi["righe_lette"],
                conteggi["righe_caricate"],
                conteggi["righe_scartate"],
                round(durata_secondi, 2),
                messaggio,
            ),
        )
