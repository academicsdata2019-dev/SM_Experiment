BACKTEST TOP GAINERS — STREAMLIT APP
====================================

WINDOWS SETUP
1. Install Python 3.11 or newer from https://www.python.org/downloads/
   During installation, tick "Add Python to PATH".
2. Extract this folder somewhere easy, such as Desktop.
3. Put "Backtest Top Gainers.csv" in the same folder as app.py.
   Alternatively, run the app and upload the CSV using the sidebar.
4. Open Command Prompt in this folder:
   - Open the folder in File Explorer.
   - Click the address bar, type cmd, and press Enter.
5. Run:
   py -m pip install -r requirements.txt
6. Start the dashboard:
   py -m streamlit run app.py
7. Your browser should open automatically. If not, copy the Local URL shown in Command Prompt
   (usually http://localhost:8501) into Chrome.

IF 'py' IS NOT RECOGNIZED
Try:
   python -m pip install -r requirements.txt
   python -m streamlit run app.py

NOTES
- This app is a Streamlit web dashboard, not a Jupyter notebook.
- It reads the CSV and displays record counts, recurring stocks, sectors, market-cap mix, and quality checks.
- It does not prove profitability. A true trading backtest needs historical price data, entry/exit rules, and transaction costs.
