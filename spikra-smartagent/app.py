# app.py
import os, time, csv, traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment
load_dotenv()
USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() in ("1","true","yes")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Optional OpenAI client (lazy init)
client = None
if USE_OPENAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("USE_OPENAI is true but OPENAI_API_KEY is not set in .env")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        raise RuntimeError("Failed to import OpenAI client: " + str(e))

app = FastAPI(title="Spikra SmartAgent Prototype")

class RunRequest(BaseModel):
    csv_path: str = "data/sample_leads.csv"

# ---------- prompts / helpers ----------
def classify_prompt(lead):
    return f"""You are a CRM assistant. Based on these fields, classify the lead into exactly one word: Hot, Warm, or Cold.
Name: {lead['name']}
Company: {lead['company']}
Interest: {lead['interest']}
Ticket: {lead['ticket']}

Output only one word: Hot or Warm or Cold.
"""

def followup_prompt(lead):
    return f"""Write a short (2-3 sentence) personalized follow-up email for {lead['name']} at {lead['company']} based on interest level: {lead['interest']}. Keep it friendly and mention the company's name once."""

def summarize_prompt(lead):
    return f"Summarize the customer ticket in one short sentence.\nTicket: {lead['ticket']}"

# ---------- Mock implementations (guaranteed to work offline) ----------
def mock_classify(lead):
    it = str(lead.get("interest","")).lower()
    if "high" in it: return "Hot"
    if "medium" in it or "med" in it: return "Warm"
    return "Cold"

def mock_followup(lead):
    return f"Hi {lead.get('name')}, thanks for your interest in {lead.get('company')}. I'd be happy to schedule a quick call to discuss next steps."

def mock_summarize(lead):
    t = str(lead.get("ticket","")).strip()
    return t[:120] + ("..." if len(t)>120 else "") if t else ""

# ---------- OpenAI wrapper (new SDK) ----------
def openai_classify(lead):
    prompt = classify_prompt(lead)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=0,
        max_tokens=6
    )
    text = resp.choices[0].message.content.strip().split()[0].capitalize()
    if text in ("Hot","Warm","Cold"):
        return text
    return mock_classify(lead)

def openai_followup(lead):
    prompt = followup_prompt(lead)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=0.3,
        max_tokens=150
    )
    return resp.choices[0].message.content.strip()

def openai_summarize(lead):
    prompt = summarize_prompt(lead)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=0,
        max_tokens=60
    )
    return resp.choices[0].message.content.strip()

# ---------- Main processing ----------
@app.get("/")
def home():
    return {"message": "Spikra SmartAgent Prototype Running", "use_openai": USE_OPENAI}

@app.post("/run")
def run_agent(req: RunRequest):
    csv_path = req.csv_path
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail=f"CSV not found: {csv_path}")

    results = []
    processed = 0
    errors = 0
    total_latency = 0.0
    start_total = time.time()

    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            lead = {
                "id": row.get("id",""),
                "name": row.get("name",""),
                "email": row.get("email",""),
                "company": row.get("company",""),
                "interest": row.get("interest",""),
                "ticket": row.get("ticket","")
            }
            item = {"lead": lead}
            t0 = time.time()
            try:
                if USE_OPENAI:
                    # Use OpenAI functions (may raise if quota exhausted)
                    category = openai_classify(lead)
                    followup = openai_followup(lead) if category in ("Hot","Warm") else ""
                    ticket_summary = openai_summarize(lead) if lead["ticket"].strip() else ""
                else:
                    # Mock
                    category = mock_classify(lead)
                    followup = mock_followup(lead) if category in ("Hot","Warm") else ""
                    ticket_summary = mock_summarize(lead)
                latency = time.time() - t0
                total_latency += latency
                processed += 1
                item.update({
                    "category": category,
                    "followup": followup,
                    "ticket_summary": ticket_summary,
                    "latency_sec": round(latency, 3)
                })
            except Exception as e:
                errors += 1
                item.update({"error": str(e), "trace": traceback.format_exc()})
            results.append(item)

    status = {
        "processed": processed,
        "errors": errors,
        "avg_latency_sec": round((total_latency/processed) if processed else 0, 3),
        "total_time_sec": round(time.time()-start_total, 3)
    }
    return {"status": status, "results": results}
