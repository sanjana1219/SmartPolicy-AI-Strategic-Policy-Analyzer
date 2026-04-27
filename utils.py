import fitz
import streamlit as st
import os
from google import genai

# 1. SETUP 
API_KEY = "Your Api key here"

def get_client():
    if not API_KEY or "PASTE_YOUR" in API_KEY:
        st.error("🔑 API Key is missing!")
        st.stop()
    return genai.Client(api_key=API_KEY)

# 2. AUTOMATIC MODEL DISCOVERY 
def get_working_model():
    client = get_client()
    try:
        models = client.models.list()

        # Always pick the FIRST valid model
        for m in models:
            if "flash" in m.name.lower():
                return m.name

        # fallback
        return models[0].name

    except Exception as e:
        st.error(f"Model discovery failed: {e}")
        return "models/gemini-1.5-flash"

def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_file.seek(0)
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return " ".join(text.split())

def generate_summary(text):
    client = get_client()
    working_model = get_working_model()
    
    st.info(f"Using model: {working_model}") 
    
    prompt = f"Summarize these policy pillars: {text[:8000]}"
    try:
        response = client.models.generate_content(model=working_model, contents=prompt)
        return response.text
    except Exception as e:
        return f"❌ AI Analysis Error: {str(e)}"

def generate_scenario_draft(summary, label, logic):
    client = get_client()
    working_model = get_working_model()
    prompt = f"Policy: {summary}\nScenario: {label}\nGoal: {logic}\nRewrite professionally."
    try:
        response = client.models.generate_content(model=working_model, contents=prompt)
        return response.text
    except Exception as e:
        return f"❌ Scenario Error: {str(e)}"
