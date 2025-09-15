import streamlit as st
import requests
import pandas as pd
import tempfile

API_BASE = "https://namaste-ipab.onrender.com/"

st.title("🧩 NAMASTE ↔ ICD-11 Integration Demo")

# ---- NAMASTE Ingest ----
st.subheader("📥 Ingest NAMASTE CSV")
uploaded = st.file_uploader("Upload NAMASTE CSV (code,term)", type=["csv"])
if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name
    r = requests.post(f"{API_BASE}/ingest/namaste", params={"file_path": tmp_path})
    st.json(r.json())

# ---- ICD-11 Sync ----
st.subheader("🌍 Sync ICD-11 Codes")
if st.button("Sync ICD-11 from WHO API"):
    r = requests.post(f"{API_BASE}/sync/icd11")
    st.json(r.json())

# ---- Autocomplete ----
st.subheader("🔍 Autocomplete")
q = st.text_input("Search for a condition (in NAMASTE or ICD-11)")

if st.button("Search"):
    r = requests.get(f"{API_BASE}/autocomplete", params={"q": q})
    if r.ok:
        results = r.json()

        with st.expander("📋 Autocomplete Results", expanded=True):
            if not results:
                st.warning("No matches found.")
            else:
                for item in results:
                    st.markdown(f"- **{item['code']}**: {item['term']}")
    else:
        st.error(f"Error {r.status_code}: {r.text}")


# ---- Mapping ----

st.subheader("🔗 Semantic Mapping")
namaste_code = st.text_input("Enter a NAMASTE code")

if st.button("Map Codes"):
    # 1) Call your FastAPI
    payload = {"namaste_code": namaste_code.strip() or None}
    r = requests.post(f"{API_BASE}/map", json=payload)
    if not r.ok:
        st.error(f"Error {r.status_code}: {r.text}")
    else:
        data = r.json()
        # 2) Build a DataFrame
        df = pd.DataFrame(data["mappings"])
        df = df.rename(columns={
            "icd_code": "ICD-11 Code",
            "explanation": "Explanation"
        })

        # 3) Show in a modal or expander
        container = None
        try:
            container = st.modal("🗂 Mapping Results")
        except AttributeError:
            container = st.expander("🗂 Mapping Results")

        with container:
            st.markdown(f"**Source Text:**  {data['query']}")
            st.table(df)

            st.markdown("**Evidence URLs:**")
            for url in data["evidence"]:
                code = url.split("#")[-1]
                st.markdown(f"- [{code}]({url})")



# ---- Audit Logs ----
st.subheader("📜 Audit Logs")
if st.button("Show Audit Logs"):
    r = requests.get(f"{API_BASE}/audit")
    df = pd.DataFrame(r.json())
    st.dataframe(df)
