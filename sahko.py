import requests
import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Sähkömonitori", page_icon="⚡")
st.title("⚡ Pörssisähkön hinta")

url = "https://api.porssisahko.net/v1/latest-prices.json"

try:
    # 1. Haetaan data
    response = requests.get(url)
    response.raise_for_status()
    json_data = response.json()
    
    df = pd.DataFrame(json_data['prices'])

    # 2. Tyypitetään ja käännetään aikavyöhykkeet
    df['startDate'] = pd.to_datetime(df['startDate'])
    df['endDate'] = pd.to_datetime(df['endDate'])
    df['startDate'] = df['startDate'].dt.tz_convert('Europe/Helsinki')
    df['endDate'] = df['endDate'].dt.tz_convert('Europe/Helsinki')

    # 3. Suodatetaan tämä päivä
    now = datetime.now(ZoneInfo("Europe/Helsinki"))
    today_str = now.strftime('%Y-%m-%d')
    
    df_today = df[df['startDate'].dt.strftime('%Y-%m-%d') == today_str].copy()
    df_today = df_today.sort_values('startDate')
    
    # Tehdään x-akselia varten pelkkä kellonaika-sarake
    df_today['Klo'] = df_today['startDate'].dt.strftime('%H:%M')

    # --- UUSI LOGIIKKA VÄRJÄYKSELLE ---
    # Luodaan uusi sarake 'Status', jonka oletusarvo on "Muu aika"
    df_today['Status'] = 'Muu aika'

    # Etsitään rivi, jossa nykyhetki osuu väliin, ja muutetaan sen statukseksi "NYT"
    # .loc on Pandasin tapa valita ja muokata tiettyjä rivejä ehtojen perusteella
    mask_current = (df_today['startDate'] <= now) & (df_today['endDate'] > now)
    df_today.loc[mask_current, 'Status'] = 'NYT'
    # ----------------------------------

    # Näytetään nykyinen hinta (sama logiikka kuin aiemmin, mutta nyt Pandasin avulla helpommin)
    if mask_current.any():
        current_row = df_today.loc[mask_current].iloc[0]
        st.metric(
            label=f"Hinta nyt (klo {current_row['Klo']})", 
            value=f"{current_row['price']} snt/kWh"
        )
    else:
        st.warning("Hinta-tietoa tälle hetkelle ei löytynyt.")

    # 4. VISUALISOINTI
    st.subheader(f"Hintakehitys tänään")
    
    # Lisätään color-parametri. Streamlit valitsee automaattisesti eri värit eri statuksille.
    st.bar_chart(
        df_today, 
        x="Klo", 
        y="price", 
        color="Status" # <--- Tämä on se taikasana
    )

    if st.button('Päivitä'):
        st.rerun()

except Exception as e:
    st.error(f"Virhe: {e}")