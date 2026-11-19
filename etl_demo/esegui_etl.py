"""
PUNTO DI INGRESSO DEL FLUSSO ETL
================================

È il programma che si lancia da riga di comando, a mano oppure da uno
schedulatore (il programma che avvia i flussi a orari prestabiliti).

Esempi, dalla cartella del progetto e con l'ambiente conda attivo:

    python esegui_etl.py --data 2026-11-17
    python esegui_etl.py --data 2026-11-17 --config config.toml
    python esegui_etl.py --help

Che cosa fa:

    1. legge gli argomenti scritti sulla riga di comando (la data di elaborazione)
    2. legge il file dei parametri
    3. prepara il log
    4. esegue il flusso
    5. termina con un "codice di uscita"

Il codice di uscita è il numero con cui un programma comunica l'esito a chi lo
ha lanciato. È ciò che permette allo schedulatore di capire se il flusso è
riuscito e, in caso contrario, di avvisare qualcuno o di non far partire i
flussi successivi. In questo progetto:

    0   tutto bene: i dati sono stati caricati
    1   flusso fermato per un motivo previsto (file mancante, controllo non superato)
    2   errore imprevisto, oppure argomenti scritti in modo errato

Per chi viene da DataStage: la data passata con --data svolge il ruolo di un
parametro del job, valorizzato a ogni esecuzione.
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from etl.configurazione import carica_configurazione
from etl.controlli import ErroreControllo
from etl.flusso import esegui_flusso
from etl.log import prepara_log

USCITA_OK = 0
USCITA_FLUSSO_FERMATO = 1
USCITA_ERRORE_IMPREVISTO = 2


def data_da_testo(testo: str) -> date:
    """Trasforma il testo '2026-11-17' in una data; se il testo non è una data valida, segnala l'errore."""
    try:
        return date.fromisoformat(testo)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"'{testo}' non è una data valida: usare il formato AAAA-MM-GG, ad esempio 2026-11-17"
        ) from None


def leggi_argomenti() -> argparse.Namespace:
    """Definisce e legge gli argomenti della riga di comando."""
    analizzatore = argparse.ArgumentParser(
        description="Flusso ETL dimostrativo: caricamento giornaliero dei movimenti di conto corrente."
    )
    analizzatore.add_argument(
        "--data",
        required=True,
        type=data_da_testo,
        help="data di elaborazione nel formato AAAA-MM-GG, ad esempio 2026-11-17",
    )
    analizzatore.add_argument(
        "--config",
        type=Path,
        default=None,
        help="file dei parametri (se non indicato: config.toml nella cartella del progetto)",
    )
    return analizzatore.parse_args()


def main() -> int:
    """Esegue il flusso e restituisce il codice di uscita."""
    argomenti = leggi_argomenti()

    try:
        config = carica_configurazione(argomenti.config)
    except (OSError, ValueError, KeyError) as errore:
        # File dei parametri mancante, illeggibile o incompleto. Il log non è
        # ancora pronto (la sua cartella è scritta proprio in quel file), quindi
        # scriviamo il messaggio sul canale degli errori del terminale.
        print(f"Impossibile leggere il file dei parametri: {errore}", file=sys.stderr)
        return USCITA_ERRORE_IMPREVISTO

    registro = prepara_log(config["percorsi"]["cartella_log"], argomenti.data)

    try:
        conteggi = esegui_flusso(argomenti.data, config)

    except (ErroreControllo, FileNotFoundError) as errore:
        # Situazioni previste: per capire che cosa è successo basta il messaggio
        registro.error("FLUSSO FERMATO: %s", errore)
        return USCITA_FLUSSO_FERMATO

    except Exception:
        # Situazioni impreviste: registro.exception aggiunge al log anche la
        # "traccia" dell'errore, cioè l'elenco delle righe di codice attraversate,
        # indispensabile per chi dovrà capire che cosa è andato storto.
        registro.exception("FLUSSO TERMINATO CON UN ERRORE IMPREVISTO")
        return USCITA_ERRORE_IMPREVISTO

    registro.info(
        "FLUSSO TERMINATO CORRETTAMENTE: lette %d, caricate %d, scartate %d",
        conteggi["righe_lette"],
        conteggi["righe_caricate"],
        conteggi["righe_scartate"],
    )
    return USCITA_OK


if __name__ == "__main__":
    # sys.exit passa il codice di uscita al sistema operativo
    sys.exit(main())
