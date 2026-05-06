import os
import google.generativeai as genAI
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genAI.configure(api_key=api_key, transport='rest')
    # Print available models for debugging
    try:
        print("--- Available Gemini Models ---")
        for m in genAI.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
        print("-------------------------------")
    except Exception as e:
        print(f"Error listing models: {e}")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    language: Optional[str] = "en"

class TranslateRequest(BaseModel):
    text: str
    target_lang: str

SYSTEM_PROMPT = """You are SkillSprint Assistant, a premium AI tutor and guide for the SkillSprint platform.
SkillSprint is a competitive coding and educational portal where students can take quizzes, participate in hackathons, and solve coding challenges.

Your goals:
1. Help students with coding questions (Python, JavaScript, C++, etc.).
2. Explain complex programming concepts simply.
3. Provide guidance on using the SkillSprint platform.
4. Be encouraging, professional, and concise.

Guidelines:
- Use Markdown for code blocks.
- Keep responses under 250 words unless asked for a deep dive.
- If the user asks about contests or quizzes, encourage them to check the dedicated pages on SkillSprint.
- Always maintain a "Premium" and "Supportive" tone.
"""

@router.post("/chat")
async def chat(request: ChatRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured on server")

    try:
        # Initialize model
        model = genAI.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT
        )

        # Prepare history for Gemini
        # Gemini expects roles to be 'user' and 'model'
        gemini_history = []
        for msg in request.history:
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.content]})

        chat_session = model.start_chat(history=gemini_history)
        
        response = chat_session.send_message(request.message)
        
        return {
            "response": response.text,
            "status": "success"
        }
    except Exception as e:
        print(f"DEBUG: Gemini Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate")
async def translate(request: TranslateRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured on server")

    try:
        model = genAI.GenerativeModel("gemini-2.5-flash")
        prompt = f"Translate the following text to {request.target_lang}. Only return the translated text, nothing else:\n\n{request.text}"
        
        response = model.generate_content(prompt)
        
        return {
            "translated_text": response.text.strip(),
            "status": "success"
        }
    except Exception as e:
        print(f"DEBUG: Gemini Translate Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
