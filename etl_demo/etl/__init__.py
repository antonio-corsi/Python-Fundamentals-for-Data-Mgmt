"""
Pacchetto "etl": il codice del flusso dimostrativo.

Un "pacchetto" in Python è semplicemente una cartella che contiene file .py
(i "moduli") e un file __init__.py come questo. Ogni modulo ha un compito:

    configurazione.py   legge il file dei parametri (config.toml)
    log.py              prepara il log su schermo e su file
    estrazione.py       E di ETL: legge i file sorgente
    trasformazione.py   T di ETL: controlla, ripulisce, arricchisce, aggrega
    caricamento.py      L di ETL: scrive nel database di destinazione
    flusso.py           mette in fila tutti i passi, dall'inizio alla fine
"""
