import os
from openai import OpenAI

class AIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_API_BASE")
        )
        self.model = "gpt-5" # Default to gpt-5 as per instructions

    def generate_quiz_questions(self, topic, count=5):
        """ChatGPT ашиглан асуулт үүсгэх"""
        prompt = f"Generate {count} trivia questions about {topic} in JSON format. Each question should have: question_text, answers (list of 4 options with 'text' and 'is_correct' boolean), and difficulty (easy, medium, hard)."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a trivia expert. Return ONLY JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Error: {e}")
            return None

    def get_ai_coach_advice(self, user_stats):
        """Хэрэглэгчийн тоглолтын статистик дээр үндэслэн зөвлөгөө өгөх"""
        prompt = f"Based on these stats: {user_stats}, give a short, encouraging advice for the player in Mongolian."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful gaming coach."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Error: {e}")
            return "AI Coach одоогоор амарч байна."
