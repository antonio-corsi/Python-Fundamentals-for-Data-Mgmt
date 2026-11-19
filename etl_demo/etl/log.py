"""
Preparazione del log.

Il "log" è il diario di bordo del flusso: una riga per ogni fatto importante
(avvio, righe lette, righe scartate, errori, fine). Lo scriviamo sia sullo
schermo sia su un file, così resta traccia di ogni esecuzione anche quando il
flusso gira di notte, lanciato da uno schedulatore.

Usiamo il modulo standard "logging" e non la funzione print(), perché logging
aggiunge da solo data, ora e livello di gravità (INFO, WARNING, ERROR) a ogni
messaggio.
"""

import logging
from datetime import date
from pathlib import Path


def prepara_log(cartella_log: Path, data_elaborazione: date) -> logging.Logger:
    """
    Configura il log e restituisce l'oggetto con cui scrivere i messaggi.

    Viene creato un file per ogni data di elaborazione, ad esempio:
        log/etl_20261117.log
    Se rieseguiamo il flusso per la stessa data, i nuovi messaggi si aggiungono
    in coda al file: la storia delle esecuzioni non va persa.
    """
    cartella_log.mkdir(parents=True, exist_ok=True)
    file_log = cartella_log / f"etl_{data_elaborazione:%Y%m%d}.log"

    # "etl" è il nome del nostro registro: tutti i moduli del pacchetto etl
    # scrivono qui, perché usano nomi che iniziano con "etl." (es. "etl.flusso")
    registro = logging.getLogger("etl")
    registro.setLevel(logging.INFO)

    # Se la funzione viene chiamata due volte (capita nei notebook), togliamo le
    # destinazioni precedenti: altrimenti ogni messaggio comparirebbe doppio
    for destinazione in list(registro.handlers):
        registro.removeHandler(destinazione)
        destinazione.close()

    # Aspetto di ogni riga:  2026-11-17 06:00:01 | INFO    | messaggio
    formato = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    su_file = logging.FileHandler(file_log, encoding="utf-8")
    su_file.setFormatter(formato)
    registro.addHandler(su_file)

    su_schermo = logging.StreamHandler()
    su_schermo.setFormatter(formato)
    registro.addHandler(su_schermo)

    return registro
