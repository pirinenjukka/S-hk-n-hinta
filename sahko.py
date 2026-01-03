"""Sähkömonitori

Simple Streamlit app that fetches hourly electricity prices from the
`porssisahko` API and displays today's price chart and the current price.

Run with:
    streamlit run sahko.py

Dependencies: `streamlit`, `pandas`, `requests`
"""

import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Sähkömonitori", page_icon="⚡")
st.title("⚡ Pörssisähkön hinta")

url = "https://api.porssisahko.net/v1/latest-prices.json"

try:
    # 1. Request data from API
    response = requests.get(url)
    response.raise_for_status()
    json_data = response.json()
    
    df = pd.DataFrame(json_data['prices'])

    # 2. Type and convert timezones
    df['startDate'] = pd.to_datetime(df['startDate'])
    df['endDate'] = pd.to_datetime(df['endDate'])
    df['startDate'] = df['startDate'].dt.tz_convert('Europe/Helsinki')
    df['endDate'] = df['endDate'].dt.tz_convert('Europe/Helsinki')

    # 3. Filter today's data
    now = datetime.now(ZoneInfo("Europe/Helsinki"))
    today_str = now.strftime('%Y-%m-%d')
    
    df_today = df[df['startDate'].dt.strftime('%Y-%m-%d') == today_str].copy()
    df_today = df_today.sort_values('startDate')
    
    # Create a time-only column for the x-axis
    df_today['Klo'] = df_today['startDate'].dt.strftime('%H:%M')

    # --- NEW LOGIC FOR COLORING ---
    # Create a new column 'Status' with default 'Other time'
    df_today['Status'] = 'Muu aika'

    # Find the row where the current time falls in the interval and set its status to 'NOW'
    # .loc is Pandas' way to select and modify rows based on conditions
    mask_current = (df_today['startDate'] <= now) & (df_today['endDate'] > now)
    df_today.loc[mask_current, 'Status'] = 'NYT'
    # ----------------------------------

    # Show current price (same logic as before, but easier with Pandas)
    if mask_current.any():
        current_row = df_today.loc[mask_current].iloc[0]
        st.metric(
            label=f"Hinta nyt (klo {current_row['Klo']})", 
            value=f"{current_row['price']} snt/kWh"
        )
    else:
        st.warning("Hinta-tietoa tälle hetkelle ei löytynyt.")

    # 4. VISUALIZATION
    st.subheader(f"Hintakehitys tänään")
    
    # Add color parameter. Streamlit will automatically choose different colors for each status.
    st.bar_chart(
        df_today, 
        x="Klo", 
        y="price", 
        color="Status" # <--- This is the magic word
    )

    if st.button('Päivitä'):
        st.rerun()

except Exception as e:
    st.error(f"Virhe: {e}")