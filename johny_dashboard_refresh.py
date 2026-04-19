# ===== AUTO-REFRESH HELPER =====
# Johnny Dashboard'ın tüm sayfalarında 15 saniye refresh

import streamlit as st
import time

def setup_auto_refresh(interval_seconds=15):
    """
    Streamlit dashboard'ta auto-refresh kurulumu
    
    Kullanım:
    setup_auto_refresh(15)  # 15 saniyede bir yenile
    """
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = time.time()
    
    # Refresh kontrol
    placeholder = st.empty()
    
    while True:
        current_time = time.time()
        elapsed = current_time - st.session_state.last_refresh_time
        
        if elapsed > interval_seconds:
            st.session_state.last_refresh_time = current_time
            st.rerun()
        
        # Countdown göster
        remaining = int(interval_seconds - elapsed)
        with placeholder.container():
            st.caption(f"🔄 Sonraki yenileme: {remaining}s")
        
        time.sleep(1)

# Her sayfada başında çağır:
# from johny_dashboard_refresh import setup_auto_refresh
# setup_auto_refresh(15)
