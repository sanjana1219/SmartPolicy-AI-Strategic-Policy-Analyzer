import fitz  # PyMuPDF 
import streamlit as st
import os
from google import genai
from utils import get_client, get_working_model, extract_text_from_pdf, generate_summary, generate_scenario_draft
import re

# PAGE CONFIG 
st.set_page_config(page_title="SmartPolicy AI Dashboard", layout="wide")

# CSS STYLING 
st.markdown("""
<style>

/* GLOBAL BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #0F1C2E, #16283D);
}

/*  SIDEBAR  */
[data-testid="stSidebar"] {
    background-color: #0B1624;
    padding-top: 20px;
}

[data-testid="stSidebar"] h1 {
    color: #3B82F6 !important;
    font-weight: 800;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown {
    color: #CBD5E1 !important;
}

/* Upload box */
section[data-testid="stFileUploader"] {
    background-color: #111F33;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #1E3A5F;
}

/* Sidebar button */
[data-testid="stSidebar"] .stButton > button {
    background-color: #1E293B !important;
    color: #E2E8F0 !important;
    border-radius: 8px !important;
    border: 1px solid #334155 !important;
    font-weight: 600 !important;
    width: 100%;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #243447 !important;
}

/*  MAIN TITLE  */
h1 {
    color: #E2E8F0 !important;
    font-weight: 800 !important;
}

/*  SECTION TITLES  */
h2, h3 {
    color: #93C5FD !important;
    font-weight: 700 !important;
}

/*  BODY / GENERATED TEXT */
.stMarkdown, .stText, p, span, div {
    color: #CBD5E1 !important;
}

/*  METADATA CARDS */
.metadata-card {
    background-color: #1E3A5F;
    padding: 30px;
    border-radius: 18px;
    border-bottom: 4px solid #3B82F6;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.35);
    text-align: center;
    margin-bottom: 20px;
}

.card-label {
    color: #93C5FD !important;
    font-size: 0.8rem !important;
    font-weight: 900 !important;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.card-value {
    color: #FFFFFF !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    margin-top: 12px;
}

/* MAIN BUTTONS  */
div.stButton > button {
    background-color: #3B82F6;
    color: white;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 600;
    border: none;
}

div.stButton > button:hover {
    background-color: #2563EB;
    color: white;
}

</style>
""", unsafe_allow_html=True)


# SIDEBAR 
with st.sidebar:
    st.title("🛡️ SmartPolicy AI")
    uploaded_file = st.file_uploader("Upload Policy PDF", type="pdf")
    
    if st.button("🔄 Reset System"):
        st.session_state.clear()
        st.rerun()

#  MAIN DASHBOARD 
st.title("💡 SmartPolicy AI: Strategic Analyzer")

# HELPER FUNCTION 
def extract_policy_year(text):
    # Correct regex to capture full year
    years = re.findall(r'\b(?:19|20)\d{2}\b', text)
    if years:
        years = list(map(int, years))
        return f"{min(years)} - {max(years)}" if len(years) > 1 else f"{years[0]}"
    return "Unknown"

# DISPLAY METADATA CARDS 
col_a, col_b = st.columns(2)
with col_a:
    fname = uploaded_file.name if uploaded_file else "No File Uploaded"
    st.markdown(f"""
    <div class='metadata-card'>
        <div class='card-label'>📄 Document Identity</div>
        <div class='card-value'>{fname}</div>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    if uploaded_file:
        raw_text = extract_text_from_pdf(uploaded_file)
        policy_year = extract_policy_year(raw_text)
    else:
        raw_text = ""
        policy_year = "2024 - 2030 (Projected)"
    st.markdown(f"""
    <div class='metadata-card'>
        <div class='card-label'>⏳ Time Horizon</div>
        <div class='card-value'>{policy_year}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# MAIN FUNCTIONALITY 
if uploaded_file:

    col1, col2 = st.columns(2)

    # POLICY SUMMARY 
    with col1:
        st.subheader("1. Policy Summarisation")
        if "summary" not in st.session_state:
            with st.spinner("Analyzing..."):
                st.session_state.summary = generate_summary(raw_text)
        if "summary" in st.session_state:
            st.markdown(st.session_state.summary)

    # SCENARIO ADAPTATION + CHATBOT 
    with col2:
        st.subheader("2. Scenario Adaptation")

        # Predefined scenarios
        choice = st.selectbox("Select Target Audience:", 
                              ["Public Awareness", "Budget-Constrained", "Emergency Response"])

        if st.button("🚀 Apply Scenario"):
            if "summary" in st.session_state:
                with st.spinner("Adapting..."):
                    adapted_text = generate_scenario_draft(
                        st.session_state.summary, choice, "Adjust strategy accordingly"
                    )
                    st.session_state.adapted = adapted_text
            else:
                st.warning("Summarize the policy first.")

        if "adapted" in st.session_state:
            st.success(f"Strategy for: {choice}")
            st.write(st.session_state.adapted)

        st.markdown("---")
        st.subheader("💬 Ask About Your Own Scenario")

        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Chat input
        user_input = st.text_input("Type your scenario question here:")

        if st.button("Ask AI"):
            if "summary" not in st.session_state:
                st.warning("Please summarize the policy first.")
            elif user_input.strip() == "":
                st.warning("Please enter a scenario question.")
            else:
                with st.spinner("Thinking..."):
                    client = get_client()
                    model_name = get_working_model()

                    # Include previous chat in prompt for context
                    conversation_context = ""
                    for i, chat in enumerate(st.session_state.chat_history):
                        conversation_context += f"Q{i+1}: {chat['user']}\nA{i+1}: {chat['ai']}\n"

                    prompt = (
                        f"Policy Summary: {st.session_state.summary}\n"
                        f"{conversation_context}"
                        f"User Scenario Question: {user_input}\n"
                        f"Provide a professional recommendation:"
                    )
                    try:
                        response = client.models.generate_content(model=model_name, contents=prompt)
                        ai_response = response.text

                        # Save conversation
                        st.session_state.chat_history.append({"user": user_input, "ai": ai_response})

                        # Display full chat history
                        for chat in st.session_state.chat_history:
                            st.markdown(f"**You:** {chat['user']}")
                            st.markdown(f"**AI:** {chat['ai']}")
                    except Exception as e:
                        st.error(f"❌ Chatbot Error: {str(e)}")

else:
    st.info("👈 Please upload a PDF in the sidebar to begin.")