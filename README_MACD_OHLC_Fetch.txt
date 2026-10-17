MACD CrossOver / CrossDown OHLC fetch package

Files:
- Fetch_MACD_Crossover_CrossDown_OHLC.py: fetches daily OHLC and volume for every event date from Yahoo Finance when run with internet access. Also includes previous trading-day OHLC and percentage calculations.
- MACD_Crossover_CrossDown_Event_Dates.csv: event list extracted from the two SVG timeline files.

Run:
  py -m pip install requests
  py Fetch_MACD_Crossover_CrossDown_OHLC.py

Output:
- MACD_Crossover_CrossDown_OHLC.csv
- MACD_OHLC_Fetch_Errors.csv

Notes:
- Historical price data is fetched from Yahoo Finance at runtime; it is not embedded in this package. Internet access is required.
- The script tries SYMBOL.NS and then SYMBOL.BO by default. Use TICKER_OVERRIDES for special ticker formats.
- If a signal date is not a trading session or Yahoo has no bar for that date, the row is marked MISSING_SIGNAL_DATE_BAR.
- Dates are read from the SVG axis and assigned year 2026, matching the provided timeline context.
