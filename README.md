# VBA Control with Voice Commands

This script allows controlling the **VisualBoyAdvance** emulator using voice commands. It uses **speech_recognition** for voice recognition and **pydirectinput** to send input to the emulator window.

## Requirements

Make sure you have the following Python libraries installed:

```bash
pip install speechrecognition pygetwindow pydirectinput
```

Additionally, **VisualBoyAdvance** must be open to enable recognition and interaction with the window.

## Features

- **Voice Control**: Allows sending voice commands to VBA.
- **Error Correction**: Uses Levenshtein distance to correct misrecognized words.
- **Turbo Mode**: Enables automatic repetition of a command until stopped.

## Voice Commands

The script recognizes the following voice commands:

| Command | Corresponding Key |
|---------|------------------|
| left | ← |
| right | → |
| up | ↑ |
| down | ↓ |
| confirm | Z |
| back | X |
| start | Enter |
| select | Backspace |
| turbo [command] | Activates turbo mode |
| stop | Deactivates turbo mode |

## Usage

1. **Start VisualBoyAdvance.**
2. **Run the script:**
   ```bash
   python script.py
   ```
3. **Select the microphone** when prompted.
4. **Speak the commands** to control the emulator.

## Turbo Mode

Turbo mode allows continuously repeating a command without needing to say it multiple times. To activate:

- Say **"turbo"** followed by a valid command (e.g., "turbo left").
- To deactivate turbo mode, say **"stop"**.

## Code Structure

- **Voice Recognition**: Uses `speech_recognition` to capture and process voice input.
- **Command Handling**:
  - Uses Levenshtein distance to correct recognition errors.
  - Extracts commands from the spoken phrase.
- **VBA Interaction**: Finds the VBA window and brings it to the foreground.
- **Command Execution**: Inserts voice commands into a queue and executes them in a separate thread.

## Notes

- Voice recognition may not always be precise, especially in noisy environments.
- Ensure VisualBoyAdvance is focused to receive input.
- If the script cannot find VBA, verify that the window is named **"VisualBoyAdvance"**.

## Contributions

If you have suggestions or improvements, feel free to open a pull request or report an issue!