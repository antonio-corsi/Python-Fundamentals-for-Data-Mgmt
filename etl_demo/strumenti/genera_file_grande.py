"""
GENERATORE DEL FILE GRANDE PER LE PROVE DI PRESTAZIONI
======================================================

Crea un file CSV di movimenti con alcuni milioni di righe, da usare nel notebook
02_grandi_volumi.ipynb per confrontare pandas, Polars e DuckDB.

A differenza dei file giornalieri della demo, questo file è "pulito": non
contiene errori voluti, le date sono nel formato AAAA-MM-GG e gli importi usano
il punto decimale. Qui infatti non ci interessa il controllo dei dati, ma solo
la velocità con cui i diversi strumenti leggono e aggregano molte righe.

File prodotto:

    dati/grandi_volumi/movimenti_grande.csv

Colonne: id_movimento; id_conto; data_operazione; importo; divisa; codice_causale

Come si lancia (dalla cartella del progetto, con l'ambiente conda attivo):

    python strumenti/genera_file_grande.py                    5 milioni di righe (circa 210 MB)
    python strumenti/genera_file_grande.py --righe 20000000   20 milioni di righe (circa 850 MB)

Il file va generato UNA volta, prima della demo: la scrittura richiede da
qualche decina di secondi a qualche minuto, secondo il numero di righe.
"""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

RADICE_PROGETTO = Path(__file__).resolve().parent.parent
FILE_CONTI = RADICE_PROGETTO / "dati" / "input" / "conti.csv"
CARTELLA_USCITA = RADICE_PROGETTO / "dati" / "grandi_volumi"
FILE_USCITA = CARTELLA_USCITA / "movimenti_grande.csv"

SEME = 2026
RIGHE_PER_BLOCCO = 1_000_000  # generiamo e scriviamo un milione di righe alla volta, per non riempire la memoria


def main() -> None:
    analizzatore = argparse.ArgumentParser(description="Genera il file grande per le prove di prestazioni.")
    analizzatore.add_argument("--righe", type=int, default=5_000_000, help="numero di righe da generare")
    righe_richieste = analizzatore.parse_args().righe

    if not FILE_CONTI.exists():
        raise FileNotFoundError(f"Manca {FILE_CONTI}: eseguire prima  python strumenti/genera_dati.py")

    casuale = np.random.default_rng(SEME)
    CARTELLA_USCITA.mkdir(parents=True, exist_ok=True)

    # Valori fra cui estrarre a caso
    id_conti = pd.read_csv(FILE_CONTI, sep=";", dtype=str)["id_conto"].to_numpy()
    giorni_lavorativi = pd.bdate_range("2026-01-02", "2026-11-18").strftime("%Y-%m-%d").to_numpy()
    divise = ["EUR", "USD", "GBP", "CHF"]
    causali = ["POS", "BON", "PRE", "SDD", "STI", "COM", "VER"]

    inizio = time.perf_counter()
    righe_scritte = 0
    while righe_scritte < righe_richieste:
        quante = min(RIGHE_PER_BLOCCO, righe_richieste - righe_scritte)
        blocco = pd.DataFrame(
            {
                "id_movimento": np.arange(righe_scritte + 1, righe_scritte + quante + 1),
                "id_conto": casuale.choice(id_conti, size=quante),
                "data_operazione": casuale.choice(giorni_lavorativi, size=quante),
                "importo": np.round(casuale.normal(loc=-50, scale=400, size=quante), 2),
                "divisa": casuale.choice(divise, size=quante, p=[0.92, 0.05, 0.02, 0.01]),
                "codice_causale": casuale.choice(causali, size=quante, p=[0.35, 0.20, 0.12, 0.12, 0.08, 0.08, 0.05]),
            }
        )
        primo_blocco = righe_scritte == 0
        blocco.to_csv(
            FILE_USCITA,
            sep=";",
            index=False,
            mode="w" if primo_blocco else "a",  # "w" crea il file, "a" aggiunge in coda
            header=primo_blocco,  # i nomi delle colonne solo una volta, in testa
            float_format="%.2f",  # importi sempre con due decimali
            lineterminator="\n",
            encoding="utf-8",
        )
        righe_scritte += quante
        print(f"Scritte {righe_scritte:>12,} righe su {righe_richieste:,}".replace(",", "."))

    megabyte = FILE_USCITA.stat().st_size / 1024**2
    print(f"\nFile creato: {FILE_USCITA}")
    print(f"Dimensione:  {megabyte:.0f} MB - Tempo impiegato: {time.perf_counter() - inizio:.0f} secondi")


if __name__ == "__main__":
    main()
