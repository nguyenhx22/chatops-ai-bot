# ChatOps-AI Bot

ChatOps-AI Bot is an AI-driven chatbot powered by intelligent agents for managing production operations. It enables Cloud Foundry users to manage production tasks through natural conversation, allowing operations such as starting, stopping, and restarting cloud applications. Additionally, it leverages Large Language Models (LLMs) to analyze incidents, provide intelligent recommendations, execute remediation actions, and continuously learn from past incidents for improved accuracy.

## Features

- **Cloud Foundry Tasks**: Manage production tasks through natural conversation.
- **Incident Resolution Assistant (IRA)**: Analyze incidents, provide recommendations, and execute remediation actions.
- **User Authentication**: Secure login with Azure AD.
- **Customizable LLM Models**: Select and configure different LLM models for the chatbot.

## Project Structure

```
├── auth/
│   ├── oauth_client.py
│   ├── authentication.py
│   └── authentication_handler.py
├── backend/
│   ├── chatops_service.py
│   ├── db_service.py
│   ├── knowledge_base.py
│   └── utilities.py
├── bin/
├── core/
│   └── config.py
├── data/
│   ├── ira_incident_history.txt
│   ├── ira_investigation_history.txt
│   ├── mpa_platform_data.txt
│   └── mpa_platform_summary.txt
├── frontend/
│   ├── chat_window.py
│   ├── chat_sidebar.py
│   └── style.py
├── agents/
│   ├── cloud_foundry_agent.py
│   ├── ira_agent.py
│   ├── prompts/
│   │    └── cf_agent_system_prompt.py
│   └── tools/
│       ├── cloud_foundry_tools.py
│       ├── common_tools.py
│       └── ira_tools.py
├── notebooks/
├── scripts/
├── tests/
├── app.py
├── manifest.yml
├── README.md
├── requirements.txt
└── runtime.txt
```

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your_organization_name/chatops-ai-bot.git
    cd chatops-ai-bot
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    - Create a `.env` file in the root directory with the following content:
        ```env
        # LLM Keys
        OPENAI_API_KEY=your_openai_api_key
        GROQ_API_KEY=your_groq_api_key

        # Cloud Foundry
        CF_PASSWORD=your_cf_password

        # Postgres
        PG_DB_PASSWORD=your_pg_db_password

        # Azure
        AZ_TENANT_ID=your_azure_tenant_id
        AZ_CLIENT_ID=your_azure_client_id
        AZ_CLIENT_SECRET=your_azure_client_secret

        # ChatOps Service
        CLIENT_SECRET_CHATOPS_SERVICE=your_client_secret_chatops_service
        ```

## Usage

1. Run the application:
    ```sh
    streamlit run app.py
    ```

2. Open your web browser and navigate to `http://localhost:8501`.

3. Click Azure AD and start interacting with the chatbot.


