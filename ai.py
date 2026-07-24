from openai import OpenAI
import json

import os

# Helper to load .env file manually
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_env()

def analyse_resume(resume_text, user_goal):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if groq_api_key:
        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        model_name = "llama-3.1-8b-instant"
    elif openai_api_key:
        client = OpenAI(api_key=openai_api_key)
        model_name = "gpt-4o-mini"
    else:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": "No API Key is set. Please set GROQ_API_KEY or OPENAI_API_KEY in your .env file."
        }
    prompt = f"""
You are a senior software engineer and hiring manager.
Evaluate the resume based on the user's career goal.
User Goal:
{user_goal}
STRICT RULES:
- Extract only skills relevant to this goal.
- Remove irrelevant skills.
- Identify real skill gaps.
- Generate roadmap only for missing skills.
- Make output different based on the user's goal.
- Return ONLY valid JSON. No markdown.

Required JSON format:
{{
    "skills": [],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}
Resume:
{resume_text}
"""
    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.3,
            messages=[
                {"role": "system","content": "You are a strict hiring manager."},
                {"role": "user","content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()

        # Remove markdown JSON wrapper if AI returns it
        if "```json" in content:
            content = content.replace("```json", "")
            content = content.replace("```", "")
        start = content.find("{")
        end = content.rfind("}") + 1
        json_data = content[start:end]
        return json.loads(json_data)
    except Exception as e:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }

def evaluate_answer(question, answer):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if groq_api_key:
        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        model_name = "llama-3.1-8b-instant"
    elif openai_api_key:
        client = OpenAI(api_key=openai_api_key)
        model_name = "gpt-4o-mini"
    else:
        return {"error": "API Key is not configured."}

    prompt = f"""
You are an expert technical interviewer. Evaluate the candidate's answer to this question:
Question: {question}
Candidate's Answer: {answer}

Provide feedback including:
1. A score from 0 to 100.
2. Strengths of the answer.
3. Constructive feedback on how to improve.
4. An exemplar model answer.

Return ONLY valid JSON.
Required JSON format:
{{
    "score": 85,
    "strengths": "Your explanation is...",
    "improvements": "You should add...",
    "exemplar": "A model answer would be..."
}}
"""
    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are a professional hiring manager."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.replace("```json", "")
            content = content.replace("```", "")
        start = content.find("{")
        end = content.rfind("}") + 1
        json_data = content[start:end]
        return json.loads(json_data)
    except Exception as e:
        return {"error": str(e)}