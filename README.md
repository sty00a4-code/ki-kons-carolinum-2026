# KI-Kons-Carolinum-2026

Kl-gestützte Analyse und Visualisierung klinischer Lernverläufe in zahnmedizinischen Behandlungskursen -Pilotprojekt zur longitudinalen Begleitung der Kompetenzentwicklung

## Setup

### Prerequisites

- Python 3.8+

### Installation

1. Clone the repository:

```bash
git clone https://github.com/sty00a4-code/ki-kons-carolinum-2026.git
cd ki-kons-carolinum-2026
```

2. Create a virtual environment:

```bash
python3 -m venv venv
```

3. Activate the virtual environment:

```bash
source venv/bin/activate # Linux/Mac
venv\Scripts\activate    # Windows
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

To deactivate the environment:

```bash
deactivate
```

## Run the local website

This project can be served locally as a small web dashboard for the performance data. The app is written in Python and can be run with Streamlit.

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   pip install streamlit
   ```
   For a reproducible setup, you can also add Streamlit to requirements.txt so future installations only need:

3. Start the local server:
   ```bash
   streamlit run projekt2/app.py
   ```
   If your app script has a different name or location, replace the path accordingly.

4. Open the dashboard:
   ```
   Local URL: http://localhost:8501
   ```
   Open this URL in your browser to view the dashboard.

5. Stop the server: Press Ctrl+C in the terminal to stop the local web server.

### Notes

- The dashboard expects the SQLite database file to be available in the project folder.
- If you rename the app entry script, update the command in step 3.
