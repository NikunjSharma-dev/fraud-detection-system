import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Fraud Detection Ledger", layout="wide")
st.title("🛡️ Autonomous Fraud Detection & Transaction Ledger")

tab1, tab2 = st.tabs(["💳 Customer Terminal Sim", "📊 Live Admin Analytics"])

# ==========================================
# TAB 1: CUSTOMER TERMINAL
# ==========================================
with tab1:
    st.header("Simulate a Transaction")
    col1, col2 = st.columns(2)
    
    with col1:
        account_id = st.text_input("Account ID", value="ACC10294")
        amount = st.number_input("Amount (INR)", min_value=10.0, value=500.0, step=50.0)
    with col2:
        location_profile = st.selectbox(
            "Transaction Location Profile",
            ["Local (Mumbai)", "Suspicious (Delhi - velocity spike)"]
        )
        lat, lon = (19.0760, 72.8777) if "Mumbai" in location_profile else (28.6139, 77.2090)

    if st.button("Swipe Card", type="primary"):
        payload = {"account_id": account_id, "amount": amount, "lat": lat, "lon": lon}
        
        with st.spinner("Processing..."):
            response = requests.post(f"{API_URL}/transaction/submit", json=payload).json()
            
        st.session_state['current_txn'] = response.get("transaction_id")
        
        # Wait 1 second to let async ML process finish, then poll status
        time.sleep(1) 
        
    if 'current_txn' in st.session_state:
        # Check Admin API to see if ML changed the status
        ledger = requests.get(f"{API_URL}/admin/ledger-summary").json()
        current_tx = next((t for t in ledger["transactions"] if t["id"] == st.session_state['current_txn']), None)
        
        if current_tx:
            status = current_tx["status"]
            if status == "Approved":
                st.success(f"✅ Transaction Approved! ID: {current_tx['id']}")
            elif status == "Declined":
                st.error("❌ Blocked by DB Trigger rules.")
            elif status == "Awaiting Verification":
                st.warning(f"⚠️ Suspicious Activity Detected! ML Risk Score: {current_tx['risk_score']}")
                otp_input = st.text_input("Enter 6-Digit OTP (123456 to pass)", key="otp")
                if st.button("Verify Identity"):
                    if requests.patch(f"{API_URL}/transaction/{current_tx['id']}/verify", json={"otp": otp_input}).status_code == 200:
                        st.success("✅ Verified. Ledger Updated.")
                        del st.session_state['current_txn']
                    else:
                        st.error("Invalid OTP.")

# ==========================================
# TAB 2: LIVE ADMIN MONITOR
# ==========================================
with tab2:
    @st.fragment(run_every=2)
    def live_dashboard():
        try:
            data = requests.get(f"{API_URL}/admin/ledger-summary").json()
            df = pd.DataFrame(data["transactions"])
            
            m1, m2 = st.columns(2)
            m1.metric("Total Active Ledger Volume", f"₹{data['total_volume']:,.2f}")
            m2.metric("ML Anomalies Flagged today", data['fraud_count'])
                
            if not df.empty:
                fig = px.pie(df, names="status", title="Recent Transaction Status Breakdown", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Latest Live Ledger Log Entries")
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("Waiting for backend API...")

    live_dashboard()