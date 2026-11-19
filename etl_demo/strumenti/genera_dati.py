"""
GENERATORE DEI DATI SINTETICI DELLA DEMO
========================================

Questo script crea i file di input del flusso ETL dimostrativo.
I dati sono "sintetici", cioè inventati: nessun cliente, conto o movimento è reale.

Che cosa produce (nella cartella dati/input):

    clienti.csv              anagrafica dei clienti
    conti.csv                anagrafica dei conti correnti
    cambi.xlsx               cambi giornalieri contro euro (file Excel)
    movimenti_20261116.csv   movimenti di lunedì 16/11/2026    (file "normale")
    movimenti_20261117.csv   movimenti di martedì 17/11/2026   (file "normale")
    movimenti_20261118.csv   movimenti di mercoledì 18/11/2026 (file volutamente corrotto)

Nei file dei movimenti inseriamo di proposito alcuni errori, perché un flusso ETL
serio deve saperli riconoscere e scartare:

    - date non valide            (es. 31/02/2026, data vuota, formato diverso da gg/mm/aaaa)
    - importi non validi         (es. "n.d.", importo vuoto, punto decimale al posto della virgola)
    - righe duplicate            (lo stesso movimento presente due volte)
    - conti inesistenti          (il conto non è presente nell'anagrafica)
    - divisa senza cambio        (movimenti in JPY, ma la tabella dei cambi non contiene lo yen)
    - codici scritti male        (spazi e minuscole: " eur", "pos "): questi NON vanno
                                  scartati, vanno solo ripuliti

Il generatore è "deterministico": usa un seme fisso (SEME), quindi ogni esecuzione
produce esattamente gli stessi file. In questo modo i numeri citati nella scaletta
della demo restano validi anche se rigeneriamo i dati.

Come si lancia (dalla cartella del progetto, con l'ambiente conda attivo):

    python strumenti/genera_dati.py
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# PARAMETRI DEL GENERATORE
# ----------------------------------------------------------------------------

SEME = 42  # numero di partenza del generatore casuale: stesso seme = stessi dati

RADICE_PROGETTO = Path(__file__).resolve().parent.parent
CARTELLA_INPUT = RADICE_PROGETTO / "dati" / "input"

NUMERO_CLIENTI = 2_000
NUMERO_CONTI = 3_000
NUMERO_MOVIMENTI_AL_GIORNO = 20_000

GIORNI_NORMALI = [date(2026, 11, 16), date(2026, 11, 17)]
GIORNO_CORROTTO = date(2026, 11, 18)
GIORNI_DEI_CAMBI = [date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 18), date(2026, 11, 19)]

# Quante righe sbagliate inseriamo in un file "normale"
ERRORI_FILE_NORMALE = {
    "DATA_NON_VALIDA": 60,
    "IMPORTO_NON_VALIDO": 50,
    "CONTO_INESISTENTE": 70,
    "CAMBIO_MANCANTE": 30,
    "DUPLICATO": 100,
}
# Nel file corrotto, in più, il 30% delle righe ha l'importo in un formato sbagliato
QUOTA_IMPORTI_CORROTTI = 0.30

# Causali dei movimenti: codice -> (peso, descrizione, segno, importo minimo, importo massimo)
# Il "peso" è la frequenza con cui la causale compare; il segno vale -1 per le uscite,
# +1 per le entrate e 0 quando può essere sia un'entrata sia un'uscita.
CAUSALI = {
    "POS": (0.35, "Pagamento con carta", -1, 5, 300),
    "BON": (0.20, "Bonifico", 0, 50, 5_000),
    "PRE": (0.12, "Prelievo contante", -1, 20, 500),
    "SDD": (0.12, "Addebito diretto", -1, 20, 400),
    "STI": (0.08, "Accredito stipendio", +1, 1_200, 3_500),
    "COM": (0.08, "Commissioni e spese", -1, 1, 15),
    "VER": (0.05, "Versamento", +1, 100, 5_000),
}

# Cambi di partenza (quante unità di divisa servono per comprare 1 euro).
# Sono valori inventati ma verosimili: NON sono i cambi ufficiali di quei giorni.
CAMBI_BASE = {"EUR": 1.0, "USD": 1.10, "GBP": 0.86, "CHF": 0.95}


# ----------------------------------------------------------------------------
# FUNZIONI DI SUPPORTO
# ----------------------------------------------------------------------------

def formatta_importo(valore: float) -> str:
    """Trasforma un numero nel formato italiano: 1234.5 -> '1.234,50'."""
    testo = f"{valore:,.2f}"  # formato anglosassone: '1,234.50'
    # Scambiamo virgole e punti passando da un carattere provvisorio ("X")
    return testo.replace(",", "X").replace(".", ",").replace("X", ".")


def genera_clienti(casuale: np.random.Generator) -> pd.DataFrame:
    """Crea l'anagrafica dei clienti."""
    giorni_dal_2005 = casuale.integers(0, 365 * 21, size=NUMERO_CLIENTI)
    inizio_rapporto = pd.Timestamp("2005-01-03") + pd.to_timedelta(giorni_dal_2005, unit="D")
    return pd.DataFrame(
        {
            "id_cliente": [f"CL{numero:06d}" for numero in range(1, NUMERO_CLIENTI + 1)],
            "segmento": casuale.choice(
                ["RETAIL", "PRIVATE", "SMALL BUSINESS", "CORPORATE"],
                size=NUMERO_CLIENTI,
                p=[0.70, 0.10, 0.15, 0.05],
            ),
            "provincia": casuale.choice(
                ["MI", "RM", "TO", "NA", "BO", "FI", "GE", "PA", "BA", "VE"], size=NUMERO_CLIENTI
            ),
            "data_inizio_rapporto": inizio_rapporto.strftime("%Y-%m-%d"),
        }
    )


def genera_conti(casuale: np.random.Generator, clienti: pd.DataFrame) -> pd.DataFrame:
    """Crea l'anagrafica dei conti: ogni conto appartiene a un cliente e a una filiale."""
    return pd.DataFrame(
        {
            "id_conto": [f"CC{numero:08d}" for numero in range(1, NUMERO_CONTI + 1)],
            "id_cliente": casuale.choice(clienti["id_cliente"].to_numpy(), size=NUMERO_CONTI),
            "codice_filiale": [f"F{numero:03d}" for numero in casuale.integers(1, 26, size=NUMERO_CONTI)],
            "tipo_conto": casuale.choice(["ORDINARIO", "GIOVANI", "BUSINESS"], size=NUMERO_CONTI, p=[0.75, 0.10, 0.15]),
            "stato": casuale.choice(["ATTIVO", "CHIUSO"], size=NUMERO_CONTI, p=[0.95, 0.05]),
        }
    )


def genera_cambi() -> pd.DataFrame:
    """Crea la tabella dei cambi: una riga per ogni giorno e per ogni divisa."""
    righe = []
    for posizione, giorno in enumerate(GIORNI_DEI_CAMBI):
        for divisa, cambio_base in CAMBI_BASE.items():
            # Piccola variazione giornaliera, uguale a ogni esecuzione
            variazione = 0.0 if divisa == "EUR" else 0.002 * posizione
            righe.append({"data": pd.Timestamp(giorno), "divisa": divisa, "cambio": round(cambio_base + variazione, 4)})
    return pd.DataFrame(righe)


def genera_movimenti_puliti(casuale: np.random.Generator, giorno: date, conti: pd.DataFrame) -> pd.DataFrame:
    """Crea i movimenti di un giorno, ancora senza errori."""
    numero = NUMERO_MOVIMENTI_AL_GIORNO
    codici = list(CAUSALI)
    pesi = [CAUSALI[codice][0] for codice in codici]
    causali = casuale.choice(codici, size=numero, p=pesi)

    importi = np.zeros(numero)
    descrizioni = np.empty(numero, dtype=object)
    for codice, (_, descrizione, segno, minimo, massimo) in CAUSALI.items():
        righe_della_causale = causali == codice
        quante = int(righe_della_causale.sum())
        valori = casuale.uniform(minimo, massimo, size=quante)
        if codice == "PRE":
            valori = np.round(valori / 20) * 20  # i prelievi sono multipli di 20 euro
        if codice == "BON":
            # Un bonifico su cento è di importo elevato (serve per il flag "rilevante")
            grandi = casuale.random(quante) < 0.01
            valori[grandi] = casuale.uniform(10_000, 80_000, size=int(grandi.sum()))
        segni = casuale.choice([-1, 1], size=quante) if segno == 0 else np.full(quante, segno)
        importi[righe_della_causale] = np.round(valori * segni, 2)
        descrizioni[righe_della_causale] = descrizione

    return pd.DataFrame(
        {
            "id_movimento": [f"M{giorno:%Y%m%d}-{progressivo:06d}" for progressivo in range(1, numero + 1)],
            "id_conto": casuale.choice(conti["id_conto"].to_numpy(), size=numero),
            "data_operazione": f"{giorno:%d/%m/%Y}",
            "importo": [formatta_importo(valore) for valore in importi],
            "divisa": casuale.choice(["EUR", "USD", "GBP", "CHF"], size=numero, p=[0.92, 0.05, 0.02, 0.01]),
            "codice_causale": causali,
            "descrizione": descrizioni,
        }
    )


def sporca_movimenti(
    casuale: np.random.Generator, movimenti: pd.DataFrame, giorno: date, file_corrotto: bool
) -> tuple[pd.DataFrame, dict]:
    """
    Inserisce gli errori voluti nei movimenti.

    Restituisce la tabella "sporcata" e un dizionario con il numero di righe
    sbagliate per ciascun tipo di errore: ci servirà per controllare che il
    flusso ETL scarti esattamente le righe che ci aspettiamo.
    """
    movimenti = movimenti.copy()
    errori = dict(ERRORI_FILE_NORMALE)
    if file_corrotto:
        errori["IMPORTO_NON_VALIDO"] += int(len(movimenti) * QUOTA_IMPORTI_CORROTTI)

    # Mescoliamo le posizioni delle righe e ne prendiamo dei gruppi che non si
    # sovrappongono: così ogni riga sbagliata ha un solo tipo di errore.
    posizioni = casuale.permutation(len(movimenti))
    inizio = 0
    gruppi = {}
    for motivo, quante in errori.items():
        gruppi[motivo] = posizioni[inizio : inizio + quante]
        inizio += quante

    # --- Date non valide ---
    date_sbagliate = ["31/02/2026", "", f"{giorno:%Y-%m-%d}", f"{giorno:%d-%m-%Y}", "00/00/0000"]
    colonna = movimenti.columns.get_loc("data_operazione")
    movimenti.iloc[gruppi["DATA_NON_VALIDA"], colonna] = casuale.choice(
        date_sbagliate, size=errori["DATA_NON_VALIDA"]
    )

    # --- Importi non validi ---
    importi_sbagliati = ["n.d.", "", "1234.56", "12,3", "abc", "1,234.56"]
    colonna = movimenti.columns.get_loc("importo")
    movimenti.iloc[gruppi["IMPORTO_NON_VALIDO"], colonna] = casuale.choice(
        importi_sbagliati, size=errori["IMPORTO_NON_VALIDO"]
    )

    # --- Conti che non esistono in anagrafica ---
    colonna = movimenti.columns.get_loc("id_conto")
    movimenti.iloc[gruppi["CONTO_INESISTENTE"], colonna] = [
        f"CC99{numero:06d}" for numero in casuale.integers(0, 999_999, size=errori["CONTO_INESISTENTE"])
    ]

    # --- Divisa per la quale non abbiamo il cambio ---
    colonna = movimenti.columns.get_loc("divisa")
    movimenti.iloc[gruppi["CAMBIO_MANCANTE"], colonna] = "JPY"

    # --- Codici scritti male (da ripulire, NON da scartare) ---
    # Li mettiamo solo su righe corrette, così non interferiscono con i conteggi degli scarti.
    righe_corrette = posizioni[inizio:]
    da_ritoccare = casuale.choice(righe_corrette, size=700, replace=False)
    for nome_colonna, righe in [
        ("divisa", da_ritoccare[:300]),
        ("codice_causale", da_ritoccare[300:600]),
        ("id_conto", da_ritoccare[600:]),
    ]:
        colonna = movimenti.columns.get_loc(nome_colonna)
        originali = movimenti.iloc[righe, colonna]
        movimenti.iloc[righe, colonna] = [
            f" {valore.lower()}" if indice % 2 == 0 else f"{valore.lower()}  "
            for indice, valore in enumerate(originali)
        ]

    # --- Righe duplicate: copiamo alcune righe corrette e le aggiungiamo in fondo ---
    da_duplicare = casuale.choice(righe_corrette, size=errori["DUPLICATO"], replace=False)
    movimenti = pd.concat([movimenti, movimenti.iloc[da_duplicare]], ignore_index=True)

    # Infine rimescoliamo le righe, così gli errori sono sparsi in tutto il file
    movimenti = movimenti.sample(frac=1, random_state=SEME).reset_index(drop=True)
    return movimenti, errori


def main() -> None:
    casuale = np.random.default_rng(SEME)
    CARTELLA_INPUT.mkdir(parents=True, exist_ok=True)

    clienti = genera_clienti(casuale)
    conti = genera_conti(casuale, clienti)
    cambi = genera_cambi()

    # lineterminator="\n": stesso carattere di fine riga su Windows, Linux e macOS
    clienti.to_csv(CARTELLA_INPUT / "clienti.csv", sep=";", index=False, encoding="utf-8", lineterminator="\n")
    conti.to_csv(CARTELLA_INPUT / "conti.csv", sep=";", index=False, encoding="utf-8", lineterminator="\n")
    cambi.to_excel(CARTELLA_INPUT / "cambi.xlsx", sheet_name="cambi", index=False)
    print(f"clienti.csv: {len(clienti)} righe")
    print(f"conti.csv:   {len(conti)} righe")
    print(f"cambi.xlsx:  {len(cambi)} righe")

    for giorno in GIORNI_NORMALI + [GIORNO_CORROTTO]:
        puliti = genera_movimenti_puliti(casuale, giorno, conti)
        sporchi, errori = sporca_movimenti(casuale, puliti, giorno, file_corrotto=(giorno == GIORNO_CORROTTO))
        nome_file = f"movimenti_{giorno:%Y%m%d}.csv"
        sporchi.to_csv(CARTELLA_INPUT / nome_file, sep=";", index=False, encoding="utf-8", lineterminator="\n")

        scarti_attesi = sum(errori.values())
        print(f"\n{nome_file}: {len(sporchi)} righe")
        for motivo, quante in errori.items():
            print(f"    {motivo:<20} {quante:>6}")
        print(f"    {'TOTALE SCARTI ATTESI':<20} {scarti_attesi:>6}  ({scarti_attesi / len(sporchi):.1%})")
        print(f"    {'RIGHE BUONE ATTESE':<20} {len(sporchi) - scarti_attesi:>6}")


if __name__ == "__main__":
    main()
