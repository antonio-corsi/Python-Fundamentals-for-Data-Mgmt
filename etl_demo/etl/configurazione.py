"""
Lettura del file dei parametri (config.toml).

Teniamo i parametri FUORI dal codice: per passare dall'ambiente di sviluppo a
quello di produzione basta cambiare il file dei parametri, senza toccare i
programmi.
"""

import tomllib  # modulo della libreria standard che legge i file TOML
from pathlib import Path

# Cartella principale del progetto, calcolata a partire dalla posizione di questo
# file: .../demo_etl_python/etl/configurazione.py  ->  .../demo_etl_python
# In questo modo non dipendiamo dalla cartella da cui viene lanciato il programma.
RADICE_PROGETTO = Path(__file__).resolve().parent.parent

FILE_PARAMETRI_PREDEFINITO = RADICE_PROGETTO / "config.toml"


def carica_configurazione(file_parametri: Path | None = None) -> dict:
    """
    Legge il file dei parametri e restituisce un dizionario con due voci:

        "percorsi"  cartelle e file, già trasformati in percorsi completi
        "regole"    soglie usate dai controlli

    Se non indichiamo alcun file, usiamo config.toml nella cartella del progetto.
    """
    if file_parametri is None:
        file_parametri = FILE_PARAMETRI_PREDEFINITO

    # I file TOML vanno aperti in modalità binaria ("rb"): lo richiede tomllib
    with open(file_parametri, "rb") as file_aperto:
        parametri = tomllib.load(file_aperto)

    # Trasformiamo ogni percorso relativo (es. "dati/input") in un percorso
    # completo (es. C:\progetti\demo_etl_python\dati\input)
    percorsi = {}
    for nome, valore in parametri["percorsi"].items():
        percorsi[nome] = (RADICE_PROGETTO / valore).resolve()

    return {"percorsi": percorsi, "regole": parametri["regole"]}
