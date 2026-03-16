import os
import asyncio
from groq import Groq
from typing import List, Tuple, Any
from fastapi import HTTPException
from ..config import settings

def _transcribe_with_groq(file_path: str) -> dict:
    """Synchronous Groq SDK call for transcription"""
    client = Groq(api_key=settings.GROQ_API_KEY.strip())
    
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(file_path), audio_file.read()),
            model="whisper-large-v3-turbo",
            temperature=0,
            response_format="verbose_json",
        )
    
    return transcription

async def transcribe_audio_file(file_path: str) -> str:
    """
    Transcribes audio file using Groq SDK (whisper-large-v3-turbo, ultra-fast).
    Falls back to OpenAI Whisper API if Groq fails.
    """
    
    # --- PHASE 1: Try Groq SDK (blazing fast) ---
    if settings.GROQ_API_KEY:
        try:
            # Run synchronous Groq SDK in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _transcribe_with_groq, file_path)
            
            transcription_text = _format_whisper_result(result)
            print("DEBUG: Transcription successful via Groq SDK")
            return transcription_text
                
        except Exception as groq_err:
            print(f"DEBUG: Groq SDK failed: {str(groq_err)}. Falling back to OpenAI...")

    # --- PHASE 2: Fallback to OpenAI Whisper via httpx ---
    import httpx
    api_key = settings.OPENAI_API_KEY.strip()
    if not api_key:
        raise ValueError("Both Groq and OpenAI API keys are failing or missing.")
    
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            with open(file_path, "rb") as audio_file:
                files = {"file": audio_file}
                data = {
                    "model": "whisper-1",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "segment"
                }
                response = await client.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                print("DEBUG: Transcription successful via OpenAI (fallback)")
                return _format_whisper_result(result)
        except Exception as e:
            print(f"DEBUG: OpenAI also failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"All transcription services failed: {str(e)}")

def _format_whisper_result(result: Any) -> str:
    """Helper to format OpenAI/Groq verbose_json output (dict or object)"""
    if isinstance(result, dict):
        segments = result.get("segments", [])
        text = result.get("text", "")
    else:
        segments = getattr(result, "segments", [])
        text = getattr(result, "text", "")

    if not segments:
        return text.strip() if text else str(result)
        
    formatted_lines = []
    for segment in segments:
        if isinstance(segment, dict):
            start_seconds = int(segment.get("start", 0))
            seg_text = segment.get("text", "").strip()
        else:
            start_seconds = int(getattr(segment, "start", 0))
            seg_text = getattr(segment, "text", "").strip()
            
        mm, ss = divmod(start_seconds, 60)
        hh, mm = divmod(mm, 60)
        timestamp = f"[{hh:02d}:{mm:02d}:{ss:02d}]"
        
        if seg_text:
            formatted_lines.append(f"{timestamp} {seg_text}")
            
    return "\n".join(formatted_lines)

def clean_transcript(raw: str) -> str:
    """Strips blank lines and whitespace from each line."""
    if not raw:
        return ""
    lines = raw.split("\n")
    cleaned = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned)
