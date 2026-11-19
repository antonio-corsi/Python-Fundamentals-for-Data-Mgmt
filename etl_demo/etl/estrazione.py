"""
E di ETL: ESTRAZIONE (in inglese "Extract").

Qui leggiamo i dati dalle sorgenti e li portiamo in memoria sotto forma di
DataFrame. Un DataFrame è la tabella di pandas: righe e colonne, come un foglio
di calcolo o una tabella di database.

Regola che seguiamo in questo modulo: leggere senza interpretare. I controlli e
le conversioni si fanno dopo, nel modulo trasformazione.py.

Per chi viene da DataStage: queste funzioni corrispondono agli stage di lettura
(Sequential File per i file di testo, i connettori per database ed Excel).
"""

import logging
from pathlib import Path

import pandas as pd

registro = logging.getLogger(__name__)

# Le colonne che ci aspettiamo nel file dei movimenti: è il "tracciato" del file
COLONNE_MOVIMENTI = [
    "id_movimento",
    "id_conto",
    "data_operazione",
    "importo",
    "divisa",
    "codice_causale",
    "descrizione",
]


def leggi_movimenti(percorso: Path) -> pd.DataFrame:
    """
    Legge il file CSV dei movimenti "così com'è".

    Tutte le colonne vengono lette come testo (dtype=str). È una scelta voluta:
    se chiedessimo a pandas di convertire subito date e importi, una sola riga
    sbagliata potrebbe far fallire la lettura dell'intero file oppure, peggio,
    essere interpretata in modo errato senza che ce ne accorgiamo.

    Aggiungiamo inoltre la colonna "riga_file" con il numero della riga nel file
    di origine: ci servirà per dire esattamente quale riga è stata scartata.
    """
    if not percorso.exists():
        raise FileNotFoundError(f"File dei movimenti non trovato: {percorso}")

    movimenti = pd.read_csv(
        percorso,
        sep=";",  # il separatore di colonna è il punto e virgola
        dtype=str,  # tutte le colonne come testo
        keep_default_na=False,  # una cella vuota resta testo vuoto "", non diventa "valore mancante"
        encoding="utf-8",
    )

    # Controllo del tracciato: se manca una colonna ci fermiamo subito, con un messaggio chiaro
    colonne_mancanti = [colonna for colonna in COLONNE_MOVIMENTI if colonna not in movimenti.columns]
    if colonne_mancanti:
        raise ValueError(f"Nel file {percorso.name} mancano le colonne: {colonne_mancanti}")

    movimenti = movimenti[COLONNE_MOVIMENTI]

    # La prima riga del file contiene i nomi delle colonne, quindi i dati partono dalla riga 2
    movimenti.insert(0, "riga_file", range(2, len(movimenti) + 2))

    registro.info("Letto %s: %d righe", percorso.name, len(movimenti))
    return movimenti


def leggi_anagrafica(percorso: Path, colonna_chiave: str) -> pd.DataFrame:
    """
    Legge una tabella anagrafica in formato CSV (conti oppure clienti).

    La "chiave" è la colonna che identifica ogni riga (id_conto, id_cliente).
    Controlliamo che non contenga valori ripetuti: una chiave doppia in una
    tabella anagrafica moltiplicherebbe le righe dei movimenti quando le uniamo.
    """
    if not percorso.exists():
        raise FileNotFoundError(f"File anagrafico non trovato: {percorso}")

    anagrafica = pd.read_csv(percorso, sep=";", dtype=str, keep_default_na=False, encoding="utf-8")

    if anagrafica[colonna_chiave].duplicated().any():
        raise ValueError(f"Nel file {percorso.name} la chiave {colonna_chiave} contiene valori ripetuti")

    registro.info("Letto %s: %d righe", percorso.name, len(anagrafica))
    return anagrafica


def leggi_cambi(percorso: Path) -> pd.DataFrame:
    """
    Legge la tabella dei cambi dal file Excel (foglio "cambi").

    Colonne: data, divisa, cambio. Il cambio indica quante unità di divisa
    servono per comprare 1 euro (ad esempio 1,10 dollari per 1 euro).

    Per leggere i file Excel pandas usa, dietro le quinte, la libreria openpyxl.
    """
    if not percorso.exists():
        raise FileNotFoundError(f"File dei cambi non trovato: {percorso}")

    cambi = pd.read_excel(percorso, sheet_name="cambi")
    cambi["divisa"] = cambi["divisa"].str.strip().str.upper()

    registro.info("Letto %s: %d righe", percorso.name, len(cambi))
    return cambi
