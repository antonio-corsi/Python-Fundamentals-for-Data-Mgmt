"""
TEST AUTOMATICI DELLE TRASFORMAZIONI
====================================

Un "test automatico" è una piccola funzione che esegue un pezzo del nostro
codice su un caso semplice, di cui conosciamo già il risultato giusto, e
verifica che il risultato ottenuto sia proprio quello.

A che cosa servono: quando fra sei mesi modificheremo una regola, basterà
rilanciare i test per sapere in pochi secondi se abbiamo rotto qualcos'altro.

Usiamo la libreria pytest, che funziona per convenzioni:

    - i file dei test si chiamano test_*.py
    - le funzioni di test si chiamano test_*
    - la verifica si scrive con la parola chiave "assert" (in italiano
      "afferma"): se l'affermazione è falsa, il test fallisce

Come si lanciano: dal terminale con il comando  pytest  oppure, in VS Code,
dal pannello "Testing" (l'icona a forma di ampolla nella barra laterale).
"""

import pandas as pd

from etl.trasformazione import (
    aggiungi_anagrafiche,
    calcola_riepilogo,
    componi_scarti,
    controlla_formati,
    converti_in_euro,
    segna_rilevanti,
    togli_duplicati,
)

# ----------------------------------------------------------------------------
# FUNZIONI DI SUPPORTO: costruiscono piccole tabelle di prova
# ----------------------------------------------------------------------------


def crea_grezzi(righe: list[dict]) -> pd.DataFrame:
    """
    Costruisce una tabella di movimenti "grezzi", come se fosse appena stata
    letta dal file: tutte le colonne sono testo, più il numero di riga.
    Per ogni riga indichiamo solo i valori che ci interessano: gli altri
    prendono un valore corretto di base.
    """
    riga_di_base = {
        "id_movimento": "M1",
        "id_conto": "CC00000001",
        "data_operazione": "17/11/2026",
        "importo": "100,00",
        "divisa": "EUR",
        "codice_causale": "BON",
        "descrizione": "Bonifico",
    }
    righe_complete = []
    for numero, riga in enumerate(righe, start=1):
        completa = {**riga_di_base, "id_movimento": f"M{numero}", **riga}
        righe_complete.append(completa)

    grezzi = pd.DataFrame(righe_complete, dtype=str)
    grezzi.insert(0, "riga_file", range(2, len(grezzi) + 2))
    return grezzi


def crea_anagrafiche() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Due conti e due clienti di prova."""
    conti = pd.DataFrame(
        {
            "id_conto": ["CC00000001", "CC00000002"],
            "id_cliente": ["CL000001", "CL000002"],
            "codice_filiale": ["F001", "F002"],
        }
    )
    clienti = pd.DataFrame({"id_cliente": ["CL000001", "CL000002"], "segmento": ["RETAIL", "CORPORATE"]})
    return conti, clienti


def crea_cambi() -> pd.DataFrame:
    """Cambi di prova per il 17/11/2026: euro e dollaro."""
    return pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-11-17", "2026-11-17"]),
            "divisa": ["EUR", "USD"],
            "cambio": [1.0, 1.10],
        }
    )


# ----------------------------------------------------------------------------
# TEST SUL CONTROLLO DEI FORMATI
# ----------------------------------------------------------------------------


def test_importo_in_formato_italiano_viene_convertito_in_numero():
    grezzi = crea_grezzi([{"importo": "1.234,56"}, {"importo": "-12,50"}, {"importo": "1234,56"}])

    movimenti, scarti = controlla_formati(grezzi)

    assert movimenti["importo"].tolist() == [1234.56, -12.50, 1234.56]
    assert len(scarti) == 0


def test_importo_in_formato_sbagliato_viene_scartato():
    grezzi = crea_grezzi(
        [
            {"importo": "100,00"},  # corretto
            {"importo": "1234.56"},  # punto decimale invece della virgola
            {"importo": "n.d."},  # testo
            {"importo": ""},  # vuoto
            {"importo": "12,3"},  # un solo decimale
        ]
    )

    movimenti, scarti = controlla_formati(grezzi)

    assert len(movimenti) == 1
    assert scarti["motivo_scarto"].tolist() == ["IMPORTO_NON_VALIDO"] * 4
    # Le righe scartate sono proprio la terza, quarta, quinta e sesta riga del file
    assert scarti["riga_file"].tolist() == [3, 4, 5, 6]


def test_data_inesistente_o_in_formato_diverso_viene_scartata():
    grezzi = crea_grezzi(
        [
            {"data_operazione": "17/11/2026"},  # corretta
            {"data_operazione": "31/02/2026"},  # il 31 febbraio non esiste
            {"data_operazione": "2026-11-17"},  # formato diverso da gg/mm/aaaa
            {"data_operazione": ""},  # vuota
        ]
    )

    movimenti, scarti = controlla_formati(grezzi)

    assert len(movimenti) == 1
    assert movimenti["data_operazione"].iloc[0] == pd.Timestamp("2026-11-17")
    assert scarti["motivo_scarto"].tolist() == ["DATA_NON_VALIDA"] * 3


def test_codici_con_spazi_e_minuscole_vengono_ripuliti_e_non_scartati():
    grezzi = crea_grezzi([{"divisa": " eur", "codice_causale": "pos  ", "id_conto": " cc00000001 "}])

    movimenti, scarti = controlla_formati(grezzi)

    assert movimenti["divisa"].iloc[0] == "EUR"
    assert movimenti["codice_causale"].iloc[0] == "POS"
    assert movimenti["id_conto"].iloc[0] == "CC00000001"
    assert len(scarti) == 0


# ----------------------------------------------------------------------------
# TEST SUI DUPLICATI
# ----------------------------------------------------------------------------


def test_del_movimento_ripetuto_resta_solo_la_prima_riga():
    grezzi = crea_grezzi([{"id_movimento": "MA"}, {"id_movimento": "MB"}, {"id_movimento": "MA"}])
    movimenti, _ = controlla_formati(grezzi)

    senza_duplicati, scarti = togli_duplicati(movimenti)

    assert senza_duplicati["id_movimento"].tolist() == ["MA", "MB"]
    assert scarti["motivo_scarto"].tolist() == ["DUPLICATO"]
    assert scarti["riga_file"].tolist() == [4]  # la ripetizione era sulla quarta riga del file


# ----------------------------------------------------------------------------
# TEST SULLE ANAGRAFICHE
# ----------------------------------------------------------------------------


def test_il_movimento_riceve_filiale_e_segmento_del_proprio_conto():
    conti, clienti = crea_anagrafiche()
    movimenti, _ = controlla_formati(crea_grezzi([{"id_conto": "CC00000002"}]))

    arricchiti, scarti = aggiungi_anagrafiche(movimenti, conti, clienti)

    assert arricchiti["codice_filiale"].iloc[0] == "F002"
    assert arricchiti["segmento"].iloc[0] == "CORPORATE"
    assert len(scarti) == 0


def test_il_movimento_su_un_conto_inesistente_viene_scartato():
    conti, clienti = crea_anagrafiche()
    movimenti, _ = controlla_formati(crea_grezzi([{"id_conto": "CC00000001"}, {"id_conto": "CC99999999"}]))

    arricchiti, scarti = aggiungi_anagrafiche(movimenti, conti, clienti)

    assert arricchiti["id_conto"].tolist() == ["CC00000001"]
    assert scarti["motivo_scarto"].tolist() == ["CONTO_INESISTENTE"]


# ----------------------------------------------------------------------------
# TEST SULLA CONVERSIONE IN EURO
# ----------------------------------------------------------------------------


def test_la_conversione_in_euro_divide_per_il_cambio():
    movimenti, _ = controlla_formati(crea_grezzi([{"importo": "110,00", "divisa": "USD"}, {"importo": "50,00"}]))

    convertiti, scarti = converti_in_euro(movimenti, crea_cambi())

    # 110 dollari al cambio di 1,10 dollari per euro valgono 100 euro
    assert convertiti["importo_eur"].tolist() == [100.00, 50.00]
    assert len(scarti) == 0


def test_il_movimento_senza_cambio_viene_scartato():
    movimenti, _ = controlla_formati(crea_grezzi([{"divisa": "JPY"}, {"divisa": "EUR"}]))

    convertiti, scarti = converti_in_euro(movimenti, crea_cambi())

    assert convertiti["divisa"].tolist() == ["EUR"]
    assert scarti["motivo_scarto"].tolist() == ["CAMBIO_MANCANTE"]


# ----------------------------------------------------------------------------
# TEST SU FLAG E RIEPILOGO
# ----------------------------------------------------------------------------


def test_il_flag_rilevante_non_dipende_dal_segno_e_la_soglia_e_compresa():
    movimenti = pd.DataFrame({"importo_eur": [9_999.99, 10_000.00, -25_000.00]})

    segnati = segna_rilevanti(movimenti, soglia_eur=10_000)

    assert segnati["flag_rilevante"].tolist() == [False, True, True]


def test_il_riepilogo_conta_e_somma_per_filiale_e_causale():
    movimenti = pd.DataFrame(
        {
            "id_movimento": ["M1", "M2", "M3"],
            "codice_filiale": ["F001", "F001", "F002"],
            "codice_causale": ["POS", "POS", "BON"],
            "importo_eur": [-10.00, -5.50, 100.00],
        }
    )

    riepilogo = calcola_riepilogo(movimenti)

    assert len(riepilogo) == 2
    riga_pos = riepilogo[riepilogo["codice_causale"] == "POS"].iloc[0]
    assert riga_pos["numero_movimenti"] == 2
    assert riga_pos["totale_eur"] == -15.50


# ----------------------------------------------------------------------------
# TEST D'INSIEME: NESSUNA RIGA DEVE SPARIRE
# ----------------------------------------------------------------------------


def test_ogni_riga_letta_finisce_fra_le_buone_oppure_fra_gli_scarti():
    conti, clienti = crea_anagrafiche()
    grezzi = crea_grezzi(
        [
            {},  # riga corretta
            {"data_operazione": "31/02/2026"},  # data non valida
            {"importo": "abc"},  # importo non valido
            {"id_movimento": "M1"},  # duplicato della prima riga
            {"id_conto": "CC99999999"},  # conto inesistente
            {"divisa": "JPY"},  # cambio mancante
            {"importo": "220,00", "divisa": "usd "},  # corretta, con la divisa da ripulire
        ]
    )

    movimenti, scarti_formati = controlla_formati(grezzi)
    movimenti, scarti_duplicati = togli_duplicati(movimenti)
    movimenti, scarti_conti = aggiungi_anagrafiche(movimenti, conti, clienti)
    movimenti, scarti_cambi = converti_in_euro(movimenti, crea_cambi())
    scarti = componi_scarti(grezzi, [scarti_formati, scarti_duplicati, scarti_conti, scarti_cambi])

    # Quadratura: 7 righe lette = 2 buone + 5 scartate
    assert len(movimenti) == 2
    assert len(scarti) == 5
    assert len(grezzi) == len(movimenti) + len(scarti)

    # Ogni scarto ha il suo motivo, nell'ordine delle righe del file
    assert scarti["motivo_scarto"].tolist() == [
        "DATA_NON_VALIDA",
        "IMPORTO_NON_VALIDO",
        "DUPLICATO",
        "CONTO_INESISTENTE",
        "CAMBIO_MANCANTE",
    ]
    # Negli scarti ritroviamo il valore originale, scritto esattamente come era nel file
    assert scarti["importo"].iloc[1] == "abc"
