@echo off
REM ============================================================================
REM  LANCIO DEL FLUSSO ETL DA UNO SCHEDULATORE (Windows)
REM ============================================================================
REM  Lo "schedulatore" e' il programma che avvia i flussi a orari prestabiliti:
REM  l'Utilita' di pianificazione di Windows oppure lo schedulatore aziendale.
REM  Uno schedulatore non conosce Python: sa solo lanciare un comando, passargli
REM  dei parametri e leggere il codice di uscita con cui il comando termina.
REM  Questo file fa da ponte fra lo schedulatore e il nostro flusso.
REM
REM  Uso:
REM      esegui_etl.bat 2026-11-17
REM
REM  Che cosa fa:
REM      1. si sposta nella cartella del progetto, da qualunque cartella parta
REM      2. esegue il flusso DENTRO l'ambiente conda "etl_demo"
REM      3. restituisce allo schedulatore il codice di uscita del flusso:
REM             0 = tutto bene      1 = flusso fermato      2 = errore
REM
REM  Perche' serve l'ambiente conda: l'ambiente non contiene solo python.exe, ma
REM  anche le librerie di sistema (file .dll) di cui i pacchetti hanno bisogno.
REM  Eseguire il comando dentro l'ambiente garantisce che vengano trovate.
REM
REM  NOTA: questo file non contiene lettere accentate di proposito, perche' il
REM  Prompt dei comandi di Windows non usa la codifica UTF-8.
REM ============================================================================

setlocal

REM ----------------------------------------------------------------------------
REM  DA ADATTARE ALLA PROPRIA INSTALLAZIONE
REM  Percorso del comando conda. Con Miniconda installato per il solo utente e':
REM      %USERPROFILE%\miniconda3\condabin\conda.bat
REM  Con Miniforge e':
REM      %USERPROFILE%\miniforge3\condabin\conda.bat
REM  Usiamo il percorso completo perche' uno schedulatore, di norma, non eredita
REM  le impostazioni del terminale da cui lavoriamo ogni giorno.
REM ----------------------------------------------------------------------------
set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
set "AMBIENTE=etl_demo"

REM La data di elaborazione e' il primo parametro ed e' obbligatoria:
REM la decide lo schedulatore, non il flusso.
if "%~1"=="" (
    echo Uso: esegui_etl.bat AAAA-MM-GG
    exit /b 2
)

if not exist "%CONDA_BAT%" (
    echo Comando conda non trovato: "%CONDA_BAT%"
    echo Correggere la variabile CONDA_BAT all'inizio di questo file.
    exit /b 2
)

REM %~dp0 e' la cartella in cui si trova questo file (la cartella schedulazione).
REM Con ".." saliamo di un livello e arriviamo alla cartella del progetto.
cd /d "%~dp0.."

REM "conda run -n etl_demo" esegue il comando che segue dentro l'ambiente,
REM senza bisogno di attivarlo prima. L'opzione --no-capture-output fa comparire
REM i messaggi del flusso man mano che vengono scritti.
REM "call" e' necessario perche' in Windows conda e' a sua volta un file .bat.
call "%CONDA_BAT%" run -n %AMBIENTE% --no-capture-output python esegui_etl.py --data %~1

REM ERRORLEVEL contiene il codice di uscita dell'ultimo comando eseguito
set "CODICE_USCITA=%ERRORLEVEL%"
echo Flusso terminato con codice di uscita %CODICE_USCITA%

exit /b %CODICE_USCITA%
