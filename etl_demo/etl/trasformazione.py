"""
T di ETL: TRASFORMAZIONE (in inglese "Transform").

Qui i dati letti dalle sorgenti vengono controllati, ripuliti, arricchiti con le
anagrafiche, convertiti in euro e infine aggregati.

Ogni funzione di questo modulo segue lo stesso schema:

    riceve una tabella  ->  restituisce le righe valide  +  le righe scartate

Le righe scartate non vengono buttate via: le raccogliamo, insieme al motivo
dello scarto, e alla fine le scriviamo in un file. In questo modo nessuna riga
"sparisce" e possiamo sempre spiegare che fine ha fatto ogni riga letta.

Le funzioni non leggono file e non scrivono su database: lavorano solo sulle
tabelle che ricevono. Per questo sono facili da provare una per una con dei
test automatici (cartella tests).

Per chi viene da DataStage: queste funzioni corrispondono agli stage
Transformer, Remove Duplicates, Lookup e Aggregator; la tabella degli scarti
corrisponde ai link di reject.
"""

import logging

import pandas as pd

registro = logging.getLogger(__name__)

# Formato atteso per la data: giorno/mese/anno con l'anno di quattro cifre (es. 17/11/2026)
FORMATO_DATA = "%d/%m/%Y"

# Formato atteso per l'importo, scritto come "espressione regolare", cioè come
# modello che descrive come deve essere fatto un testo. Si legge così:
#
#   -?                       un segno meno facoltativo
#   ( \d{1,3}(\.\d{3})+      da 1 a 3 cifre seguite da uno o più gruppi ".123" (punto delle migliaia)
#     | \d+ )                oppure una semplice sequenza di cifre senza punti
#   ,\d{2}                   la virgola e poi esattamente due cifre decimali
#
# Esempi accettati:  "-12,50"   "1.234,56"   "1234,56"
# Esempi rifiutati:  "1234.56"  "12,3"       "n.d."     ""
FORMATO_IMPORTO = r"-?(\d{1,3}(\.\d{3})+|\d+),\d{2}"


def separa_scarti(tabella: pd.DataFrame, righe_valide: pd.Series, motivo: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide una tabella in due parti: le righe valide e le righe scartate.

    tabella        la tabella da dividere
    righe_valide   una colonna di valori Vero/Falso, uno per riga: Vero = riga valida
    motivo         il codice che spiega perché le altre righe vengono scartate

    Delle righe scartate teniamo solo il numero di riga nel file di origine
    (riga_file) e il motivo: il contenuto originale lo recupereremo alla fine.
    """
    valide = tabella[righe_valide].copy()
    scartate = tabella.loc[~righe_valide, ["riga_file"]].copy()  # il simbolo ~ significa "non"
    scartate["motivo_scarto"] = motivo

    registro.info("Controllo %-20s righe valide: %6d   righe scartate: %5d", motivo, len(valide), len(scartate))
    return valide, scartate


def controlla_formati(grezzi: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Controlla la data e l'importo di ogni riga e li converte dal testo al tipo corretto.
    Ripulisce inoltre i codici (spazi in eccesso, minuscole).
    """
    movimenti = grezzi.copy()

    # --- 1) DATA --------------------------------------------------------------
    # Con errors="coerce" le date che non rispettano il formato non provocano un
    # errore: diventano NaT ("Not a Time", cioè "data mancante"). Subito dopo
    # scartiamo proprio le righe rimaste senza data.
    movimenti["data_operazione"] = pd.to_datetime(movimenti["data_operazione"], format=FORMATO_DATA, errors="coerce")
    movimenti, scarti_data = separa_scarti(movimenti, movimenti["data_operazione"].notna(), "DATA_NON_VALIDA")

    # --- 2) IMPORTO -----------------------------------------------------------
    # Prima verifichiamo che il testo rispetti esattamente il formato atteso...
    formato_corretto = movimenti["importo"].str.fullmatch(FORMATO_IMPORTO, na=False)
    movimenti, scarti_importo = separa_scarti(movimenti, formato_corretto, "IMPORTO_NON_VALIDO")

    # ...e solo dopo lo convertiamo in numero. Un importo scritto in un formato
    # diverso deve essere scartato, non "interpretato" in qualche modo.
    movimenti["importo"] = (
        movimenti["importo"]
        .str.replace(".", "", regex=False)  # togliamo il punto delle migliaia: "1.234,56" -> "1234,56"
        .str.replace(",", ".", regex=False)  # la virgola decimale diventa punto: "1234,56" -> "1234.56"
        .astype(float)  # da testo a numero con la virgola
    )

    # --- 3) PULIZIA DEI CODICI --------------------------------------------------
    # " eur" e "EUR" devono essere la stessa cosa: togliamo gli spazi ai lati
    # (strip) e portiamo tutto in maiuscolo (upper).
    for colonna in ["id_conto", "divisa", "codice_causale"]:
        movimenti[colonna] = movimenti[colonna].str.strip().str.upper()
    movimenti["descrizione"] = movimenti["descrizione"].str.strip()

    scarti = pd.concat([scarti_data, scarti_importo], ignore_index=True)
    return movimenti, scarti


def togli_duplicati(movimenti: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lo stesso id_movimento non può comparire due volte.
    Teniamo la prima riga che incontriamo e scartiamo le ripetizioni successive.
    """
    gia_incontrato = movimenti.duplicated(subset="id_movimento", keep="first")
    return separa_scarti(movimenti, ~gia_incontrato, "DUPLICATO")


def aggiungi_anagrafiche(
    movimenti: pd.DataFrame, conti: pd.DataFrame, clienti: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggiunge a ogni movimento le informazioni del conto (cliente, filiale) e del
    cliente (segmento). I movimenti il cui conto non esiste in anagrafica vengono scartati.

    L'operazione che affianca due tabelle usando una colonna in comune si chiama
    "merge" in pandas ed equivale alla JOIN del linguaggio SQL.
    """
    # Per ogni conto ricaviamo anche il segmento del cliente a cui appartiene
    conti_completi = conti.merge(
        clienti[["id_cliente", "segmento"]],
        on="id_cliente",
        how="left",  # "left": teniamo tutti i conti, anche se il cliente non si trovasse
        validate="many_to_one",  # pandas controlla per noi che id_cliente sia unico fra i clienti
    )

    arricchiti = movimenti.merge(
        conti_completi[["id_conto", "id_cliente", "codice_filiale", "segmento"]],
        on="id_conto",
        how="left",  # teniamo tutti i movimenti: quelli senza conto restano con le colonne nuove vuote
        validate="many_to_one",  # molti movimenti per un solo conto: mai il contrario
    )

    # Se la filiale è rimasta vuota, significa che il conto non è stato trovato
    conto_trovato = arricchiti["codice_filiale"].notna()
    return separa_scarti(arricchiti, conto_trovato, "CONTO_INESISTENTE")


def converti_in_euro(movimenti: pd.DataFrame, cambi: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcola il controvalore in euro di ogni movimento, usando il cambio del
    giorno dell'operazione. I movimenti per i quali non esiste un cambio
    (giorno o divisa non presenti nella tabella) vengono scartati.

    NOTA: per semplicità trattiamo gli importi come numeri con la virgola
    (float). In un flusso reale gli importi si gestiscono con il tipo Decimal
    oppure in centesimi interi, per evitare errori di arrotondamento.
    """
    cambi_del_giorno = cambi.rename(columns={"data": "data_operazione"})

    con_cambio = movimenti.merge(
        cambi_del_giorno[["data_operazione", "divisa", "cambio"]],
        on=["data_operazione", "divisa"],  # la coppia giorno + divisa identifica un cambio
        how="left",
        validate="many_to_one",
    )

    valide, scartate = separa_scarti(con_cambio, con_cambio["cambio"].notna(), "CAMBIO_MANCANTE")

    # Il cambio indica quante unità di divisa servono per 1 euro: per passare
    # dalla divisa all'euro dobbiamo quindi dividere.
    valide["importo_eur"] = (valide["importo"] / valide["cambio"]).round(2)
    return valide, scartate


def segna_rilevanti(movimenti: pd.DataFrame, soglia_eur: float) -> pd.DataFrame:
    """
    Aggiunge la colonna flag_rilevante: Vero se il controvalore in euro, senza
    segno, raggiunge la soglia indicata nel file dei parametri.
    """
    movimenti = movimenti.copy()
    movimenti["flag_rilevante"] = movimenti["importo_eur"].abs() >= soglia_eur
    return movimenti


def calcola_riepilogo(movimenti: pd.DataFrame) -> pd.DataFrame:
    """
    Riassume i movimenti per filiale e causale: quanti sono e quanto valgono in euro.
    Equivale a una SELECT ... GROUP BY del linguaggio SQL.
    """
    riepilogo = movimenti.groupby(["codice_filiale", "codice_causale"], as_index=False).agg(
        numero_movimenti=("id_movimento", "count"),
        totale_eur=("importo_eur", "sum"),
    )
    riepilogo["totale_eur"] = riepilogo["totale_eur"].round(2)
    return riepilogo


def componi_scarti(grezzi: pd.DataFrame, elenco_scarti: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Riunisce gli scarti prodotti dai vari controlli e, per ciascuno, recupera la
    riga originale così come era scritta nel file (usando il numero di riga).

    Il risultato ha le colonne: riga_file, motivo_scarto e poi tutte le colonne
    originali del file, ancora in formato testo.
    """
    tutti_gli_scarti = pd.concat(elenco_scarti, ignore_index=True)
    scarti = tutti_gli_scarti.merge(grezzi, on="riga_file", how="left", validate="one_to_one")
    return scarti.sort_values("riga_file").reset_index(drop=True)
