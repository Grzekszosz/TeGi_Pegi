#test
import tempfile
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st
import pandas as pd

from CVgetData.get_persons import get_persons, count_persons
from CVgetData.get_rfps import get_rfps, count_rfps
from agent.chat import run_chat

from CVgetData.cv_reader.graph_builder import  CVGraphBuilder

load_dotenv(".env")

def save_upload_to_temp(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix or ""
    # NamedTemporaryFile na Windows: delete=False, bo inaczej plik bywa zablokowany
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getbuffer())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


#✅ RFP → Skill requirements są w grafie i są odczytywane (mandatory + all req)
#✅ Person → Skill są w grafie i są odczytywane
#✅ Tryb STRICT działa logicznie (brak wyników, bo nikt nie ma kompletu mandatory)
#✅ Tryb SOFT robi ranking + explainability (matched/missing)
#✅ Brak warningów Neo4j o brakujących property (czyli query są “czyste”)
#Co NIE jest spełnione (to są wymogi PRD, których Twój system jeszcze nie realizuje)
#TODO ❌ Real-time availability management (YAML/JSON, allocation %, daty, aktualizacja bez rebuild)
#TODO ❌ Multi-factor scoring (skills + experience level + availability + wagi)
#TODO ❌ Experience/proficiency na relacji HAS_SKILL (np. lata, poziom 1–5)
#TODO ❌ Temporal queries typu „kto będzie dostępny po zakończeniu projektu”
#TODO ❌ Team composition optimization / what-if
#TODO ❌ (opcjonalnie PRD) encje/relacje typu Company/Project/Certification/University




def load_cv_page():
    st.title("CV Database")
    st.subheader(f"Total CVs in the database: {count_persons()}")

    st.subheader("CV Details")
    data = get_persons()
    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch", hide_index=True)

    st.subheader("Actions")

    uploaded_file = st.file_uploader(
        "Select CV from your device",
        type=["pdf", "docx", "txt"],
        key="cv_uploader",
    )

    if st.button("Add a new CV", disabled=(uploaded_file is None), key="add_cv_btn"):
        if uploaded_file is None:
            st.warning("Select CV")
            return

        tmp_path = save_upload_to_temp(uploaded_file)

        try:
            ext = tmp_path.suffix.lower()
            if ext != ".pdf" or ext != ".json" or ext != ".txt":
                st.error(f"Na razie wspieram tylko PDF, json, txt. Dostałem: {ext}")
                return

            builder = CVGraphBuilder()  # możesz też wynieść wyżej
            builder.process_single_cv(tmp_path)

            st.success("CV processed and added to DB")
        except Exception as e:
            st.error(f"Processing failed: {type(e).__name__}: {e}")
        finally:
            tmp_path.unlink(missing_ok=True)


def load_rfp_page():
    st.title('RFP Database')
    st.subheader(f'Total RFPs in the database: {count_rfps()}')

    st.subheader('RFP Details')
    data = get_rfps()
    print(data)

    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch', hide_index=True)

    st.subheader('Actions')
    uploaded_file = st.file_uploader('Select RfP from your device', type=None)
    if st.button('Add a new RFP'):
        if uploaded_file is not None:
            st.success('Uploaded RFP')
        else:
            st.warning('Select RFP')

def load_bi_page():
    st.title("TalentMatch AI")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "ai", "content": "Siema. Pytaj o dostępność ludzi, skille i dopasowanie do RFP."}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Napisz wiadomość...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("ai"):
            with st.spinner("Myślę..."):
                ai_reply = run_chat(st.session_state.messages)

            st.markdown(ai_reply)

        st.session_state.messages.append({"role": "ai", "content": ai_reply})

def load_proj_ass_page():
    st.title('Project Assignments')
    st.subheader(f'Total Project Assignments in the database: {5}')

    st.subheader('Project Assignment Details')
    data = [
        {
            'Id': 'PRJ-001',
            'Name': 'Customer Portal for DataSystems Inc',
            'Start Date': '2025-08-04',
            'End Date': '',
            'Team Size': '4',
            'Assigned Programmers': ['Vincent Smith', 'David Ross', 'Nicholas Smith', 'Roger Porter']
        },
        {
            'Id': 'PRJ-006',
            'Name': 'E-commerce Platform for FinTech Innovations',
            'Start Date': '2025-02-24',
            'End Date': '2025-07-2',
            'Team Size': '2',
            'Assigned Programmers': ['Sandra Rose', 'Kenneth House']
        },
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch', hide_index=True)

    st.subheader('Actions')
    uploaded_file = st.file_uploader('Select Project assignment from your device', type=None)
    if st.button('Add a new Project Assignment'):
        if uploaded_file is not None:
            st.success('Uploaded Project assignment')
        else:
            st.warning('Select Project assignment')

if __name__ == "__main__":
    st.sidebar.title('MENU')
    page = st.sidebar.radio('Select page:', ['CVs', 'RFPs', 'Project Assignments' , 'BI Query Tool'])

    match page:
        case 'CVs':
            load_cv_page()
        case 'RFPs':
            load_rfp_page()
        case 'Project Assignments':
            load_proj_ass_page()
        case 'BI Query Tool':
            load_bi_page()
