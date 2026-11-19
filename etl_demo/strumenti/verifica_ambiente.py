"""
VERIFICA DELL'AMBIENTE: IL CONTROLLO DA FARE PRIMA DELLA DEMO
=============================================================

Questo script verifica in pochi secondi che sulla macchina ci sia tutto ciò che
serve alla demo: la versione di Python, le librerie, i file di input e il
funzionamento di ciascuno strumento usato nei notebook (pandas, SQLite, Polars,
DuckDB, Parquet).

Le prove su Polars, DuckDB e Parquet usano le STESSE istruzioni del notebook
02_grandi_volumi.ipynb, applicate a un file di poche righe: se qui risulta
tutto a posto, anche il notebook funzionerà.

Come si lancia (dalla cartella del progetto, con l'ambiente conda attivo):

    python strumenti/verifica_ambiente.py

Lo script termina con codice di uscita 0 se tutte le prove obbligatorie sono
superate, 1 in caso contrario.
"""

import importlib
import sqlite3
import sys
import tempfile
from pathlib import Path

RADICE_PROGETTO = Path(__file__).resolve().parent.parent
CARTELLA_INPUT = RADICE_PROGETTO / "dati" / "input"
FILE_GRANDE = RADICE_PROGETTO / "dati" / "grandi_volumi" / "movimenti_grande.csv"

FILE_DI_INPUT = [
    "clienti.csv",
    "conti.csv",
    "cambi.xlsx",
    "movimenti_20261116.csv",
    "movimenti_20261117.csv",
    "movimenti_20261118.csv",
]

# Nome con cui si importa la libreria -> a che cosa serve nella demo
LIBRERIE = {
    "pandas": "tabelle di dati (flusso ETL e notebook)",
    "numpy": "calcolo numerico (usato da pandas e dai generatori dei dati)",
    "openpyxl": "lettura dei file Excel",
    "pyarrow": "formato Parquet (notebook 02)",
    "polars": "motore Polars (notebook 02)",
    "duckdb": "motore DuckDB (notebook 02)",
    "pytest": "test automatici",
    "ipykernel": "esecuzione dei notebook in VS Code",
}

esiti = []  # elenco di Vero/Falso, uno per ogni prova obbligatoria


def prova(descrizione: str, funzione) -> None:
    """Esegue una prova, stampa l'esito e lo annota nell'elenco degli esiti."""
    try:
        dettaglio = funzione()
        print(f"[  OK  ] {descrizione}" + (f"  ({dettaglio})" if dettaglio else ""))
        esiti.append(True)
    except Exception as errore:
        print(f"[ERRORE] {descrizione}")
        print(f"         {type(errore).__name__}: {errore}")
        esiti.append(False)


def percorso_per_sql(percorso: Path) -> str:
    """Prepara un percorso per un comando SQL: barre in avanti e apostrofi raddoppiati."""
    return percorso.as_posix().replace("'", "''")


# ----------------------------------------------------------------------------
# LE PROVE
# ----------------------------------------------------------------------------


def prova_python() -> str:
    if sys.version_info < (3, 11):
        raise RuntimeError("serve Python 3.11 o successivo (per il modulo tomllib)")
    return f"Python {sys.version.split()[0]}"


def prova_libreria(nome: str):
    def esegui() -> str:
        modulo = importlib.import_module(nome)
        return f"versione {getattr(modulo, '__version__', 'non indicata')}"

    return esegui


def prova_file_di_input() -> str:
    mancanti = [nome for nome in FILE_DI_INPUT if not (CARTELLA_INPUT / nome).exists()]
    if mancanti:
        raise FileNotFoundError(f"mancano {mancanti}: eseguire  python strumenti/genera_dati.py")
    return f"{len(FILE_DI_INPUT)} file presenti"


def prova_pandas() -> str:
    import pandas as pd

    movimenti = pd.read_csv(CARTELLA_INPUT / "movimenti_20261117.csv", sep=";", dtype=str, keep_default_na=False)
    cambi = pd.read_excel(CARTELLA_INPUT / "cambi.xlsx", sheet_name="cambi")
    return f"{len(movimenti)} movimenti e {len(cambi)} cambi letti"


def prova_sqlite() -> str:
    connessione = sqlite3.connect(":memory:")  # database temporaneo, solo in memoria
    try:
        connessione.execute("CREATE TABLE prova (numero INTEGER)")
        with connessione:
            connessione.executemany("INSERT INTO prova (numero) VALUES (?)", [(1,), (2,), (3,)])
        somma = connessione.execute("SELECT SUM(numero) FROM prova").fetchone()[0]
    finally:
        connessione.close()
    if somma != 6:
        raise RuntimeError(f"somma attesa 6, ottenuta {somma}")
    return f"SQLite {sqlite3.sqlite_version}"


def scrivi_file_di_prova(cartella: Path) -> tuple[Path, Path]:
    """Crea due piccoli file CSV con lo stesso tracciato dei file usati nel notebook 02."""
    file_movimenti = cartella / "movimenti.csv"
    file_conti = cartella / "conti.csv"
    file_movimenti.write_text(
        "id_movimento;id_conto;data_operazione;importo;divisa;codice_causale\n"
        "1;CC00000001;2026-11-17;-10.50;EUR;POS\n"
        "2;CC00000001;2026-11-17;-4.50;EUR;POS\n"
        "3;CC00000002;2026-11-17;100.00;EUR;BON\n"
        "4;CC00000002;2026-11-17;50.00;USD;BON\n"
        "5;CC00000003;2026-11-17;70.00;EUR;BON\n",
        encoding="utf-8",
    )
    file_conti.write_text(
        "id_conto;id_cliente;codice_filiale;tipo_conto;stato\n"
        "CC00000001;CL000001;F001;ORDINARIO;ATTIVO\n"
        "CC00000002;CL000002;F002;ORDINARIO;ATTIVO\n"
        "CC00000003;CL000003;F003;ORDINARIO;CHIUSO\n",
        encoding="utf-8",
    )
    return file_movimenti, file_conti


def controlla_risultato(filiali: list, numeri: list, totali: list) -> None:
    """Il risultato atteso sul file di prova: F001/POS 2 movimenti per -15.00, F002/BON 1 movimento per 100.00."""
    if filiali != ["F001", "F002"] or numeri != [2, 1] or [round(valore, 2) for valore in totali] != [-15.0, 100.0]:
        raise RuntimeError(f"risultato inatteso: {filiali} {numeri} {totali}")


def prova_polars() -> str:
    import polars as pl

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as cartella:
        file_movimenti, file_conti = scrivi_file_di_prova(Path(cartella))
        movimenti = pl.scan_csv(file_movimenti, separator=";")
        conti = pl.scan_csv(file_conti, separator=";")
        domanda = (
            movimenti.filter(pl.col("divisa") == "EUR")
            .join(conti.filter(pl.col("stato") == "ATTIVO"), on="id_conto", how="inner")
            .group_by("codice_filiale", "codice_causale")
            .agg(
                pl.len().alias("numero_movimenti"),
                pl.col("importo").sum().alias("totale"),
            )
            .sort("codice_filiale", "codice_causale")
        )
        risultato = domanda.collect()
        colonne = risultato.to_dict(as_series=False)
    controlla_risultato(colonne["codice_filiale"], colonne["numero_movimenti"], colonne["totale"])
    return "lettura pigra del CSV, filtro, unione, aggregazione"


def comando_duckdb(sorgente_movimenti: str, file_conti: Path) -> str:
    return f"""
        SELECT c.codice_filiale,
               m.codice_causale,
               COUNT(*)       AS numero_movimenti,
               SUM(m.importo) AS totale
        FROM {sorgente_movimenti} AS m
        JOIN read_csv('{percorso_per_sql(file_conti)}', delim = ';', header = true) AS c
          ON m.id_conto = c.id_conto
        WHERE m.divisa = 'EUR'
          AND c.stato = 'ATTIVO'
        GROUP BY c.codice_filiale, m.codice_causale
        ORDER BY c.codice_filiale, m.codice_causale
    """


def prova_duckdb() -> str:
    import duckdb

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as cartella:
        file_movimenti, file_conti = scrivi_file_di_prova(Path(cartella))
        sorgente = f"read_csv('{percorso_per_sql(file_movimenti)}', delim = ';', header = true)"
        risultato = duckdb.sql(comando_duckdb(sorgente, file_conti)).df()
    controlla_risultato(
        risultato["codice_filiale"].tolist(), risultato["numero_movimenti"].tolist(), risultato["totale"].tolist()
    )
    return "SQL direttamente sui file CSV"


def prova_parquet() -> str:
    import duckdb
    import pandas as pd
    import polars as pl

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as cartella:
        file_movimenti, file_conti = scrivi_file_di_prova(Path(cartella))
        file_parquet = Path(cartella) / "movimenti.parquet"

        # Conversione da CSV a Parquet con DuckDB
        sorgente_csv = f"read_csv('{percorso_per_sql(file_movimenti)}', delim = ';', header = true)"
        duckdb.sql(f"SELECT * FROM {sorgente_csv}").write_parquet(str(file_parquet))

        # Lettura del Parquet con i tre strumenti
        con_duckdb = duckdb.sql(
            comando_duckdb(f"read_parquet('{percorso_per_sql(file_parquet)}')", file_conti)
        ).df()
        con_polars = pl.scan_parquet(file_parquet).filter(pl.col("divisa") == "EUR").collect()
        con_pandas = pd.read_parquet(file_parquet, columns=["id_conto", "importo", "divisa", "codice_causale"])

    controlla_risultato(
        con_duckdb["codice_filiale"].tolist(), con_duckdb["numero_movimenti"].tolist(), con_duckdb["totale"].tolist()
    )
    if con_polars.height != 4 or len(con_pandas) != 5:
        raise RuntimeError(f"righe inattese: Polars {con_polars.height}, pandas {len(con_pandas)}")
    return "scrittura con DuckDB, lettura con DuckDB, Polars e pandas"


def main() -> int:
    print("=" * 78)
    print("VERIFICA DELL'AMBIENTE DELLA DEMO")
    print("=" * 78)
    print(f"Interprete Python in uso: {sys.executable}")
    print("(il percorso deve contenere il nome dell'ambiente conda, ad esempio etl_demo)\n")

    prova("Versione di Python", prova_python)

    print("\n--- Librerie ---")
    for nome, scopo in LIBRERIE.items():
        prova(f"{nome:<10} {scopo}", prova_libreria(nome))

    print("\n--- File e strumenti ---")
    prova("File di input", prova_file_di_input)
    prova("pandas: lettura di CSV ed Excel", prova_pandas)
    prova("SQLite: creazione, inserimento, interrogazione", prova_sqlite)
    prova("Polars: stesse istruzioni del notebook 02", prova_polars)
    prova("DuckDB: stesse istruzioni del notebook 02", prova_duckdb)
    prova("Parquet: conversione e lettura", prova_parquet)

    print("\n--- File grande per il notebook 02 (facoltativo per il resto della demo) ---")
    if FILE_GRANDE.exists():
        print(f"[  OK  ] {FILE_GRANDE.name} presente ({FILE_GRANDE.stat().st_size / 1024**2:.0f} MB)")
    else:
        print(f"[ NOTA ] {FILE_GRANDE.name} non ancora generato: eseguire  python strumenti/genera_file_grande.py")

    superate = sum(esiti)
    print("\n" + "=" * 78)
    if all(esiti):
        print(f"TUTTO A POSTO: {superate} prove superate su {len(esiti)}")
        return 0
    non_superate = len(esiti) - superate
    print(f"ATTENZIONE: {non_superate} prove NON superate su {len(esiti)} (vedere le righe [ERRORE] qui sopra)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
