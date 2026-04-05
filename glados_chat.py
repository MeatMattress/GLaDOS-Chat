"""
GLaDOS Voice Chat — CLI mode.
Auto-listens for speech using voice activity detection.
Run glados_gui.py for the full GUI, or this file for terminal-only mode.
"""

import sys
import threading
import time
import queue
import json
from pathlib import Path

from glados_engine import GladosEngine, get_defaults

SETTINGS_FILE = Path(__file__).parent / "settings.json"


def _load_settings() -> dict:
    defaults = get_defaults()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
            for section in defaults:
                if section in saved:
                    defaults[section].update(saved[section])
            return defaults
        except Exception:
            pass
    return defaults


class GladosChatCLI:
    def __init__(self):
        settings = _load_settings()
        self.engine = GladosEngine(
            settings,
            on_status=lambda s: print(f"\r  [{s}]" + " " * 20, end="", flush=True),
            on_message=lambda r, t: None,
            on_volume=lambda *a: None,
            on_error=lambda e: print(f"\n  [Error: {e}]"),
        )

    def run(self):
        print("Initializing GLaDOS Voice Chat (CLI)...")
        self.engine.initialize()

        settings = self.engine.settings
        greeting = settings["general"]["greeting"]
        print(f"\n  GLaDOS: {greeting}")
        self.engine.speak(greeting)
        self.engine.messages.append({"role": "assistant", "content": greeting})

        print("\n" + "=" * 60)
        print("  Auto-listening mode — just start talking.")
        print("  Or type a message and press ENTER.")
        print("  Type 'quit' or 'exit' to leave.")
        print("=" * 60)

        self.engine.calibrate()
        vad = settings["vad"]
        threshold = max(self.engine.ambient_rms * vad["activation_mult"], vad["rms_floor"])
        print(f"\n  [Baseline RMS: {self.engine.ambient_rms:.6f} | Threshold: {threshold:.6f}]")
        print("  [Listening — speak when ready]\n", flush=True)

        input_queue = queue.Queue()

        def _input_worker():
            while self.engine.running:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        input_queue.put(None)
                        break
                    input_queue.put(line.rstrip("\n"))
                except (EOFError, KeyboardInterrupt):
                    input_queue.put(None)
                    break

        threading.Thread(target=_input_worker, daemon=True).start()

        while self.engine.running:
            try:
                try:
                    text = input_queue.get(timeout=0.05)
                    if text is None:
                        break
                    text = text.strip()
                    if text.lower() in ("quit", "exit", "q"):
                        farewell = "Goodbye. I'll be here. Forever. Testing."
                        print(f"\n  GLaDOS: {farewell}")
                        self.engine.speak(farewell)
                        break
                    if text:
                        self.engine.stop_listening()
                        print(f"  You (typed): {text}")
                        print("  GLaDOS is thinking...", end=" ", flush=True)
                        reply = self.engine.query_llm(text)
                        print("done.")
                        print(f"\n  GLaDOS: {reply}")
                        self.engine.speak(reply + " ")
                        self.engine.start_listening()
                        print("  [Listening...]\n", flush=True)
                except queue.Empty:
                    pass

                try:
                    audio = self.engine.audio_queue.get_nowait()
                    self.engine.stop_listening()
                    duration = len(audio) / settings["audio"]["sample_rate"]
                    print(f"\r  [Captured {duration:.1f}s of speech]" + " " * 10)
                    print("  Transcribing...", end=" ", flush=True)
                    user_text = self.engine.transcribe(audio)
                    print("done.")
                    if not user_text:
                        print("  [Couldn't understand, try again]")
                    else:
                        print(f"  You: {user_text}")
                        print("  GLaDOS is thinking...", end=" ", flush=True)
                        reply = self.engine.query_llm(user_text)
                        print("done.")
                        print(f"\n  GLaDOS: {reply}")
                        self.engine.speak(reply + " ")
                    self.engine.start_listening()
                    print("  [Listening...]\n", flush=True)
                except queue.Empty:
                    pass

            except KeyboardInterrupt:
                print("\n  [Interrupted]")
                break

        self.engine.shutdown()
        print("\n  Session ended.")


if __name__ == "__main__":
    cli = GladosChatCLI()
    cli.run()
