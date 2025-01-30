import streamlit as st
import autogen
import pandas as pd

# Configuration for LLM
llm_config = {
    "model": "gpt-4o", 
    "api_key": "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"
}

# Initialize agents
AE_Agent = autogen.AssistantAgent(
    name="AE_Agent",
    llm_config=llm_config,
    system_message="""
    You are the Account Executive Agent. Your role is to analyze the business requirements from the RFP and provide a strategic response.
    """,
)

Tech_Specialist_Agent = autogen.AssistantAgent(
    name="Tech_Specialist_Agent",
    llm_config=llm_config,
    system_message="""
    You are the Technical Specialist Agent. Your role is to analyze the technical requirements from the RFP and suggest technical solutions.
    """,
)

Product_Specialist_Agent = autogen.AssistantAgent(
    name="Product_Specialist_Agent",
    llm_config=llm_config,
    system_message="""
    You are the Product Specialist Agent. Your role is to align the product capabilities with the RFP requirements and provide insights.
    """,
)

user_proxy_auto = autogen.UserProxyAgent(
    name="User_Proxy_Auto",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE") or "complete" in x.get("content", "").lower(),
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "coding",
        "use_docker": False,
    },
)

# Streamlit UI
st.title("RFP Analysis and Agent Collaboration")

uploaded_file = st.file_uploader("Upload an RFP Excel file with 3 tabs", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Log the uploaded file details
        # st.write(f"Uploaded file details: {uploaded_file}")

        # Read the Excel file
        rfp_data = pd.ExcelFile(uploaded_file)
        st.write(f"Sheet names: {rfp_data.sheet_names}")
        
        # Verify tabs
        if len(rfp_data.sheet_names) < 3:
            st.error("The uploaded file must have at least 3 tabs.")
        else:
            # Load data from tabs
            tab1 = pd.read_excel(rfp_data, sheet_name=rfp_data.sheet_names[0])
            tab2 = pd.read_excel(rfp_data, sheet_name=rfp_data.sheet_names[1])
            tab3 = pd.read_excel(rfp_data, sheet_name=rfp_data.sheet_names[2])

            # Display preview of tabs
            st.subheader("Preview of Tab 1")
            st.dataframe(tab1.head())
            st.subheader("Preview of Tab 2")
            st.dataframe(tab2.head())
            st.subheader("Preview of Tab 3")
            st.dataframe(tab3.head())

            # Ensure agents are initialized
            if not (AE_Agent and Tech_Specialist_Agent and Product_Specialist_Agent):
                st.error("Agents could not be initialized. Please check your configuration.")
            else:
                # Tasks for agents
                st.subheader("Agent Outputs")
                
                with st.spinner("AE Agent working on the analysis...."):
                    chat_results = autogen.initiate_chats([
                        {   
                            "sender": user_proxy_auto,
                            "recipient": AE_Agent,
                            "message": f"Find responses to each question and get me the answers. The Company that is responding to the RFP is Microsoft: {tab1.to_csv(index=False)}. Reply with TERMINATE once done.",
                            "silent": False,
                            "clear_history": False,
                            "summary_method": "last_msg",
                            "carryover": "Wait for confirmation of code execution before terminating the conversation. Reply TERMINATE in the end when everything is done.",
                        }
                    ])
                    st.markdown(chat_results[-1].chat_history[-1]["content"])
                
                
                with st.spinner("Product Specialist working on the analysis...."):
                    chat_results_product = autogen.initiate_chats([
                        {   
                            "sender": user_proxy_auto,
                            "recipient": Product_Specialist_Agent,
                            "message": f"Find responses to each question and get me the answers. The Company that is responding to the RFP is Microsoft: {tab2.to_csv(index=False)}. Reply with TERMINATE once done.",
                            "silent": False,
                            "clear_history": False,
                            "summary_method": "last_msg",
                            "carryover": "Reply TERMINATE in the end when everything is done.",
                        }
                    ])
                    st.markdown(chat_results_product[-1].chat_history[-1]["content"])
                
                with st.spinner("Technical Specialist working on the analysis...."):
                    chat_results_tech = autogen.initiate_chats([
                        {   
                            "sender": user_proxy_auto,
                            "recipient": Tech_Specialist_Agent,
                            "message": f"Find responses to each question and get me the answers. The Company that is responding to the RFP is Microsoft: {tab3.to_csv(index=False)}. Reply with TERMINATE once done.",
                            "silent": False,
                            "clear_history": False,
                            "summary_method": "last_msg",
                            "carryover": "Reply TERMINATE in the end when everything is done.",
                        }
                    ])
                    st.markdown(chat_results_tech[-1].chat_history[-1]["content"])
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.write("Please upload a file to proceed.")
