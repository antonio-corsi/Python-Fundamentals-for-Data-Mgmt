"""
TEST DEL CARICAMENTO: "O TUTTO O NIENTE"
========================================

Verifichiamo la proprietà più importante del caricamento: se qualcosa va
storto a metà, il database deve restare esattamente com'era prima.

Per provocare l'errore di proposito usiamo un riepilogo con due righe uguali:
la chiave primaria della tabella riepilogo_giornaliero le rifiuta. A quel
punto i movimenti sono già stati cancellati e reinseriti, ma la transazione
viene annullata per intero e ritroviamo i dati del caricamento precedente.
"""

import sqlite3
from datetime import date

import pandas as pd
import pytest

from etl.caricamento import apri_database, carica_risultati

GIORNO = date(2026, 11, 17)


def crea_movimenti(quanti: int) -> pd.DataFrame:
    """Costruisce una tabella di movimenti già trasformati, pronta per il caricamento."""
    return pd.DataFrame(
        {
            "id_movimento": [f"M{numero}" for numero in range(quanti)],
            "id_conto": "CC00000001",
            "id_cliente": "CL000001",
            "codice_filiale": "F001",
            "segmento": "RETAIL",
            "data_operazione": pd.Timestamp("2026-11-17"),
            "codice_causale": "POS",
            "descrizione": "Pagamento con carta",
            "divisa": "EUR",
            "importo": -10.0,
            "cambio": 1.0,
            "importo_eur": -10.0,
            "flag_rilevante": False,
        }
    )


def conta(connessione: sqlite3.Connection, tabella: str) -> int:
    return connessione.execute(f"SELECT COUNT(*) FROM {tabella}").fetchone()[0]


def test_se_il_caricamento_fallisce_a_meta_il_database_resta_com_era(tmp_path):
    connessione = apri_database(tmp_path / "prova.db")
    riepilogo_corretto = pd.DataFrame(
        {"codice_filiale": ["F001"], "codice_causale": ["POS"], "numero_movimenti": [3], "totale_eur": [-30.0]}
    )
    riepilogo_con_chiave_doppia = pd.DataFrame(
        {
            "codice_filiale": ["F001", "F001"],
            "codice_causale": ["POS", "POS"],
            "numero_movimenti": [2, 3],
            "totale_eur": [-20.0, -30.0],
        }
    )

    try:
        # Primo caricamento, corretto: 3 movimenti
        carica_risultati(connessione, crea_movimenti(3), riepilogo_corretto, GIORNO)
        assert conta(connessione, "movimenti") == 3

        # Secondo caricamento per la stessa giornata: 5 movimenti, ma il riepilogo è sbagliato
        with pytest.raises(sqlite3.IntegrityError):
            carica_risultati(connessione, crea_movimenti(5), riepilogo_con_chiave_doppia, GIORNO)

        # Il database contiene ancora i 3 movimenti di prima: né 5, né 0
        assert conta(connessione, "movimenti") == 3
        assert conta(connessione, "riepilogo_giornaliero") == 1
    finally:
        connessione.close()
