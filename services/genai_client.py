import os
import streamlit as st
from google import genai

@st.cache_resource
def get_genai_client():
    return genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT_ID"),
        location="us-central1"
    )
