from dotenv import load_dotenv
import streamlit as st
import pandas as pd

load_dotenv(".env")

def load_cv_page():
    st.title('Users CVs')
    st.subheader(f'Total CVs: {5}')

    st.subheader('Users Info Table')
    data = [
        {
            'id': 1,
            'name': 'Jan Kowalski',
            'email': 'jan@example.com',
            'location': 'Warsaw'
        },
        {
            'id': 2,
            'name': 'Dorota Marek',
            'email': 'dorota@example.com',
            'location': 'Gdańsk'
        },
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader('Actions')
    uploaded_file = st.file_uploader('Select CV from your device', type=None)
    if st.button('Add CV'):
        if uploaded_file is not None:
            st.success('Uploaded CV')
        else:
            st.warning('Select CV')

def load_rfp_page():
    st.title('Request for Proposals')
    st.subheader(f'Total RFPs: {5}')

    st.subheader('RFP Info Table')
    data = [
        {
            'Project title': 'Cloud Migration Project',
            'Start Date': '',
            'Duration': '19 months',
            'Team Size': '12 people',
            'Budget Range': '$100K - $250K'
        },
        {
            'Project title': 'Cloud Migration Project',
            'Start Date': '',
            'Duration': '19 months',
            'Team Size': '12 people',
            'Budget Range': '$100K - $250K'
        },
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader('Actions')
    uploaded_file = st.file_uploader('Select RfP from your device', type=None)
    if st.button('Add RfP'):
        if uploaded_file is not None:
            st.success('Uploaded RfP')
        else:
            st.warning('Select RfP')

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
    st.title('Project assignments')
    st.subheader(f'Total Project assignments: {5}')

    st.subheader('Project assignment Info Table')
    data = [
        {
            'id': 1,
            'name': 'Jan Kowalski',
            'email': 'jan@example.com',
            'location': 'Warsaw'
        },
        {
            'id': 2,
            'name': 'Dorota Marek',
            'email': 'dorota@example.com',
            'location': 'Gdańsk'
        },
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader('Actions')
    uploaded_file = st.file_uploader('Select Project assignment from your device', type=None)
    if st.button('Add Project assignment'):
        if uploaded_file is not None:
            st.success('Uploaded Project assignment')
        else:
            st.warning('Select Project assignment')

if __name__ == "__main__":
    st.sidebar.title('MENU')
    page = st.sidebar.radio('Select page:', ['CVs', 'RFPs', 'BI QueryTool', 'Project assignments'])

    match page:
        case 'CVs':
            load_cv_page()
        case 'RFPs':
            load_rfp_page()
        case 'BI QueryTool':
            load_bi_page()
        case 'Project assignments':
            load_proj_ass_page()