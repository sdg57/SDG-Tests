import os
import streamlit as st
import pandas as pd
import openai
import autogen
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from dotenv import load_dotenv


# Load environment variables from a .env file (if available)
load_dotenv()

# Set OpenAI API Key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("❌ OPENAI_API_KEY is not set. Please set it as an environment variable.")

# Set OpenAI API Key
os.environ["OPENAI_API_KEY"] = openai_api_key
config_list = config_list_from_json(env_or_file="oai_config.json")

# Streamlit UI
st.title("🤖 AI-Powered RFP Response Generator (Single Interaction Per Agent)")
# Purpose and Instructions
# App Instructions
st.markdown(
    """
    <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; color: black;">
        <h3>Welcome to the AI-Powered RFP Response Generator</h3>
        <p>This application assists in generating AI-driven responses for Request for Proposals (RFPs).</p>
        <h4>How to Use:</h4>
        <ol>
            <li><strong>Create AI Agents:</strong> In the side bar Provide an agent name and system message to define how the agent should respond.</li>
            <li>You can create as many agents you want based on your RFP excel and its tabs</li>
            <li><strong>Upload RFP File:</strong> Click on 'Upload RFP Excel File' in the sidebar and select a file containing a "Questions" column with the proposal questions.</li>
            <li><strong>Assign Tabs to Agents:</strong> After uploading the file, in the side bar assign relevant spreadsheet tabs to the agents for question handling.</li>
            <li><strong>Generate AI Responses:</strong> Click 'Generate AI Responses' to let the AI process and generate answers.</li>
            <li><strong>Review AI Responses:</strong> Check the generated responses under the 'Agent Outputs' section.</li>
        </ol>
        <p>Follow these steps to efficiently generate AI-powered RFP responses tailored to your needs.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize the session state key if it doesn't exist
if "agents" not in st.session_state:
    st.session_state["agents"] = []  # Or any default value you want
if "sheet_names" not in st.session_state:
    st.session_state["sheet_names"] = []

agents = {}

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    company_name = st.text_input("Company Name")
    product_name = st.text_input("Product/Solution Name")

    agents = {}
    # Agent Creation
    st.subheader("Create AI Agents")
    agent_name = st.text_input("Agent Name: No Whitespaces for now please ")
    # agent_role = st.text_input("Agent Role")
    agent_system_message = st.text_area("Prompt for the Agent - Enter role description and any other details for the agent to follow")

    if st.button("Add Agent"):
        if agent_name and agent_system_message:
            if "agents" not in st.session_state:
                st.session_state["agents"] = []
            st.session_state["agents"].append({
                "name": agent_name,
                # "role": agent_role,
                "system_message": agent_system_message,
                "assigned_tabs": []
            })

    # File Upload
    uploaded_file = st.file_uploader("Upload RFP Excel File", type=["xlsx"])
    # Store extracted tabs
    if uploaded_file:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        st.session_state["sheet_names"] = sheet_names
        st.success(f"Detected sheets: {', '.join(sheet_names)}")
    

    # Multi-select for sheet assignment
    st.subheader("Assign Tabs to Agents")
    if st.session_state["agents"] and st.session_state["sheet_names"]:
        selected_agent = st.selectbox("Select Agent", [agent["name"] for agent in st.session_state["agents"]])
        selected_sheets = st.multiselect("Assign 1 or more Tabs to Agent", st.session_state["sheet_names"])
    
    if st.button("Assign Tabs"):
        for agent in st.session_state["agents"]:
            if agent["name"] == selected_agent:
                agent["assigned_tabs"] = selected_sheets
                st.success(f"Assigned {', '.join(selected_sheets)} to {selected_agent}")

    # Display Active Agents and Tab Assignments
    if st.session_state["agents"]:
        st.subheader("Updated Agent Assignments")
        for agent in st.session_state["agents"]:
            st.info(f"{agent['name']} -  (Tabs: {', '.join(agent['assigned_tabs'])})")



# Process RFP File & Extract Questions from Assigned Tabs
if uploaded_file:
    try:
        if "categorized_questions" not in st.session_state:
            st.session_state["categorized_questions"] = {}

        xls = pd.ExcelFile(uploaded_file)
        
        for agent in st.session_state["agents"]:
            agent_name = agent["name"]
            # assigned_tabs = agent["assigned_tabs"]
            assigned_tabs = agent.get("assigned_tabs", []) #get assigned tabs

            if not assigned_tabs:
                st.warning(f"Agent '{agent_name}' has no assigned tabs. Assign tabs before generating responses.")
                st.session_state["categorized_questions"][agent_name] = []  # Ensure empty list is stored
                continue  # Skip processing for this agent

            extracted_questions = []

            for sheet in assigned_tabs:
                if sheet not in xls.sheet_names:
                    st.warning(f"Sheet '{sheet}' not found in the uploaded file for {agent_name}. Skipping it.")
                    continue  # Skip if sheet is missing

                df = xls.parse(sheet)
                question_cols = [col for col in df.columns if "question" in col.lower()]  

                if not question_cols:
                    st.warning(f"⚠️ No question columns found in '{sheet}' for agent '{agent_name}'.")
                    continue  


                for col in df.columns:
                    if "question" in col.lower():  # Detect question columns
                        extracted_questions.extend(df[col].dropna().tolist())
            # # Debug: Print extracted questions
            # st.write(f"🔍 Debug: Questions extracted for agent '{agent_name}': {extracted_questions}")

            st.session_state["categorized_questions"][agent["name"]] = extracted_questions

        st.success("RFP questions extracted. Please assign Spreadsheet tabs to agents in the sidebar")

    except Exception as e:
        st.error(f"Error processing file: {e}")

#nitialize AI Agents with User-Defined Roles & Tabs
def initialize_agents():
    if "agents" not in st.session_state:
        st.session_state["agents"] = []

    agents = {}

    # Create a User Proxy (Coordinator)
    user_proxy = UserProxyAgent(
        name="Coordinator",
        code_execution_config=False,
        human_input_mode="NEVER",
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE") #or "complete" in x.get("content", "").lower()
    )
    agents["Coordinator"] = user_proxy

    # Create User-Defined Agents
    for agent_cfg in st.session_state["agents"]:
        if agent_cfg["name"] not in agents:  # Ensure each agent is only initialized once
            agent = AssistantAgent(
                name=agent_cfg["name"],
                system_message=agent_cfg["system_message"],
                llm_config={"config_list": config_list}
            )
            agents[agent_cfg["name"]] = agent
    return agents

# Editable Responses
if "rfp_responses" not in st.session_state:
    st.session_state["rfp_responses"] = {}

st.subheader("Generate AI Responses")

# Generate AI Response for Each Agent Using User Proxy (Single Turn)
if st.button("Generate AI Responses"):
    if "categorized_questions" not in st.session_state or not any(st.session_state["categorized_questions"].values()):
        st.error("Please upload an RFP file and assign agents to tabs.")
    else:
        agents = initialize_agents()

        for agent_name, questions in st.session_state["categorized_questions"].items():
            if agent_name not in agents:
                st.warning(f"No AI agent available for {agent_name}.")
                continue

            with st.spinner(f"Generating response for {agent_name}..."):
                # response = agents["Coordinator"].initiate_chat(
                #     agents[agent_name],
                #     message=f"Company: {company_name}\nProduct: {product_name}\nAgent Role: {agent_name}\nQuestions: {questions}",
                #     max_turns=1  # Ensures single response from the agent
                # )

                # Use autogen.initiate_chats() like in your screenshot
                chat_results = autogen.initiate_chats([
                    {
                        "sender": agents["Coordinator"],
                        "recipient": agents[agent_name],
                        "message": f"You work for {company_name}. Find responses related to {questions} for the {product_name} as a {agent_name} and follow instructions these instructions: {agent_system_message}. Reply with TERMINATE once done.",
                        "silent": False,
                        "clear_history": False,
                        "summary_method": "last_msg",
                        # "carryover": "TERMINATE"
                    }
                ])

                # Store the single response per agent
                st.session_state["rfp_responses"][agent_name] = chat_results

        st.success("AI responses generated!")

# Display AI Responses
st.subheader("Agent Outputs")

for agent_name, chat_results in st.session_state["rfp_responses"].items():
    st.subheader(f"Agent: {agent_name}")

    # Extract and display only the last response message
    try:
        readable_response = chat_results[-1].chat_history[-1]["content"]
    except (IndexError, KeyError, TypeError):
        readable_response = "No response available."

    # Display the response with Markdown
    st.markdown(f"**Response:**\n\n{readable_response}")


# # Export Final Responses
# if st.button("Export Responses to Excel"):
#     response_data = pd.DataFrame([
#         {"Agent": agent_name, "Response": response}
#         for agent_name, response in st.session_state["rfp_responses"].items()
#     ])
#     response_data.to_excel("rfp_ai_final_responses.xlsx", index=False)
#     st.success("Final responses exported successfully!")
