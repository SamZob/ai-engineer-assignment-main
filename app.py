from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from uuid import uuid4
import json
from pydantic import BaseModel
from typing import List, Optional
import httpx
import re
import subprocess
from googletrans import Translator, LANGUAGES
import uvicorn
from dotenv import load_dotenv
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Directory where your design.html and other static files are stored
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('static/design.html')

# Mock database for storing snippets
snippets_db = []
requests_db = []
feedbacks = []

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
# Snippet generation and Management

@app.post("/create-snippet/")
async def create_snippet():
    snippets = load_snippets()
    snippet = {
        "id": str(uuid4()),
        "description": None,
        "language": None,  # Language will be set after code generation
        "title": None,     # Title will be set after code generation
        "code": None       # Code will be generated later
    }
    snippets.append(snippet)
    save_snippets(snippets)
    return JSONResponse(content=snippet)

@app.post("/generate-code/{snippet_id}")
async def generate_code(snippet_id: str, description: str = Form(...)):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    
    snippet["description"] = description
    # Process the description to determine the language and generate code
    new_description = process_language(description)
    language = detect_language(new_description)
    code = await generate_response(new_description, language)
    
    # Generate title based on description
    title_prompt = f"Title only: Generate title based on the folowing user description: {description}. The title must not exceed 10 words and should be doubles quoted or single quoted "
    # Update the snippet with the generated code, language, and a dynamic title
    snippet["code"] = code
    snippet["language"] = language
    snippet["title"] = await request_chatgpt(title_prompt)
    save_snippets(snippets)
    return JSONResponse(content=snippet)

@app.get("/snippets/")
def list_snippets():
    return load_snippets()

@app.delete("/snippets/{snippet_id}")
def delete_snippet(snippet_id: str) :
    snippets = load_snippets()
    snippets = [snippet for snippet in snippets if snippet["id"] != snippet_id]
    save_snippets(snippets)
    return {"message": "Snippet deleted"}

@app.get("/snippets/{snippet_id}")
def get_snippet(snippet_id: str ):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if snippet:
        return snippet
    raise HTTPException(status_code=404, detail="Snippet not found")

#################################################################
# Feedback and improved code

# Route to improve code after giving feedback on code
@app.post("/snippets/{snippet_id}/improve-code/")
async def improve_code(snippet_id: str, feedback: str = Form(...)):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    # Store feedback and immediately use it to improve the code
    snippet['feedback_code'] = feedback

    # Assume you're using feedback to generate a prompt to improve code
    prompt = f"Code only: Improve the following {snippet['language']} code based on this feedback: '{feedback}'. Here is the original code:\n{snippet['code']}"
    improved_code = await request_chatgpt(prompt)

    # Update snippet with the improved code
    snippet['improved_code'] = improved_code
    save_snippets(snippets)

    return {"message": "Code improved", "code": improved_code}


################################################################################
# Generate tests / feedbacks / improved tests

@app.post("/snippets/{snippet_id}/generate-tests/")
async def generate_tests(snippet_id: str):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if snippet:
        improved_code = snippet['improved_code']
        prompt = f"Tests only: Generate test cases for the following {snippet['language']} code:\n '{improved_code}'. The format should respect the following regex expression: r'Test case \d+:\nInput:\s*(.*?)\nExpected output:\s*(.*?)(?=\n\nTest case |\Z)' "
        tests = await request_chatgpt(prompt)
        snippet['tests'] = tests
        save_snippets(snippets)
        return {"message": "tests generated", "tests": tests}
    raise HTTPException(status_code=404, detail="Snippet not found")


@app.post("/snippets/{snippet_id}/improve-tests/")
async def improve_tests(snippet_id: str, feedback:str = Form(...)):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)

    if snippet:
        snippet['feedback_tests'] = feedback
        if snippet['feedback_tests']:
            prompt = f"Tests only: Improve the following test cases for the {snippet['language']} code based on the feedback: '{snippet['feedback_tests']}'. Here are the test cases:\n{snippet['tests']}"
            improved_tests = await request_chatgpt(prompt)
            snippet['improved_tests'] = improved_tests
            save_snippets(snippets)
            return {"message": "Tests improved", "tests": improved_tests}
    raise HTTPException(status_code=404, detail="Snippet not found")


def clean_code(code):
    # Remove markdown code fences if present
    return code.replace("```python", "").replace("```", "").strip()


def parse_and_execute_tests(code, test_cases):
    # Clean and prepare the code
    cleaned_code = clean_code(code)
    # Find all functions in the code (assuming simple function definitions)
    functions = re.findall(r"def (\w+)\(", cleaned_code)
    
    test_script = f"{cleaned_code}\n"
    test_case_pattern = re.compile(r"Test case \d+:\nInput:\s*(.*?)\nExpected output:\s*(.*?)(?=\n\nTest case |\Z)", re.DOTALL)
    matches = test_case_pattern.findall(test_cases)
    
    for match in matches:
        inputs, expected_output = match
        if functions:
            # Assuming the first function is the one to test
            function_name = functions[0]
            test_script += f"""
print("Running test with inputs: {inputs} with expected output: {expected_output}")
result = {function_name}({inputs})
print("got" + str(result))
assert result == {expected_output}, f"Test failed: expected {expected_output}, got {{result}}"
"""
    return test_script

@app.post("/snippets/{snippet_id}/test/")
async def test_snippet(snippet_id: str):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)

    if snippet and snippet["language"] == "Python":
        full_script = parse_and_execute_tests(snippet['improved_code'], snippet['improved_tests'])

        try:
            result = subprocess.run(['python', '-c', full_script], text=True, capture_output=True, check=True)
            snippet["test_results"] = {"Test": "passed", "results":result.stdout} 
            save_snippets(snippets)
            return {"message": "Tests passed", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            snippet["test_results"] = {"Test": "failed", "results":e.output}
            save_snippets(snippets)
            return {"message": "Tests failed", "output": e.output}
    else:
        raise HTTPException(status_code=404, detail="Snippet not found or not Python")
    

@app.post("/regenerate-code/")
async def regenerate_code(snippet_id: str = Form(...)):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if snippet:
        results = snippet['test_results']
        if results:
            if results['Test'] == 'failed':
            
                prompt = f"code only: Improve the following {snippet['language']} code based on the test results: '{results['results']}'. Here is the code: \n{snippet['improved_code']}"
                regenerate_code = await request_chatgpt(prompt)
                snippet['regenerated_code'] = regenerate_code
                save_snippets(snippets)
                return {"message": "Code regenerated", "code": regenerate_code}
            
            raise HTTPException(status_code=404, detail="Tests did not fail")
        raise HTTPException(status_code=404, detail="Tests results not found")
    raise HTTPException(status_code=404, detail="Snippet not found")

# Run app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port= 8000 )