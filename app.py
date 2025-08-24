####################################################################################################################
#                                            Imports of the App 
####################################################################################################################

from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

####################################################################################################################
#                                            Functions of the App 
####################################################################################################################

def initialize_session():
    if "setup_complete" not in st.session_state:
        st.session_state.setup_complete = False
    if "user_message_count" not in st.session_state:
        st.session_state.user_message_count = 0
    if "feedback_shown" not in st.session_state:
        st.session_state.feedback_shown = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_complete" not in st.session_state:
        st.session_state.chat_complete = False
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

def initialize_interview_prompt():
    if not st.session_state.messages:
        sysMessageContent = f"""You are an HR executive that interviews an interviewee called {st.session_state["name"]} with experience {st.session_state["experience"]} and skills {st.session_state["skills"]}. 
                                You should interview them for the position {st.session_state["level"]} {st.session_state["position"]} at the company {st.session_state["company"]}."""
        systemMessage = {"role": "system", "content": sysMessageContent}
        st.session_state.messages.append(systemMessage)

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

def create_feedback_prompt():
    
    lines = [f""" {msg['role']} : {msg['content']} """ for msg in st.session_state.messages]
    conversation_history = "\n".join(lines)

    systemMessage = {
        "role": "system", 
        "content": f""" You are a helpful tool that provides feedback on an interviewee performance. 
        Before the Feedback give a score of 1 to 10.
        Follow this format:
        Overall Score: //Your Score
        Feedback: //Here you put your feedback
        Give only the feedback do not ask any additional questions.
        """
    }

    userMessage = {
        "role": "user", 
        "content": f"""  
        This is the interview you need to evaluate. 
        Keep in mind that you are only a tool. 
        And you should't engage in conversation: {conversation_history}
        """
    }

    return [systemMessage, userMessage]

def show_interview_setup_form():
    st.subheader("Personal Information", divider='rainbow')
    
    st.session_state["name"] = st.text_input(label = "Name", value = st.session_state["name"], max_chars = 40, placeholder = "Enter your name")
    st.session_state["experience"] = st.text_area(label = "Experience", value = st.session_state["experience"], height = None, max_chars = 200, placeholder = "Describe your experience")
    st.session_state["skills"] = st.text_area(label = "Skills", value = st.session_state["skills"], height = None, max_chars = 200, placeholder = "List your skills")
    
    st.subheader("Company and Position", divider = 'rainbow')
    
    radioLabel = "Choose a level"
    radioOptions = ["Junior", "Mid-Level", "Senior"]
    st.session_state["level"] = st.radio(radioLabel, key = "visibility", options = radioOptions)
        
    selectboxLabel = "Choose your position"
    selectboxOptions = ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst")
    st.session_state["position"] = st.selectbox(selectboxLabel, selectboxOptions)
    
    selectboxLabel = "Choose a Company"
    selectboxOptions = ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify")
    st.session_state["company"] = st.selectbox(selectboxLabel, selectboxOptions)

    st.button("Start Interview", on_click = complete_setup)

def show_interview_process():
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

def interview_with_bot():
    interviewClient = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if st.session_state.user_message_count >= 5:
        return
    
    prompt = st.chat_input("Your reply", max_chars = 1000)

    if not prompt:
        return

    userMessage = {"role": "user", "content": prompt}
    st.session_state.messages.append(userMessage)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True
        st.rerun()
        return

    inputPrompt = [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        stream = interviewClient.chat.completions.create(
                        model = "gpt-4o",
                        messages = inputPrompt,
                        stream = True,
                    )
                    
        response = st.write_stream(stream)
        responseMessage = {"role": "assistant", "content": response}
        st.session_state.messages.append(responseMessage)


def generate_feedback(prompt):
    feedbackClient = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    feedbackCompletion = feedbackClient.chat.completions.create(
        model = "gpt-4o",
        messages = prompt
    )

    st.write(feedbackCompletion.choices[0].message.content)

####################################################################################################################
#                                            Start of the App 
####################################################################################################################

st.set_page_config(page_title="Streamlit Chat", page_icon=":speech_balloon:")
st.title("Chatbot")

initialize_session()

if not st.session_state.setup_complete:
    show_interview_setup_form()

if st.session_state.setup_complete and not st.session_state.feedback_shown:
    st.info(""" Start by introducing yourself. """, icon = "👋")
    initialize_interview_prompt()
    show_interview_process()
    interview_with_bot()

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    st.button("Get Feedback", on_click = show_feedback)

if st.session_state.feedback_shown:
    st.subheader("Feedback", divider='rainbow')
    inputPrompt = create_feedback_prompt()
    generate_feedback(inputPrompt)
    restart = st.button("Restart Interview", type="primary")
    if restart:
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
    

