import streamlit as st
from university_rag import get_response


# PAGE CONFIG

st.set_page_config(
    page_title="University AI Chatbot",
    page_icon="🎓",
    layout="centered"
)


# CUSTOM CSS

st.markdown("""
<style>
.main {
    padding-top: 1rem;
}

.stButton button {
    width: 100%;
    border-radius: 10px;
}

div[data-testid="stSidebar"] {
    border-right: 1px solid #e6e6e6;
}
</style>
""", unsafe_allow_html=True)


# TITLE

st.title("🎓 University AI Chatbot")
st.caption("Ask about attendance, fees, exams, scholarships, placements, hostel rules and more.")

# -----------------------
# SESSION STATE
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "questions" not in st.session_state:
    st.session_state.questions = []

if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""


# SIDEBAR

with st.sidebar:

    st.header("📚 Previous Questions")

    if st.session_state.questions:

        unique_questions = list(dict.fromkeys(
            reversed(st.session_state.questions)
        ))

        for i, q in enumerate(unique_questions):

            display_q = (
                q[:40] + "..."
                if len(q) > 40
                else q
            )

            if st.button(
                display_q,
                key=f"history_{i}",
                use_container_width=True
            ):
                st.session_state.selected_question = q

    else:
        st.info("No previous questions yet.")

    st.markdown("---")

    st.subheader("📊 Statistics")

    st.metric(
        "Questions Asked",
        len(st.session_state.questions)
    )

    st.metric(
        "Messages",
        len(st.session_state.messages)
    )

    st.markdown("---")

    if st.button(
        "🧹 Clear Chat",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.session_state.questions = []
        st.session_state.selected_question = ""
        st.rerun()


# QUICK ACTIONS

st.markdown("### 🚀 Quick Questions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📚 Attendance"):
        st.session_state.selected_question = (
            "What is the attendance policy?"
        )

with col2:
    if st.button("💰 Fees"):
        st.session_state.selected_question = (
            "Explain the fee structure."
        )

with col3:
    if st.button("🏠 Hostel"):
        st.session_state.selected_question = (
            "What are the hostel rules?"
        )

# WELCOME SCREEN

if not st.session_state.messages:
    st.info(
        "👋 Welcome! Ask anything related to university rules, academics, exams, attendance, hostel facilities, scholarships, placements, or fees."
    )

# -----------------------
# DISPLAY CHAT HISTORY
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# CHAT INPUT

query = st.chat_input("Ask your question...")

# Handle sidebar question clicks
if st.session_state.selected_question:
    query = st.session_state.selected_question
    st.session_state.selected_question = ""

# PROCESS QUERY

if query:

    # Save question history
    st.session_state.questions.append(query)

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": query
    })

    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):

        with st.spinner("Thinking... 🤔"):

            try:
                result = get_response(query)

                answer = result.get(
                    "answer",
                    "⚠️ No response generated."
                )

            except Exception as e:
                answer = f"⚠️ Error: {str(e)}"

        
    
        
        placeholder = st.empty()

        streamed_text = ""

        for word in answer.split():
            streamed_text += word + " "
            placeholder.markdown(streamed_text)

        placeholder.markdown(streamed_text)

    
        # FEEDBACK BUTTONS

        col1, col2 = st.columns(2)

        with col1:
            st.button(
                "👍 Helpful",
                key=f"helpful_{len(st.session_state.messages)}"
            )

        with col2:
            st.button(
                "👎 Not Helpful",
                key=f"not_helpful_{len(st.session_state.messages)}"
            )

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })