"""AI-powered question generator using OpenAI"""
import json
import requests
from flask import current_app

def generate_trivia_question(category_name="General Knowledge", difficulty="medium"):
    """
    OpenAI API-аар trivia асуулт үүсгэх.
    Алдааны үед яагаад амжилтгүй болсныг логт бичнэ.
    """
    api_key = current_app.config.get('OPENAI_API_KEY')

    # === API Key шалгалт ===
    if not api_key or api_key == 'your-api-key-here':
        current_app.logger.error("❌ OPENAI_API_KEY is missing or still set to default.")
        return None

    # === Prompt (илүү тодорхой, давхардлыг багасгах) ===
    prompt = (
        f"Generate a unique and interesting {difficulty} difficulty trivia question about '{category_name}'. "
        "The question should be different from typical ones and creative.\n\n"
        "Return ONLY a valid JSON object with exactly these keys:\n"
        '"question": "the question text",\n'
        '"correct_answer": "the correct answer",\n'
        '"wrong_answers": ["wrong1", "wrong2", "wrong3"]\n\n'
        "Do NOT include any extra text, markdown, or explanation. "
        "Ensure the JSON is valid."
    )

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=current_app.config.get('OPENAI_API_BASE')
        )
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()

        # Заримдаа ```json ... ``` гэж ирдэг
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        result = json.loads(content)

        # Шаардлагатай түлхүүрүүд байгаа эсэх
        if not all(k in result for k in ('question', 'correct_answer', 'wrong_answers')):
            current_app.logger.error("❌ AI returned incomplete data.")
            return None

        return result

    except requests.exceptions.Timeout:
        current_app.logger.error("❌ OpenAI request timed out.")
        return None
    except json.JSONDecodeError as e:
        current_app.logger.error(f"❌ Failed to parse AI response as JSON: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"❌ Unexpected error in AI generator: {e}")
        return None