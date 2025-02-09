import json
import sys
import random
from typing import Annotated, Union, Optional

import pymupdf
from google import genai
from pydantic import BaseModel
from fastapi import FastAPI, Form, UploadFile

class Choice(BaseModel):
    text: str
    is_correct: bool


class MultipleChoiceQuestion(BaseModel):
  question: str
  choices: list[Choice]

class YesNoQuestion(BaseModel):
  question: str
  is_correct: bool

class CorrectResponseQuestion(BaseModel):
  question: str
  correct_response: str


class GenerateForm(BaseModel):
    gemimi_token: str
    user_prompt: str
    multiple_choice_count: int
    correct_response_count: int
    yes_no_count: int

common_prompt = "Do not ask about whether or not an information is stated in the text above."
model_name = "gemini-2.0-flash"


def generate_all(text, gemimi_token, user_prompt, multiple_choice_count, correct_response_count, yes_no_count):    
    
    client = genai.Client(api_key=gemimi_token)

    def generate(prompt, QuestionType):
        response = client.models.generate_content(
            model=model_name, 
            contents=f"{text}\n\n{prompt}\n{user_prompt}\n{common_prompt}",
            config={
                'response_mime_type': 'application/json',
                'response_schema': QuestionType,
            },
        )
        return json.loads(response.text)

    return {
        "multiple_choice": [generate("Generate a multiple choice question based on informartion in the text above", MultipleChoiceQuestion) for i in range(multiple_choice_count)],

        "correct_response": [generate("Generate a question where the correct response is just a few words long based on informartion in the text above", CorrectResponseQuestion) for i in range(correct_response_count)],

        "yes_no": [generate(f"Generate a yes or no question based on informartion in the text above where all the answers are {random.choice(["yes", "no"])}", YesNoQuestion) for i in range(yes_no_count)]
    }


app = FastAPI()

@app.post("/generate")
def generate_api(file: UploadFile, form: GenerateForm):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type")
    doc = pymupdf.Document(stream=file.file.read(), filetype="pdf")
    text = "\n\n".join([i.get_text() for i in doc])
    return generate_all(text, form.gemimi_token, form.user_prompt, form.multiple_choice_count, form.correct_response_count, form.yes_no_count)
