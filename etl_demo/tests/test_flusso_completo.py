"""
TEST DEL FLUSSO COMPLETO
========================

I test del file test_trasformazione.py provano una funzione alla volta su
tabelline di poche righe. Qui invece eseguiamo l'intero flusso sui file veri
della cartella dati/input, dall'estrazione al caricamento.

Per non sporcare il database e le cartelle della demo, i risultati vengono
scritti in una cartella temporanea. Ce la fornisce pytest attraverso
l'argomento speciale "tmp_path": basta chiamare così un argomento della
funzione di test e pytest crea per noi una cartella vuota, diversa per ogni test.
"""

import sqlite3
from datetime import date

import pytest

from etl.configurazione import carica_configurazione
from etl.controlli import ErroreControllo
from etl.flusso import esegui_flusso


def configurazione_di_prova(cartella_temporanea) -> dict:
    """La configurazione normale, ma con le destinazioni spostate nella cartella temporanea."""
    config = carica_configurazione()
    config["percorsi"]["cartella_scarti"] = cartella_temporanea / "scarti"
    config["percorsi"]["cartella_log"] = cartella_temporanea / "log"
    config["percorsi"]["file_database"] = cartella_temporanea / "datamart_di_prova.db"
    return config


def conta_righe(file_database, tabella: str, giorno: str) -> int:
    """Conta le righe di una tabella per una data di elaborazione."""
    connessione = sqlite3.connect(file_database)
    try:
        comando = f"SELECT COUNT(*) FROM {tabella} WHERE data_elaborazione = ?"
        return connessione.execute(comando, (giorno,)).fetchone()[0]
    finally:
        connessione.close()


def test_il_flusso_carica_tutte_le_righe_buone(tmp_path):
    config = configurazione_di_prova(tmp_path)

    conteggi = esegui_flusso(date(2026, 11, 17), config)

    # Quadratura: nessuna riga sparisce
    assert conteggi["righe_lette"] == conteggi["righe_caricate"] + conteggi["righe_scartate"]
    assert conteggi["righe_caricate"] > 0
    # Nel database ci sono esattamente le righe dichiarate come caricate
    nel_database = conta_righe(config["percorsi"]["file_database"], "movimenti", "2026-11-17")
    assert nel_database == conteggi["righe_caricate"]
    # Il file degli scarti è stato scritto
    assert (tmp_path / "scarti" / "scarti_movimenti_20261117.csv").exists()


def test_rieseguire_il_flusso_non_crea_doppioni(tmp_path):
    config = configurazione_di_prova(tmp_path)

    prima_volta = esegui_flusso(date(2026, 11, 17), config)
    seconda_volta = esegui_flusso(date(2026, 11, 17), config)

    nel_database = conta_righe(config["percorsi"]["file_database"], "movimenti", "2026-11-17")
    assert seconda_volta == prima_volta
    assert nel_database == prima_volta["righe_caricate"]


def test_un_file_con_troppi_scarti_ferma_il_flusso_e_non_carica_nulla(tmp_path):
    config = configurazione_di_prova(tmp_path)

    # "pytest.raises" verifica che il codice al suo interno sollevi proprio l'errore indicato
    with pytest.raises(ErroreControllo):
        esegui_flusso(date(2026, 11, 18), config)

    nel_database = conta_righe(config["percorsi"]["file_database"], "movimenti", "2026-11-18")
    assert nel_database == 0
    # Gli scarti invece ci sono: servono a capire che cosa non va nel file
    assert (tmp_path / "scarti" / "scarti_movimenti_20261118.csv").exists()


def test_un_file_mancante_viene_segnalato_e_registrato(tmp_path):
    config = configurazione_di_prova(tmp_path)

    with pytest.raises(FileNotFoundError):
        esegui_flusso(date(2026, 11, 19), config)

    # Anche l'esecuzione fallita lascia traccia nella tabella log_esecuzioni
    connessione = sqlite3.connect(config["percorsi"]["file_database"])
    try:
        esiti = connessione.execute("SELECT esito FROM log_esecuzioni").fetchall()
    finally:
        connessione.close()
    assert esiti == [("ERRORE",)]
