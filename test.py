import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer
from dotenv import load_dotenv
import os

load_dotenv()



# Carica il modello di lingua (specifica il percorso corretto)
model = Model(os.getenv("VOSK_MODEL_PATH"))

# Imposta il riconoscitore
recognizer = KaldiRecognizer(model, 16000)
recognizer.SetWords(True)  # Per ottenere parole singole

# Coda per gestire l'audio
q = queue.Queue()

#  Callback per acquisire l'audio in tempo reale
def callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))  # Aggiunge l'audio alla coda

# Imposta il dispositivo audio
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                       channels=1, callback=callback):
    print("Parla ora...")

    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            # Risultato finale (quando riconosce una frase completa)
            result = json.loads(recognizer.Result())
            print("🟢 Testo finale:", result["text"])
        else:
            # Risultati parziali (in tempo reale)
            partial_result = json.loads(recognizer.PartialResult())
            print("⚪ Parziale:", partial_result["partial"], end='\r')
