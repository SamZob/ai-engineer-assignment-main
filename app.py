from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from uuid import uuid4
import json
import httpx
import re
import subprocess
from googletrans import Translator
import uvicorn
from dotenv import load_dotenv
import os

# Initialize the FastAPI app
app = FastAPI()

# Serve static files from the 'static' directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Environment setup
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# Mock database
snippets_db = []
requests_db = []
feedbacks = []


# Root route to serve the frontend HTML
@app.get("/")
async def read_root():
    return FileResponse("static/design.html")


# Data model class for Snippets (commented as it's not active)
# class Snippet(BaseModel):
#     id: str
#     title: str
#     language: str
#     description: str
#     description_language: str
#     code: str
#     feedback_code: Optional[str] = None
#     improved_code: Optional[str] = None
#     tests: str
#     feedback_tests: Optional[str] = None
#     improved_tests: Optional[str] = None
#     test_results: str
#     improved_code_test_results: str


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


# Helper function to generate a code response from the OpenAI API
async def generate_response(prompt: str, language: str):
    model_map = {"Python": "python", "JavaScript": "javascript", "Ruby": "ruby"}
    headers = {"Authorization": f"Bearer {API_KEY}"}
    messages = [
        {
            "role": "system",
            "content": f"Code-only: Write a {model_map.get(language)} function to satisfy: {prompt.lower()}.",
        }
    ]
    data = {
        "messages": messages,
        "model": "gpt-3.5-turbo",
        "max_tokens": 200,  # To prevent prompt injection
        "temperature": 0.5,  # Lower temperature for more deterministic output and prevent prompt injection
        "top_p": 1,
        "stop": ["#", "//"],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions", json=data, headers=headers
        )
        return response.json()["choices"][0]["message"]["content"].strip()


# Helper function to generate response from the OpenAI API
async def request_chatgpt(prompt: str):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    messages = [{"role": "system", "content": prompt}]

    data = {
        "messages": messages,
        "model": "gpt-3.5-turbo",  # Specify only 'model'
        "max_tokens": 200,  # To prevent prompt injection
        "temperature": 0.5,  # Lower temperature for more deterministic output and prevent prompt injection
        "top_p": 1,
        "stop": ["#", "//"],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json()["choices"][0]["message"]["content"].strip()


# Additional utility functions and routes
def process_language(input_text):
    """Detects and translates the input text to English if it is not in English."""
    translator = Translator()
    detected_language = translator.detect(input_text).lang
    if detected_language == "en":
        return input_text
    else:
        translated_text = translator.translate(input_text, dest="en").text
        return translated_text


def detect_language(description: str):
    """Detects the programming language of the given description using keyword matching."""
    keywords = {
        "Python": ["python", "py", "pandas", "numpy", "Python"],
        "JavaScript": ["javascript", "js", "node", "react", "Javascript", "JavaScript"],
        "Ruby": ["ruby", "rails", "Ruby", "Rails"],
    }
    for language, key_list in keywords.items():
        if any(key in description.lower() for key in key_list):
            return language
    return "Python"  # Default to Python if no specific keywords are found


# Route to generate code for a specific snippet
@app.post("/generate-code/{snippet_id}")
async def generate_code(snippet_id: str, description: str = Form(...)):
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    snippet["description"] = description
    new_description = process_language(description)
    language = detect_language(new_description)
    snippet["code"] = await generate_response(new_description, language)
    snippet["language"] = language
    snippet["title"] = await request_chatgpt(
        f"Title only: Generate a title for: {description}. Keep it simple and concise"
    )
    save_snippets(snippets)
    return JSONResponse(content=snippet)


# Route to create a new code snippet
@app.post("/create-snippet/")
async def create_snippet():
    snippets = load_snippets()
    snippet = {
        "id": str(uuid4()),
        "description": None,
        "language": None,
        "title": None,
        "code": None,
    }
    snippets.append(snippet)
    save_snippets(snippets)
    return JSONResponse(content=snippet)


# Routes for managing and testing code snippets
@app.get("/snippets/")
def list_snippets():
    """Returns a list of all stored code snippets."""
    return load_snippets()


@app.get("/snippets/{snippet_id}")
def get_snippet(snippet_id: str):
    """Returns a specific snippet by ID, or a 404 error if not found."""
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if snippet:
        return snippet
    raise HTTPException(status_code=404, detail="Snippet not found")


@app.delete("/snippets/{snippet_id}")
def delete_snippet(snippet_id: str):
    """Deletes a snippet by ID and updates the database."""
    snippets = load_snippets()
    snippets = [snippet for snippet in snippets if snippet["id"] != snippet_id]
    save_snippets(snippets)
    return {"message": "Snippet deleted"}


# Route for feedback and improved code
@app.post("/snippets/{snippet_id}/improve-code/")
async def improve_code(snippet_id: str, feedback: str = Form(...)):
    """Improves the code of a snippet based on given feedback and updates the snippet."""
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    snippet["feedback_code"] = feedback
    prompt = f"Code only: Improve the following {snippet['language']} code based on this feedback: '{feedback}'. Here is the original code:\n{snippet['code']}\n Let's think step by step"
    improved_code = await request_chatgpt(prompt)
    snippet["improved_code"] = improved_code
    save_snippets(snippets)
    return {"message": "Code improved", "code": improved_code}


# Routes to generate and improve tests
@app.post("/snippets/{snippet_id}/generate-tests/")
async def generate_tests(snippet_id: str):
    """Generates test cases for the improved code of a snippet."""
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    improved_code = snippet["improved_code"]
    prompt = f"Tests only: Generate test cases for the following {snippet['language']} code:\n '{improved_code}'.The format should respect the following regex expression: r'Test case \d+:\nInput:\s*(.*?)\nExpected output:\s*(.*?)(?=\n\nTest case |\Z)'."
    tests = await request_chatgpt(prompt)
    snippet["tests"] = tests
    save_snippets(snippets)
    return {"message": "Tests generated", "tests": tests}


@app.post("/snippets/{snippet_id}/improve-tests/")
async def improve_tests(snippet_id: str, feedback: str = Form(...)):
    """Improves test cases for a snippet based on feedback."""
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    snippet["feedback_tests"] = feedback
    prompt = f"Tests only: Improve the following test cases for the {snippet['language']} code based on this feedback: '{feedback}'. Here are the test cases:\n{snippet['tests']} The format should respect the following regex expression: r'Test case \d+:\nInput:\s*(.*?)\nExpected output:\s*(.*?)(?=\n\nTest case |\Z)'."
    improved_tests = await request_chatgpt(prompt)
    snippet["improved_tests"] = improved_tests
    save_snippets(snippets)
    return {"message": "Tests improved", "tests": improved_tests}


# Helper function to clean output
def clean_code(code):
    """Removes Markdown code fences from the provided code string."""
    if "```python" in code:
        return code.replace("```python", "").replace("```", "").strip()
    else:
        return code


# Helper function to run tests
def parse_and_execute_tests(code, test_cases):
    """Prepares and generates test execution scripts for given code and test cases."""
    cleaned_code = clean_code(code)
    functions = re.findall(
        r"def (\w+)\(", cleaned_code
    )  # Extract function names from the code
    test_script = f"{cleaned_code}\nimport sys\n"  # Prepare the script with imported sys for error handling
    test_case_pattern = re.compile(
        r"Test case \d+:\nInput:\s*(.*?)\nExpected output:\s*(.*?)(?=\n\nTest case |\Z)",
        re.DOTALL,
    )
    matches = test_case_pattern.findall(
        test_cases
    )  # Find all matches for the specified test case pattern

    for function_name in functions:
        for inputs, expected_output in matches:
            # Adjust inputs to remove surrounding parentheses if present and add them to the test script
            if "(" or ")" in inputs:
                inputs = inputs.strip("()")
            test_script += f"""
try:
    result = {function_name}({inputs})
    expected = {expected_output}
    print("\\nRunning test for function: {function_name} with inputs: {inputs}")
    print("Expected output: {expected_output}, got:", result)
    assert result == expected, "Test failed: expected {expected_output}, got " + str(result)
except Exception as e:
    print("Test for {function_name} failed due to an error:", str(e))
    sys.exit(1)
"""
    return test_script


# Routes to run tests and regenerate code
@app.post("/snippets/{snippet_id}/test/")
async def test_snippet(snippet_id: str):
    """Executes predefined tests on a specified snippet's code."""
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if not snippet or snippet["language"] != "Python":
        raise HTTPException(status_code=404, detail="Snippet not found or not Python")

    full_script = parse_and_execute_tests(
        snippet["improved_code"], snippet["improved_tests"]
    )
    try:
        # Execute the test script and capture the output
        result = subprocess.run(
            ["python", "-c", full_script], text=True, capture_output=True, check=True
        )
        snippet["test_results"] = {"Test": "passed", "results": result.stdout}
        save_snippets(snippets)
        return {"message": "Tests passed", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        snippet["test_results"] = {"Test": "failed", "results": e.stdout}
        save_snippets(snippets)
        return {"message": "Tests failed", "output": e.stdout}


@app.post("/snippets/{snippet_id}/regenerate-code/")
async def regenerate_code(snippet_id: str):
    """Regenerates code for a snippet based on test results that indicated failure."""
    snippets = load_snippets()
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if snippet:
        results = snippet["test_results"]
        if results and results["Test"] == "failed":
            prompt = f"code only: Improve the following {snippet['language']} code based on the test results: '{results['results']}'. Here is the code: \n{snippet['improved_code']}"
            regenerated_code = await request_chatgpt(prompt)
            snippet["regenerated_code"] = regenerated_code
            save_snippets(snippets)
            return {"message": "Code regenerated", "code": regenerated_code}
        raise HTTPException(
            status_code=404, detail="Tests did not fail or results not available"
        )
    raise HTTPException(status_code=404, detail="Snippet not found")


# Entry point to run the app with Uvicorn, specifying host and port
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
