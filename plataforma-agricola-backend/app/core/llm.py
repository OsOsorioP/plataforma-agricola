from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from app.core.config import (
    GOOGLE_API_KEY,
    GROQ_API_KEY,
)

llm_supervisor = ChatGroq(
    model_name="llama3-70b-8192",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)

llm_water = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)

llm_risk = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    google_api_key=GOOGLE_API_KEY
)

llm_supply_chain = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY
)

llm_vision = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)

llm_production = ChatGroq(
    model_name="gemini-2.5-flash",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)

llm_sustainability = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    google_api_key=GOOGLE_API_KEY
)

llm_kpi = ChatGroq(
    model_name="gemma-7b-it",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)
