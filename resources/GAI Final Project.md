# Project Overview

* Context   
  We are building an SMS‑based chatbot that interacts with job candidates for a Python‑developer position  
* Goal  
  Gather/verify information, answer questions, and ultimately schedule an interview with a human recruiter (or politely end the conversation)  
* Main Agent  
  Manages the dialogue turn‑by‑turn and decides among three actions:  
  * Continue  
  * Schedule  
  * End  
* Advisor Agents – Specialized helpers  
  * Exit Advisor – Confirms when ending the conversation makes sense  
  * Scheduling Advisor – Checks recruiter calendars (via SQL DB) & validates proposed slots  
  * Info Advisor – Handles candidate questions related to the position, May utilize vector database information related to the position

# Main Components

* Main Agent  
  Orchestrates the conversation with the candidate. In each interaction, it must determine the appropriate course of action by selecting from the following options:  
  * Option 1: Continue the Conversation   
    If the candidate requests additional information or has further questions, the MAIN AGENT continues the dialogue by exchanging more messages  
  * Option 2: End the Conversation  
    If the candidate expresses disinterest (e.g., already found a job), the MAIN AGENT may decide to conclude the interaction  
  * Option 3: Schedule an Interview  
    If appropriate, the MAIN AGENT proceeds to schedule an interview, confirming date and time with the recruiter  
* Supporting Agents ("Advisors")  
  To manage complexity and maintain modularity, the MAIN AGENT consults specialized secondary agents (Advisors) at each decision point:  
  * Conversation Exit Advisor  
    Evaluates whether it is appropriate to end the conversation. This agent ensures that uninterested candidates are not unnecessarily followed up with, avoiding a negative experience  
  * Interview Scheduling Advisor  
    Assists in determining whether it’s the right time to schedule an interview. It checks conversation context, validates proposed times, and may interact with external tools (e.g., recruiter calendars via function calling)  
  * Conversation Info Advisor  
    Helps answering candidate’s questions, formulate the next message and maintain engagement. Also aims to drive the conversation toward the end goal: scheduling an interview  
* Evaluation Strategy  
  To assess the performance of the system, a labeled data set of real conversations is provided. Each response turn is annotated with the correct action the bot should  
  Take:  
  * End the conversation  
  * Schedule an interview  
  * Continue the conversation

  These labeled examples should be used to evaluate model performance using metrics such as:

* Accuracy  
* Confusion Matrix

# Additional Implementation Steps

* Fine-Tuning  
  Conversation Exit Advisor should be fine-tuned to detect conversation scenarios that are expected to conclude  
* Embedding  
  Separately from the main process, we will carry out an offline embedding step, converting the provided PDF into vector representations stored in a Chroma database  
* Agent Architecture  
  With LangChain & OpenAI API Endpoint and Models  
* Function Calling to interact with the SQL database  
  When the Scheduling Advisor retrieves available time slots, it analyzes the conversation context. For example, if the user mentions 'next Friday', it infers the current date from the time the conversation took place and combines it with the user's input. Based on this, it then suggests the three nearest available time slots  
* Streamlit  
  Instead of using SMS, the proof of concept (PoC) will be implemented in Streamlit and deployed to the Streamlit Community Cloud  
* Prompting Strategies  
  * Role’s  
  * API Parameter  
  * Instructions Prompts  
  * Few-Shot Learning  
*  Evaluation & Testing  
  Use the labeled test cases to evaluate how well the multi-agent system performs on End/Continue/Schedule tasks

# Project Structure

A Project must have:

* Project Repository, that includes:  
  * Working with Git (and .gitignore)  
  * Virtual Environment (.venv and requirements.txt file)  
  * .env file (environment variables)  
  * README.md file that includes project documentation, such as:  
    * Project purpose  
    *  How to install and run the project locally  
    * Basic usage examples  
    * Project Structure  
  * App (main application code)  
    *  \_\_init\_\_.py file (package initializer)  
    * main.py file (the entry point of the application)  
    * Modules  
      Application modules, for: main app, Fine-Tuning, Embedding, etc  
      * \_\_init\_\_.py file  
      * module.py file (module implementation)  
  * Streamlit  
    * \_\_init\_\_.py file  
    * streamlit\_main.py file (Main Streamlit app)  
  * Test  
    * test\_evals.ipynb \- Detailed jupyter notebook with model performance metrics (Accuracy, Confusion Matrix)  
* Project Structure Overview  
  This is a suggested project structure ,it may vary and be adjusted as needed

├── .gitignore              \# Specifies files to ignore in version control  
├── README.md               \# Project documentation  
├── LICENSE                 \# License information  
├── requirements.txt        \# Python dependencies  
├── .venv/                  \# Virtual environment (ignored by git)  
├── .env                    \# Environment variables (ignored by git)  
├── app/                    \# Main application code  
│   ├── \_\_init\_\_.py         \# Package initializer  
│   ├── main.py             \# Entry point of the application  
│   └── modules/            \# Application modules  
│       ├── \_\_init\_\_.py     \# Package initializer for modules  
│       ├── module\_1/       \# Module 1  
│       │   ├── \_\_init\_\_.py  
│       │   └── m\_1.py      \# Module 1 implementation  
│       └── module\_2/       \# Module 2  
│           ├── \_\_init\_\_.py  
│           └── m\_2.py      \# Module 2 implementation  
├── streamlit\_app/          \# Streamlit UI code  
│   ├── \_\_init\_\_.py  
│   ├── streamlit\_main.py   \# Main Streamlit app  
│   └── utils.py            \# Helper functions for Streamlit components  
├── tests/                  \# Test suite  
│   ├── test\_main.py        \# Tests for the main application  
│   └── test\_evals.ipynb    \# For testing performance metrics

# Data & Resources

* Workflow Diagram  
* sms\_conversations.json \- labeled data set of real conversations  
* Python Developer Job Description.pdf  
* OpenAI account – API keys for embeddings, chat, and fine‑tuning  
* Chroma – Local or cloud instance  
* db\_Tech.sql – Simple availability table seeded with demo slots  
* LangChain – Agents, Memories, Tool

# Important Note

The bot's process includes additional options and complexities that were not  
covered here, but had to be simplified for the scope of this project

Workflow Diagram:  

# One Turn in the Conversation

```mermaid
flowchart TD
    A[User] --> B[User Initiates/Response Conv]
    A --> C[Fill Registration Form]
    B & C --> D[Receives and Process Input]
    D --> E{Consult Advisor<br>Decides 1 of 3 Options}
    
    E --> F1[Exit Advisor]
    E --> F2[Sched Advisor]
    E --> F3[Info Advisor]

    %% Exit Advisor Path
    F1 --> G1[Sends Output to Exit Advisor]
    G1 --> H1[Processes the complete chat history]
    H1 --> I1{Decides 1 of 2 Options}
    I1 --> J1[End Conversation]
    I1 --> K1[Don't End Conv]
    J1 --> L1[Sends Output to Main Agent]
    K1 --> L1

    %% Sched Advisor Path
    F2 --> G2[Sends Output to Sched Advisor]
    G2 --> H2[Processes the complete chat history]
    H2 --> I2{Decides 1 of 2 Options}
    I2 --> J2[Don't Sched]
    I2 --> K2[Sched]
    K2 --> L2[SQL Retrieval Sched Options]
    J2 --> M2[Sends Output to Main Agent]
    L2 --> M2
    K2 --> M2

    %% Info Advisor Path
    F3 --> G3[Sends Output to Info Advisor]
    G3 --> H3[Processes the complete chat history]
    H3 --> I3{Decides 1 of 2 Options}
    I3 --> J3[Info Not Needed]
    I3 --> K3[Info Needed]
    K3 --> L3[Vector Retrieve Info]
    J3 --> M3[Sends Output to Main Agent]
    L3 --> M3
    K3 --> M3

    %% Main Agent Re-entry
    L1 --> N[Receives and Process Input]
    M2 --> N
    M3 --> N

    N --> O{Decides 1 of 2 Options}
    O --> P[Consult Advisor Again]
    O --> Q[Sends Output]

    Q --> R[User]
