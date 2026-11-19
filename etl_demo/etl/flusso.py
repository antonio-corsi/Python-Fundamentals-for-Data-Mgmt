"""
IL FLUSSO COMPLETO: mette in fila tutti i passi, dall'estrazione al caricamento.

È il file da cui partire per capire che cosa fa il flusso: si legge dall'alto
verso il basso, come si legge da sinistra a destra il disegno di un job in uno
strumento grafico.

    ESTRAZIONE      movimenti del giorno (CSV), conti e clienti (CSV), cambi (Excel)
        |
    TRASFORMAZIONE  controllo dei formati -> duplicati -> anagrafiche -> euro -> riepilogo
        |
    SCARTI          le righe scartate, con il motivo, finiscono in un file CSV
        |
    CONTROLLI       quadratura dei conteggi e soglia massima degli scarti
        |
    CARICAMENTO     movimenti e riepilogo nel database, in un'unica transazione
"""

import logging
from datetime import date, datetime

from etl.caricamento import apri_database, carica_risultati, registra_esecuzione
from etl.controlli import verifica_quadratura, verifica_soglia_scarti
from etl.estrazione import leggi_anagrafica, leggi_cambi, leggi_movimenti
from etl.trasformazione import (
    aggiungi_anagrafiche,
    calcola_riepilogo,
    componi_scarti,
    controlla_formati,
    converti_in_euro,
    segna_rilevanti,
    togli_duplicati,
)

registro = logging.getLogger(__name__)


def esegui_flusso(data_elaborazione: date, config: dict) -> dict:
    """
    Esegue il flusso per una data di elaborazione e restituisce i conteggi finali.

    La "data di elaborazione" è il giorno a cui si riferiscono i dati da
    caricare: decide quale file leggere (movimenti_AAAAMMGG.csv) e con quale
    data vengono marcate le righe nel database.

    Questa funzione si occupa della "cornice": misura la durata e, comunque
    vada, scrive una riga nella tabella log_esecuzioni. I passi veri e propri
    sono nella funzione esegui_passi, qui sotto.
    """
    avvio = datetime.now()
    registro.info("=== AVVIO del flusso per la data di elaborazione %s ===", data_elaborazione)

    conteggi = {"righe_lette": None, "righe_caricate": None, "righe_scartate": None}
    esito = "ERRORE"
    messaggio = "Esecuzione interrotta"

    connessione = apri_database(config["percorsi"]["file_database"])
    try:
        esegui_passi(data_elaborazione, config, connessione, conteggi)
        esito = "OK"
        messaggio = ""
    except Exception as errore:
        # Annotiamo il motivo e rilanciamo l'errore verso chi ci ha chiamato
        messaggio = f"{type(errore).__name__}: {errore}"
        raise
    finally:
        # Il blocco "finally" viene eseguito sempre, sia in caso di successo sia in caso di errore
        durata = (datetime.now() - avvio).total_seconds()
        registra_esecuzione(connessione, avvio, data_elaborazione, esito, conteggi, durata, messaggio)
        connessione.close()
        registro.info("=== FINE del flusso: esito %s, durata %.2f secondi ===", esito, durata)

    return conteggi


def esegui_passi(data_elaborazione: date, config: dict, connessione, conteggi: dict) -> None:
    """I passi del flusso, uno dopo l'altro."""
    percorsi = config["percorsi"]
    regole = config["regole"]
    cartella_input = percorsi["cartella_input"]

    # ------------------------------------------------------------------
    # E = ESTRAZIONE
    # ------------------------------------------------------------------
    grezzi = leggi_movimenti(cartella_input / f"movimenti_{data_elaborazione:%Y%m%d}.csv")
    conti = leggi_anagrafica(cartella_input / "conti.csv", colonna_chiave="id_conto")
    clienti = leggi_anagrafica(cartella_input / "clienti.csv", colonna_chiave="id_cliente")
    cambi = leggi_cambi(cartella_input / "cambi.xlsx")
    conteggi["righe_lette"] = len(grezzi)

    # ------------------------------------------------------------------
    # T = TRASFORMAZIONE
    # Ogni passo restituisce le righe valide (che proseguono) e gli scarti.
    # ------------------------------------------------------------------
    movimenti, scarti_formati = controlla_formati(grezzi)
    movimenti, scarti_duplicati = togli_duplicati(movimenti)
    movimenti, scarti_conti = aggiungi_anagrafiche(movimenti, conti, clienti)
    movimenti, scarti_cambi = converti_in_euro(movimenti, cambi)
    movimenti = segna_rilevanti(movimenti, regole["soglia_importo_rilevante_eur"])
    riepilogo = calcola_riepilogo(movimenti)

    # ------------------------------------------------------------------
    # SCARTI: li scriviamo SEMPRE, anche se poi il flusso si fermerà.
    # Sono proprio gli scarti a spiegare che cosa non va nel file di input.
    # ------------------------------------------------------------------
    scarti = componi_scarti(grezzi, [scarti_formati, scarti_duplicati, scarti_conti, scarti_cambi])
    conteggi["righe_scartate"] = len(scarti)

    percorsi["cartella_scarti"].mkdir(parents=True, exist_ok=True)
    file_scarti = percorsi["cartella_scarti"] / f"scarti_movimenti_{data_elaborazione:%Y%m%d}.csv"
    scarti.to_csv(file_scarti, sep=";", index=False, encoding="utf-8")
    registro.info("Scritto %s: %d righe scartate", file_scarti.name, len(scarti))
    for motivo, quante in scarti["motivo_scarto"].value_counts().items():
        registro.info("    %-20s %6d", motivo, quante)

    # ------------------------------------------------------------------
    # CONTROLLI: se uno dei due non è superato, il flusso si ferma qui
    # e nel database non viene scritto nulla.
    # ------------------------------------------------------------------
    verifica_quadratura(len(grezzi), len(movimenti), len(scarti))
    verifica_soglia_scarti(len(grezzi), len(scarti), regole["soglia_scarti_percentuale"])

    # ------------------------------------------------------------------
    # L = CARICAMENTO
    # ------------------------------------------------------------------
    carica_risultati(connessione, movimenti, riepilogo, data_elaborazione)
    conteggi["righe_caricate"] = len(movimenti)

    registro.info(
        "Movimenti rilevanti (soglia %.0f euro): %d",
        regole["soglia_importo_rilevante_eur"],
        int(movimenti["flag_rilevante"].sum()),
    )
