from dotenv import load_dotenv
import streamlit as st
import pandas as pd

load_dotenv(".env")

def load_cv_page():
    st.title('CV Database')
    st.subheader(f'Total CVs in the database: {5}')

    st.subheader('CV Details')
    data = [
        {
            'Id': 1,
            'Name': 'Jan Kowalski',
            'Email': 'jan@example.com',
            'Location': 'Warsaw'
        },
        {
            'Id': 2,
            'Name': 'Dorota Marek',
            'Email': 'dorota@example.com',
            'Location': 'Gdańsk'
        },
    ]
    df = pd.DataFrame(data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    st.subheader('Actions')
    uploaded_file = st.file_uploader('Select CV from your device', type=None)
    if st.button('Add a new CV'):
        if uploaded_file is not None:
            st.success('Uploaded CV')
        else:
            st.warning('Select CV')

def load_rfp_page():
    st.title('RFP Database')
    st.subheader(f'Total RFPs in the database: {5}')

    st.subheader('RFP Details')
    data = [
        {
            'Project Title': 'Cloud Migration Project',
            'Start Date': '2025-10-04',
            'Duration': '19 months',
            'Team Size': '12 people',
            'Budget Range': '$100K - $250K'
        },
        {
            'Project Title': 'Security Enhancement Development',
            'Start Date': '2025-09-28',
            'Duration': '20 months',
            'Team Size': '9 people',
            'Budget Range': '$500K - $1M'
        },
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader('Actions')
    uploaded_file = st.file_uploader('Select RfP from your device', type=None)
    if st.button('Add a new RFP'):
        if uploaded_file is not None:
            st.success('Uploaded RFP')
        else:
            st.warning('Select RFP')

def load_bi_page():
    st.title('BI QueryTool')

    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                'role': 'ai',
                'content': 'Hi! What you wanna know'
            }
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    user_input = st.chat_input('Write message...')

    if user_input:
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input
        })
        with st.chat_message('user'):
            st.markdown(user_input)

        ai_reply = 'Mock answer from ai bot'
        st.session_state.messages.append({
            'role': 'ai',
            'content': ai_reply
        })
        with st.chat_message('ai'):
            st.markdown(ai_reply)

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
    st.dataframe(df, use_container_width=True, hide_index=True)

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
