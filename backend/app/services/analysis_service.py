import json
import asyncio
from groq import Groq
from ..config import settings
from .transcription import clean_transcript

def _run_groq_streaming_sync(prompt: str) -> str:
    """
    Synchronous function for Groq Chat Completion.
    """
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing from configuration")
        
    client = Groq(api_key=settings.GROQ_API_KEY.strip())
    
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
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
        
    return full_content

def _run_groq_fallback_sync(prompt: str):
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing from configuration")
        
    client = Groq(api_key=settings.GROQ_API_KEY.strip())
    return client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a specialized JSON meeting analyst. Output ONLY raw JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

def truncate_transcript(transcript: str, max_tokens: int = 6000) -> str:
    """
    Very rough token estimation (char_count / 4) to stay under TPM limits.
    Keeps the end of the meeting primarily, as that's where most tasks/decisions are.
    """
    estimated_tokens = len(transcript) / 4
    if estimated_tokens <= max_tokens:
        return transcript
        
    # If too long, take the last chunk (most relevant for decisions/tasks)
    max_chars = max_tokens * 4
    print(f"DEBUG: Transcript too long ({int(estimated_tokens)} tokens). Truncating to last {max_chars} chars.")
    return "... [TRUNCATED] ... " + transcript[-max_chars:]

async def process_transcript_with_groq(transcript: str, meeting_title: str, host_name: str):
    """
    Processes the meeting transcript using Groq Llama 3 models with token optimization.
    """
    cleaned_transcript = clean_transcript(transcript)
    
    if not cleaned_transcript.strip():
        return {
            "tldr": "No tasks or decisions extracted due to empty transcript",
            "health_score": 0,
            "tasks": [],
            "decisions": []
        }
    
    # 8,000 TPM limit on premium model. Truncate to leave room for prompt/response.
    final_transcript = truncate_transcript(cleaned_transcript, max_tokens=5500)
    
    system_prompt = f"""Expert engineering meeting analyst. Extract precisely.
Meeting: {meeting_title} | Host: {host_name}
Team: Suman S, Likhith Gowda M, J Hemanth, Nandi Prasad K M.

TASK: Actions post-meeting. Must have action verb, clear owner, specific, bounded.
Priority: HIGH (blocking/prod), MEDIUM (important), LOW (future).
DECISION: Group conclusions/agreements. Resolved — no action needed.
CONFIDENCE: 0.9-1.0 (named+clear), 0.75-0.89 (implied), 0.5-0.74 (ambiguous), <0.5 (discard).

OUTPUT ONLY RAW JSON:
{{
  "tldr": "one sentence outcome",
  "health_score": <0-100>,
  "tasks": [{{"title": "...", "description": "...", "priority": "...", "confidence_score": <0-1>, "assignee_name": "...", "owner_emp_id": "...", "owner_dept": "...", "source_quote": "..."}}],
  "decisions": [{{"title": "...", "description": "...", "decided_by_name": "...", "source_quote": "..."}}]
}}"""

    prompt = f"{system_prompt}\n\nTRANSCRIPT:\n{final_transcript}"

    try:
        loop = asyncio.get_event_loop()
        full_content = await loop.run_in_executor(None, _run_groq_streaming_sync, prompt)
        print(f"DEBUG: Analysis complete. Prompt size: ~{int(len(prompt)/4)} tokens.")
        return _parse_ai_json(full_content)
        
    except Exception as groq_err:
        print(f"DEBUG: Premium Groq Model failed ({str(groq_err)}). Falling back...")
        try:
            # Fallback uses the same (possibly truncated) transcript
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
