import os
import pandas as pd
from groq import Groq
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

# GLOBALS

retriever = None
client = None
chat_history = []
MAX_HISTORY = 5


# INIT

def initialize():

    global retriever, client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("❌ GROQ_API_KEY not set")

    client = Groq(api_key=api_key)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    if os.path.exists("vector_db"):
        vectorstore = FAISS.load_local("vector_db", embeddings, allow_dangerous_deserialization=True)
    else:
        df = pd.read_csv("university_rag_dataset_10000.csv").dropna()

        docs = []
        for _, row in df.iterrows():
            docs.append(
                Document(
                    page_content=f"""
Category: {row['category']}
Question: {row['question']}
Answer: {row['answer']}
""",
                    metadata={
                        "category": row["category"],
                        "question": row["question"]
                    }
                )
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        docs = splitter.split_documents(docs)
        vectorstore = FAISS.from_documents(docs, embeddings)
        vectorstore.save_local("vector_db")

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5}
    )


# HELPERS

def get_chat_history():
    if not chat_history:
        return "No previous conversation."

    return "\n\n".join(
        f"User: {c['question']}\nAssistant: {c['answer']}"
        for c in chat_history[-MAX_HISTORY:]
    )

def build_context(docs):
    return "\n\n".join(d.page_content for d in docs)

def extract_sources(docs):
    return [
        {
            "category": d.metadata.get("category"),
            "question": d.metadata.get("question")
        }
        for d in docs
    ]


# CORE FUNCTION

def ask(query):

    global retriever, client

    if retriever is None or client is None:
        initialize()

    docs = retriever.invoke(query)

    context = build_context(docs)
    history = get_chat_history()


# System prompt
    system_prompt = """
You are a helpful university assistant chatbot.

Rules:
- Give short, clear and precise answers.
- Keep responses within 4 to 6 lines.
- Do NOT use headings, numbering, or bullet points.
- Do NOT over-explain.
- Be direct and natural like a human tutor answering quickly.
"""

    # USER PROMPT STRUCTURE
    user_prompt = f"""
Conversation:
{history}

Context:
{context}

Question:
{query}

Answer briefly and clearly in 4–6 lines.
"""

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.5,
    max_tokens=250
)

    return {
        "answer": response.choices[0].message.content,
        "sources": extract_sources(docs)
    }


# STREAMLIT ENTRY POINT

def get_response(query):
    result = ask(query)

    chat_history.append({
        "question": query,
        "answer": result["answer"]
    })

    return result