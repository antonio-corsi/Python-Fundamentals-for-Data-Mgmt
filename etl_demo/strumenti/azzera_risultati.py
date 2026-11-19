"""
AZZERAMENTO DEI RISULTATI
=========================

Riporta il progetto allo stato iniziale, cancellando tutto ciò che è stato
prodotto dalle esecuzioni del flusso:

    dati/output    il database SQLite
    dati/scarti    i file degli scarti
    log            i file di log

I file di input (dati/input) e il file grande (dati/grandi_volumi) NON vengono
toccati.

Serve prima di una prova generale o prima della demo, per ripartire da una
situazione pulita e nota.

Come si lancia (dalla cartella del progetto, con l'ambiente conda attivo):

    python strumenti/azzera_risultati.py
"""

from pathlib import Path

RADICE_PROGETTO = Path(__file__).resolve().parent.parent
CARTELLE_DA_SVUOTARE = [
    RADICE_PROGETTO / "dati" / "output",
    RADICE_PROGETTO / "dati" / "scarti",
    RADICE_PROGETTO / "log",
]


def main() -> None:
    cancellati = 0
    for cartella in CARTELLE_DA_SVUOTARE:
        cartella.mkdir(parents=True, exist_ok=True)
        for file in cartella.iterdir():
            # Teniamo il file .gitkeep, che serve solo a conservare la cartella vuota sotto Git
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()  # unlink cancella il file
                cancellati += 1
                print(f"Cancellato {file.relative_to(RADICE_PROGETTO)}")

    print(f"\nFile cancellati: {cancellati}. Il progetto è tornato allo stato iniziale.")


if __name__ == "__main__":
    main()
