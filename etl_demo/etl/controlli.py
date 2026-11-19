"""
CONTROLLI che possono fermare il flusso.

Un flusso ETL robusto non si limita a "non dare errore": verifica da solo di
aver lavorato bene e, in caso di dubbio, si ferma PRIMA di scrivere nel
database. Meglio un caricamento mancato e segnalato che un caricamento sbagliato
e silenzioso.

Qui ci sono due controlli:

    quadratura        ogni riga letta deve essere o caricata o scartata: nessuna
                      riga può sparire e nessuna può moltiplicarsi
    soglia scarti     se gli scarti sono troppi, il file di input ha quasi
                      certamente un problema e non va caricato
"""

import logging

registro = logging.getLogger(__name__)


class ErroreControllo(Exception):
    """
    Errore sollevato quando un controllo non è superato.

    Definire un tipo di errore nostro (una "eccezione" su misura) ci permette di
    distinguere i problemi sui dati dagli errori tecnici, come un disco pieno.
    """


def verifica_quadratura(righe_lette: int, righe_buone: int, righe_scartate: int) -> None:
    """Controlla che: righe lette = righe buone + righe scartate."""
    if righe_lette != righe_buone + righe_scartate:
        raise ErroreControllo(
            f"Quadratura NON superata: lette {righe_lette}, buone {righe_buone}, scartate {righe_scartate} "
            f"(differenza {righe_lette - righe_buone - righe_scartate})"
        )
    registro.info("Quadratura superata: lette %d = buone %d + scartate %d", righe_lette, righe_buone, righe_scartate)


def verifica_soglia_scarti(righe_lette: int, righe_scartate: int, soglia_percentuale: float) -> None:
    """Controlla che la percentuale di righe scartate non superi la soglia dei parametri."""
    if righe_lette == 0:
        raise ErroreControllo("Il file di input non contiene alcuna riga di dati")

    percentuale = righe_scartate / righe_lette * 100
    if percentuale > soglia_percentuale:
        raise ErroreControllo(
            f"Scarti al {percentuale:.1f}% delle righe lette: oltre la soglia del {soglia_percentuale:.1f}%. "
            "Nessun dato viene caricato."
        )
    registro.info(
        "Scarti al %.1f%% delle righe lette (soglia %.1f%%): controllo superato", percentuale, soglia_percentuale
    )
