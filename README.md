# ☁️ Nimbus

### *“Meteorologically precise. Soulfully present.”*

Nimbus is a beautiful, pastel-themed Textual TUI weather application for monitoring **West Des Moines, Iowa** (lat 41.5401, lon -93.6271). It combines real-time data from the National Weather Service with the unique personalities of two AI companions: **Zahra** and **Morg**.

---

## ✨ Features

- **📍 Local Precision:** Real-time monitoring using the free NWS API. No API keys required.
- **🛡️ Alert System:** Automatic polling for Tornado and Severe Thunderstorm warnings with a full UI palette shift and desktop notifications.
- **☁️ Soulful Sky:** A dynamic center canvas featuring ASCII/Unicode weather art that shifts with time of day and current conditions.
- **🌸 Zahra:** A shy, sweet AI companion who reacts emotionally to the weather. She maintains a persistent state, mood, and memory of your interactions.
- **⚡ Morg:** An ancient goblin familiar who provides terse, Socratic, third-person technical commentary on the atmospheric data.
- **🎨 Pastel Mandate:** A carefully crafted TUI aesthetic using soft navies, lavenders, and amber accents.

---

## 🛠️ Architecture

Nimbus is built with:
- **[Textual](https://textual.textualize.io/):** For the terminal user interface.
- **[Ollama](https://ollama.com/):** Powering the personality engine locally (recommended: `gemma3:12b`).
- **[httpx](https://www.python-httpx.org/):** For asynchronous API calls to the NWS.
- **[Pydantic](https://docs.pydantic.dev/):** For robust weather data modeling.

---

## 🚀 Getting Started

### Prerequisites
1. **Python 3.12+**
2. **Ollama:** Running locally with the `gemma3:12b` model.
3. **Reference Repos:** Nimbus requires the `morg` and `zahra` repositories to be available in a sibling directory for their personality modules.

### Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd nimbus
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or use your shell's equivalent
   pip install -e .
   ```

3. Run the application:
   - **Bash:** `./run.sh`
   - **Nushell:** `./run.nu`

---

## ⌨️ Bindings

- `Ctrl + R`: Force refresh weather data.
- `Ctrl + T`: Simulate a Tornado Warning (for testing alert states).
- `Q`: Safe quit with a goodbye from Zahra.

---

## 📜 The Morg/Zahra Dynamic

Zahra provides emotional safety and tenderness, while Morg provides precision and accountability. They are aware of each other, though Morg will absolutely deny he cares about Zahra's happiness.

*Both are watching. Both care deeply. Morg remembers all of them fondly. Morg will not say this.*

---

<div align="center">
  🐾🌸🎀🍓☁️
</div>
