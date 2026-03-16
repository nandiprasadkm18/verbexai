import json
import asyncio
from groq import Groq
from ..config import settings
from .transcription import clean_transcript

def _run_groq_streaming_sync(prompt: str) -> str:
    """
    Synchronous function implementing the exact logic from the user.
    Runs inside a thread executor to avoid blocking the event loop.
    """
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing from configuration")
        
    client = Groq(api_key=settings.GROQ_API_KEY.strip())
    
    # EXACT logic from user snippet
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=1,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        stream=True,
        stop=None
    )
    
    full_content = ""
    for chunk in completion:
        content = chunk.choices[0].delta.content or ""
        full_content += content
        print(content, end="", flush=True)
        
    return full_content

def _run_groq_fallback_sync(prompt: str):
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing from configuration")
        
    client = Groq(api_key=settings.GROQ_API_KEY.strip())
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a specialized JSON meeting analyst. Output ONLY raw JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

async def process_transcript_with_gemini(transcript: str, meeting_title: str, host_name: str):
    """
    Processes the meeting transcript using the premium Groq model (openai/gpt-oss-120b).
    Uses the EXACT logic, parameters, and streaming requested by the user.
    """
    cleaned_transcript = clean_transcript(transcript)
    
    # Check for empty transcript
    if not cleaned_transcript.strip():
        print("DEBUG: Empty transcript detected. Returning placeholder.")
        return {
            "tldr": "No tasks or decisions extracted due to empty transcript",
            "health_score": 0,
            "tasks": [],
            "decisions": []
        }
    
    system_prompt = f"""
You are an expert meeting analyst for engineering teams.
Read the transcript and extract all tasks and decisions precisely.
Meeting: {meeting_title}
Host: {host_name}

TEAM MEMBERS (Assign tasks to these people if mentioned):
1. Suman S
2. Likhith Gowda M 
3. J Hemanth
4. Nandi Prasad K M

TASK = something someone must DO after this meeting ends
- Must have an action verb: fix, build, write, implement, review, update, create, test, deploy
- Must have an owner who committed to it or was assigned it
- Must be specific and bounded, not vague like "think about it"
- Priority HIGH = deadline mentioned, blocking others, or production issue
- Priority MEDIUM = important but no hard deadline
- Priority LOW = nice to have or future consideration

DECISION = something the group CONCLUDED and AGREED ON during the meeting
- Uses words like: decided, agreed, going with, confirmed, final call, approved, we will
- Already resolved — no further action needed from anyone
- Clearly different from a task — nobody needs to DO anything new

CONFIDENCE SCORE:
0.90-1.00 = named owner + clear specific action + explicit in transcript
0.75-0.89 = clear action + owner strongly implied from context
0.50-0.74 = action or owner is ambiguous — needs human review
0.00-0.49 = vague or speculative — will be discarded automatically

Return ONLY raw valid JSON. Zero markdown. Zero explanation. Zero preamble.
Exact structure:
{{
  "tldr": "one sentence capturing the single most important outcome",
  "health_score": <float 0 to 100>,
  "tasks": [
    {{
      "title": "<clear action title, under 10 words>",
      "description": "<1-2 sentences of context from the meeting>",
      "priority": "high or medium or low",
      "confidence_score": <float 0.0 to 1.0>,
      "assignee_name": "<full name of the person responsible, null if unknown>",
      "owner_emp_id": "<employee ID if mentioned (e.g. BE102), null if unknown>",
      "owner_dept": "<department name if mentioned (e.g. Backend Engineering), null if unknown>",
      "source_quote": "<exact words from transcript proving this task and ownership>"
    }}
  ],
  "decisions": [
    {{
      "title": "<clear decision title, under 10 words>",
      "description": "<1-2 sentences of what was decided and why>",
      "decided_by_name": "<name of person who announced or made the decision, null if group>",
      "source_quote": "<exact words from transcript proving this decision>"
    }}
  ]
}}
"""

    prompt = f"{system_prompt}\n\nTRANSCRIPT:\n{cleaned_transcript}"

    try:
        # Run the synchronous user code in a separate thread so it doesn't block FastAPI
        loop = asyncio.get_event_loop()
        full_content = await loop.run_in_executor(None, _run_groq_streaming_sync, prompt)
            
        print("\nDEBUG: AI Analysis complete via Groq Streaming.")
        return _parse_ai_json(full_content)
        
    except Exception as groq_err:
        print(f"\nDEBUG: Premium Groq Model failed: {str(groq_err)}")
        # Simple fallback if the premium model is unavailable or errors out
        try:
            loop = asyncio.get_event_loop()
            fallback_completion = await loop.run_in_executor(None, _run_groq_fallback_sync, prompt)
            return _parse_ai_json(fallback_completion.choices[0].message.content.strip())
        except Exception as e2:
            print(f"DEBUG: All fallback models failed: {str(e2)}")
            return {
                "tldr": f"AI Extraction Error: {str(groq_err)}",
                "health_score": 0,
                "tasks": [],
                "decisions": []
            }

def _parse_ai_json(text: str) -> dict:
    """Helper to clean and parse JSON from AI response"""
    text = text.strip()
    # Strip markdown fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if "```" in text:
        text = text.split("```")[0]
    
    text = text.strip()
    
    try:
        data = json.loads(text)
        if not isinstance(data.get("tasks"), list): data["tasks"] = []
        if not isinstance(data.get("decisions"), list): data["decisions"] = []
        return data
    except json.JSONDecodeError:
        print(f"DEBUG: Failed to parse JSON. Raw start: {text[:100]}")
        return {
            "tldr": "Parsing Error: The AI did not return a valid JSON structure.",
            "health_score": 0,
            "tasks": [],
            "decisions": []
        }
