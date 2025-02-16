import speech_recognition as sr
import pygetwindow as gw
import pydirectinput
import time
import queue
import threading
import re

# Configurazione di speech_recognition
r = sr.Recognizer()
#r.pause_threshold = 0.4
#r.non_speaking_duration = 0.4
r.dynamic_energy_threshold = False

# Elenca i microfoni disponibili
mic_names = sr.Microphone.list_microphone_names()
print("Microfoni disponibili:")
for index, name in enumerate(mic_names):
    print(f"{index}: {name}")

# Chiede all'utente di selezionare un microfono
mic_index = int(input("Scegli il numero del microfono che vuoi utilizzare: "))
print("Microfono selezionato:", mic_names[mic_index])

# Dizionario comandi voce → tasto da premere
vocal_commands = {
    "sinistra": "left",
    "destra": "right",
    "su": "up",
    "giù": "down",
    "conferma": "z",
    "indietro": "x",
    "inizia": "enter",
    "seleziona": "backspace"
}

def sort_vocal_commands(vocal_commands):
    new_vocal_commands = {}
    for k in sorted(vocal_commands, key=len, reverse=True):
        new_vocal_commands[k] = vocal_commands[k]
    return new_vocal_commands

vocal_commands = sort_vocal_commands(vocal_commands)

def get_vba_window():
    """Trova la finestra di VisualBoyAdvance e la porta in primo piano."""
    windows = gw.getWindowsWithTitle("VisualBoyAdvance")
    print(windows)
    if windows:
        vba_window = windows[0]
        vba_window.minimize()
        vba_window.restore()
        vba_window.activate()  # Porta la finestra in primo piano
        print("Finestra di VisualBoyAdvance trovata!")
        return True
    else:
        print("Errore: VisualBoyAdvance non trovato.")
        return False

def levenshtein_distance(s1, s2):
    """
    Calcola la distanza di Levenshtein tra s1 e s2.
    Rappresenta il numero minimo di modifiche (inserimenti, cancellazioni, sostituzioni)
    per trasformare s1 in s2.
    """
    if s1 == s2:
        return 0
    len_s1, len_s2 = len(s1), len(s2)
    dp = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]
    for i in range(len_s1 + 1):
        dp[i][0] = i
    for j in range(len_s2 + 1):
        dp[0][j] = j
    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Cancellazione
                dp[i][j - 1] + 1,       # Inserimento
                dp[i - 1][j - 1] + cost # Sostituzione
            )
    return dp[len_s1][len_s2]

def correct_words_with_levenshtein(command, known_keys, max_distance=2):
    """
    Suddivide la frase riconosciuta in parole e per ciascuna:
    - Trova la parola più vicina tra 'known_keys' se la distanza di Levenshtein ≤ max_distance.
    - Sostituisce la parola con quella corretta se possibile.
    Ritorna la frase riassemblata.
    """
    words = command.split()
    corrected_words = []
    for w in words:
        best_match = w
        best_dist = float('inf')
        for k in known_keys:
            dist = levenshtein_distance(w, k)
            if dist < best_dist:
                best_dist = dist
                best_match = k
        corrected_words.append(best_match if best_dist <= max_distance else w)
    return " ".join(corrected_words)

def extract_commands(corrected_phrase, commands_dict):
    """
    Estrae tutti i comandi presenti nella frase corrected_phrase utilizzando regex.
    Costruisce un pattern che cerca tutte le parole chiave (con boundary \b per evitare match parziali)
    e restituisce una lista di occorrenze in ordine di apparizione, inclusi duplicati.
    """
    # Costruisce il pattern regex con le chiavi, ad esempio: r'\b(?:sinistra|destra|su|giù|conferma|indietro|inizia|seleziona)\b'
    pattern = r'\b(?:' + '|'.join(map(re.escape, commands_dict.keys())) + r')\b'
    matches = re.findall(pattern, corrected_phrase)
    return matches

# Verifica se VisualBoyAdvance è aperto
if not get_vba_window():
    exit()

# Stato della modalità turbo
turbo_mode = False
turbo_command = None

# Creazione della coda per i comandi
command_queue = queue.Queue()

def command_executor():
    """Thread che esegue i comandi presenti nella coda."""
    while True:
        cmd = command_queue.get()
        if cmd is None:
            break  # Terminazione del thread se riceve None
        pydirectinput.press(cmd)
        command_queue.task_done()

# Avvio del thread esecutore
executor_thread = threading.Thread(target=command_executor, daemon=True)
executor_thread.start()

with sr.Microphone(device_index=mic_index) as source:
    print("Microfono pronto!")
    while True:
        # Se la modalità turbo è attiva, inserisci il comando nella coda
        if turbo_mode and turbo_command:
            command_queue.put(turbo_command)

        try:
            audio = r.listen(source, timeout=0.5)
            recognized = r.recognize_google(audio, language='it-IT').lower()
            print(f"Hai detto: '{recognized}'")

            # Chain of responsibility: correggi la frase e poi cerca i comandi come sottostringhe
            corrected_phrase = correct_words_with_levenshtein(
                recognized,
                list(vocal_commands.keys()) + ["turbo", "stop", "giù", "su"],
                max_distance=2
            )
            print(f"Fase di correzione → frase risultante: '{corrected_phrase}'")

            # Se la frase contiene "stop", disattiva la modalità turbo
            if "stop" in corrected_phrase:
                turbo_mode = False
                turbo_command = None
                print("Turbo disattivato.")
                continue

            # Se la frase contiene "turbo", cerca il comando da attivare in modalità turbo
            if "turbo" in corrected_phrase:
                # Per il comando turbo cerchiamo solo il PRIMO comando riconosciuto dopo "turbo"
                raw_turbo_cmd = extract_commands(corrected_phrase.replace("turbo", ""), vocal_commands)
                if raw_turbo_cmd:
                    raw_turbo_cmd = raw_turbo_cmd[0]
                    if turbo_mode and turbo_command is not None:
                        print(f"Aggiorno turbo da '{turbo_command}' a '{vocal_commands[raw_turbo_cmd]}'")
                    else:
                        print(f"Turbo attivato per il comando: '{raw_turbo_cmd}' → '{vocal_commands[raw_turbo_cmd]}'")
                    turbo_command = vocal_commands[raw_turbo_cmd]
                    turbo_mode = True
                    continue
                else:
                    print("Hai detto 'turbo', ma non ho trovato un comando valido nella frase.")
                    continue

            # Altrimenti, estrai tutti i comandi riconosciuti e inseriscili in coda
            cmds = extract_commands(corrected_phrase, vocal_commands)
            if cmds:
                for cmd in cmds:
                    normal_cmd = vocal_commands[cmd]
                    print(f"Eseguo comando singolo: '{cmd}' → '{normal_cmd}'")
                    command_queue.put(normal_cmd)
            else:
                print("Nessun comando riconosciuto nella frase.")

        except sr.WaitTimeoutError:
            pass  # Nessuna voce rilevata entro il timeout
        except sr.UnknownValueError:
            print("Non ho capito il comando...")
        except sr.RequestError as e:
            print(f"Errore nella richiesta dei risultati: {e}")
