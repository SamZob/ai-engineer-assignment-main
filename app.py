from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from uuid import uuid4
import json
from pydantic import BaseModel
from typing import List, Optional
import httpx
import subprocess
from googletrans import Translator, LANGUAGES
import uvicorn
from dotenv import load_dotenv
import os


app = FastAPI()

# Mock database for storing snippets
snippets_db = []
requests_db = []
feedbacks = []

app = FastAPI()

# Load environment variables from .env file
load_dotenv()  # This assumes your .env file is in the same directory as your main app file

API_KEY = os.getenv("OPENAI_API_KEY")

"""class Snippet(BaseModel):
    id: str
    title: str
    language: str
    description: str
    description_language: str
    code: str
    feedback_code: Optional[str] = None
    improved_code: Optional[str] = None
    tests: str 
    feedback_tests: Optional[str] = None
    improved_tests: Optional[str] = None
    test_results: str
    improved_code_test_results: str"""

# Load and save functions for persistence to a JSON file
def load_snippets():
    try:
        with open("snippets.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_snippets(snippets):
    with open("snippets.json", "w") as f:
        json.dump(snippets, f)

# Generate code using the OpenAI API
async def generate_response(prompt: str, language: str):
    model_map = {
        "Python": "python",
        "JavaScript": "javascript",
        "Ruby": "ruby"
    }
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    # Adjusting the system message to be explicitly about generating code
    messages = [{"role": "system", 
                 "content": f"Code-only: Write a {model_map.get(language)} function satisfy the following request: {prompt.lower()}."}]
    
    
    data = {
        "messages": messages,
        "model": "gpt-3.5-turbo",  # Specify only 'model'
        "max_tokens": 200,
        "temperature": 0.5, # Lower temperature for more deterministic output
        "top_p": 1,
        "stop": [ "#", "//"]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        print(response.json())
        return response.json()['choices'][0]['message']['content'].strip()

async def request_chatgpt(prompt: str):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    messages = [{"role": "system", "content": prompt}]
    
    data = {
        "messages": messages,
        "model": "gpt-3.5-turbo",  # Specify only 'model'
        "max_tokens": 200,
        "temperature": 0.5, # Lower temperature for more deterministic output
        "top_p": 1,
        "stop": [ "#", "//"]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json()['choices'][0]['message']['content'].strip()
    

def process_language(input_text):
    # Create a Translator object
    translator = Translator()
    
    # Detect the language of the input text
    detected_language = translator.detect(input_text).lang

    if detected_language == 'en':
        return input_text
    
    else:
        # Translate the text to English
        translated_text = translator.translate(input_text, dest='en').text
        
        # Return the detected language and the translated text
        return translated_text

def detect_language(description: str):
    # Simple keyword-based language detection
    keywords = {
        'Python': ['python', 'py', 'pandas', 'numpy','Python'],
        'JavaScript': ['javascript', 'js', 'node', 'react', 'Javascript', 'JavaScript'],
        'Ruby': ['ruby', 'rails', 'Ruby','Rails']
    }
    for language, key_list in keywords.items():
        if any(key in description.lower() for key in key_list):
            return language
    return "Python"  # Default to Python if no specific keywords are found

#################################################################
# Snippet Management


@app.post("/generate-code/")
async def create_snippet(description: str = Form(...) ):
    snippets = load_snippets()
    new_description = process_language(description)
    language = detect_language(description)
    code = await generate_response(new_description, language)
    snippet = {
        "id": str(uuid4()),
        "title": f"Generated {language} Function",
        "language": language,
        "description": description,
        "code": code
    }
    snippets.append(snippet)
    save_snippets(snippets)
    return JSONResponse(content=snippet)

@app.get("/snippets/")
def list_snippets():
    return load_snippets()

@app.delete("/snippets/{snippet_id}")
def delete_snippet(snippet_id: str):
    snippets = load_snippets()
    snippets = [snippet for snippet in snippets if snippet["id"] != snippet_id]
    save_snippets(snippets)
    return {"message": "Snippet deleted"}

@app.get("/snippets/{snippet_id}")
def get_snippet(snippet_id: str):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if snippet:
        return snippet
    raise HTTPException(status_code=404, detail="Snippet not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port= 8000 )
