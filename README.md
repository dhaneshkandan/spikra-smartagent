# Spikra SmartAgent - Prototype

## Overview

Spikra SmartAgent is a FastAPI-based prototype that simulates how a CRM (Customer Relationship Management) system can be enriched with AI-powered lead classification and support automation.
It uses:

- FastAPI → backend framework

- Dummy CRM Data (CSV) → to simulate leads and customer tickets

- OpenAI API → to classify lead interest, suggest follow-ups, and summarize tickets

## How to Run Locally

## 1. Clone the repo

git clone https://github.com/your-username/spikra-smartagent.git
cd spikra-smartagent

## 2. Create virtual environment

python3 -m venv venv
source venv/bin/activate # for Mac/Linux
venv\Scripts\activate # for Windows

## 3. Install dependencies

pip install -r requirements.txt

## 4. Set up environment variables

Replace your OpenAI API key:

OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-3.5-turbo

## 5. Run the FastAPI app

uvicorn app:app --reload

App will run at:
http://127.0.0.1:8000/docs

---

## Example Usage

Test the /run endpoint with:

{
"csv_path": "data/sample_leads.csv"
}

## Expected output:

{
"status": {"processed": 5, "errors": 0},
"results": [
{
"lead": {"id": "1", "name": "Asha Rao", ...},
"classification": "Hot",
"followup": "Send invoice correction immediately.",
"summary": "Customer raised issue about wrong billing."
},
...
]
}

## Problem It Solves

Businesses spend a lot of manual effort sorting customer leads and responding to tickets.
Spikra SmartAgent shows how AI + CRM automation can:

- Automatically classify leads (Hot/Medium/Cold)
- Suggest follow-ups for sales teams
- Generate summaries of customer tickets

This makes CRM systems smarter, faster, and less error-prone.
