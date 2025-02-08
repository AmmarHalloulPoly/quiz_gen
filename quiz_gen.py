import pymupdf
import json
import sys
from google import genai
from pydantic import BaseModel

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



common_prompt = "Do not generate questions about what the text provides or doesn't provide."

model_name = "gemini-2.0-flash"


def generate_all(text):    
    
    client = genai.Client(api_key="AIzaSyDXDxctHmdgQQhW6w25NH2-tKS3GaMUoOo")

    def generate(prompt, QuestionType):
        response = client.models.generate_content(
            model=model_name, 
            contents=f"{text}\n\n{prompt}. {common_prompt}",
            config={
                'response_mime_type': 'application/json',
                'response_schema': list[QuestionType],
            },
        )
        return json.loads(response.text)

    # print("Genrating multiple choice questions...")
    mc_questions = generate("Generate multiple choice questions based on the text above", MultipleChoiceQuestion)
    # print("Genrating correct response questions...")
    cr_questions = generate("Generate questions where the correct response is just a few words long based on the text above", CorrectResponseQuestion)
    # print("Genrating yes or no questions...")
    yn_questions = generate("Generate yes or no questions based on the text above where all the answers are no", YesNoQuestion)
    yn_questions.extend(generate("Generate yes or no questions based on the text above where all the answers are yes", YesNoQuestion))
    return {
        "multiple_choice": mc_questions,
        "correct_response": cr_questions,
        "yes_no": yn_questions,
    }


if len(sys.argv) != 2:
    print("You need to specify one pdf file.")
    sys.stdout.flush()
    sys.exit(-1)

filename = sys.argv[1]
with pymupdf.open(filename) as doc:
    text = '\n\n'.join([i.get_text() for i in doc])

print(json.dumps(generate_all(text), indent=4))
