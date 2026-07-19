import openai
from flask import current_app

def generate_trivia_question(category, difficulty='medium'):
    openai.api_key = current_app.config['OPENAI_API_KEY']
    prompt = f"Generate a {difficulty} trivia question about {category} with 4 options and correct answer."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message['content']