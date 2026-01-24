import tempfile
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from CVgetData.build_graph_from_rfps import build_rfp
from CVgetData.get_persons import get_persons, count_persons
from CVgetData.get_rfps import get_rfps, count_rfps
from CVgetData.tools.assignment import list_project_assignments
from agent.chat import run_chat
from CVgetData.cv_reader.graph_builder import  CVGraphBuilder
from agent.config import init_neo4j

load_dotenv(".env")

def save_upload_to_temp(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix or ""

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getbuffer())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)

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
        type=["pdf", "json", "txt"],
        key="cv_uploader",
    )

    if st.button("Add a new CV", disabled=(uploaded_file is None), key="add_cv_btn"):
        if uploaded_file is None:
            st.warning("Select CV")
            return
        tmp_path = save_upload_to_temp(uploaded_file)
        try:
            ext = tmp_path.suffix.lower()
            if ext != ".pdf" and ext != ".json" and ext != ".txt":
                st.error(f"Na razie wspieram tylko PDF, json, txt. Dostałem: {ext}")
                return
            builder = CVGraphBuilder()
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
    uploaded_file = st.file_uploader(
        "Select RFP from your device",
        type=["pdf", "json", "txt"],
        key="rfp_uploader",
    )
    if st.button("Add a new RFP", disabled=(uploaded_file is None), key="add_rfp_btn"):
        if uploaded_file is None:
            st.warning("Select RFP")
            return
        tmp_path = save_upload_to_temp(uploaded_file)
        try:
            ext = tmp_path.suffix.lower()
            if ext != ".pdf" and ext != ".json" and ext != ".txt":
                st.error(f"Na razie wspieram tylko PDF, json, txt. Dostałem: {ext}")
                return
            build_rfp(tmp_path)
            st.success("RFP processed and added to DB")
        except Exception as e:
            st.error(f"Processing failed: {type(e).__name__}: {e}")
        finally:
            tmp_path.unlink(missing_ok=True)

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
    st.title("Project Assignments")
    g = init_neo4j()
    rows = list_project_assignments(g) or []
    st.subheader(f"Total Projects in the database: {len(rows)}")
    if not rows:
        st.info("Brak projektów (RFP) w bazie.")
        return
    projects_df = pd.DataFrame([{
        "Id": r["id"],
        "Name": r.get("name"),
        "Client": r.get("client"),
        "Type": r.get("project_type"),
        "Start Date": r.get("start_date"),
        "End Date": r.get("end_date"),
        "Team Size": r.get("team_size"),
        "Assigned": r.get("assigned_count", 0),
    } for r in rows])

    st.subheader("Projects")
    st.dataframe(projects_df, width="stretch", hide_index=True)
    st.subheader("Assignments for selected project")
    rfp_ids = [r["id"] for r in rows]
    selected_id = st.selectbox("Choose project (RFP)", rfp_ids)
    selected = next((r for r in rows if r["id"] == selected_id), None)
    assigned = (selected or {}).get("assigned", [])
    if not assigned:
        st.warning("Brak przypisanych osób do tego projektu.")
        return
    ass_df = pd.DataFrame([{
        "Person": a.get("person"),
        "Person UUID": a.get("person_uuid"),
        "Role": a.get("role"),
        "Allocation": a.get("allocation"),
        "Start": a.get("start_date"),
        "End": a.get("end_date"),
    } for a in assigned])
    st.dataframe(ass_df, width="stretch", hide_index=True)

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
