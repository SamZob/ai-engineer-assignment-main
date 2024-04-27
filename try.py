from dotenv import load_dotenv
import os
from googletrans import Translator, LANGUAGES

load_dotenv()  # This assumes your .env file is in the same directory as your main app file

API_KEY = os.getenv("OPENAI_API_KEY")

print(API_KEY)


# Generate code using the OpenAI API
# """ADD NO GENERATED TEXT WITH GENERATED CODE"""
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
    messages = [{"role": "system", "content": f"Code-only: Write a {model_map.get(language)} function satisfy this user request: {prompt.lower()}."}]
    
    
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

import asyncio
import httpx

async def test_generate_response():
    prompt = "Write a simple Python function to add two numbers."
    language = "Python"
    result = await generate_response(prompt, language)
    print(f"Generated code: {result}")

# Run the test
asyncio.run(test_generate_response())

async def test_request_chatgpt():
    prompt = "Explain the concept of recursion in computer science."
    result = await request_chatgpt(prompt)
    print(f"ChatGPT Response: {result}")

# Run the test
# asyncio.run(test_request_chatgpt())

def test_process_language():
    input_text = "Hola, ¿cómo estás?"
    result = process_language(input_text)
    print(f"Processed text: {result}")

# test_process_language()

def test_detect_language():
    descriptions = [
        "Using pandas and numpy for data analysis.",
        "Building reactive interfaces with react.",
        "Developing scalable apps on rails."
    ]
    for description in descriptions:
        language = detect_language(description)
        print(f"Description: '{description}' - Detected language: {language}")

test_detect_language()
