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
    resp = requests.get(f"{API_BASE}/autocomplete", params={"q": q})
    if not resp.ok:
        st.error(f"Error {resp.status_code}: {resp.text}")
    else:
        data = resp.json()
        
        with st.expander("📋 Autocomplete Results", expanded=True):
            namaste_list = data.get("namaste", [])
            icd_list     = data.get("icd11", [])

            # NAMASTE suggestions
            if namaste_list:
                df_namaste = pd.DataFrame(namaste_list).rename(
                    columns={"code": "Code", "term": "Term"}
                )
                st.markdown("**NAMASTE Suggestions**")
                st.table(df_namaste)

            # ICD-11 suggestions
            if icd_list:
                df_icd = pd.DataFrame(icd_list).rename(
                    columns={"code": "ICD-11 Code", "title": "Title"}
                )
                st.markdown("**ICD-11 Suggestions**")
                st.table(df_icd)

            # No results case
            if not namaste_list and not icd_list:
                st.info("No suggestions found.")

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
