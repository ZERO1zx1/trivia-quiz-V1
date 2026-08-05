"""AI Coach - Хувийн дасгалжуулагч (Chapter: AI Coach)
Analyzes player's weak categories and generates personalized advice.
"""
import json
from flask import current_app
from app.extensions import db


def get_user_weak_categories(user_id):
    """Get user's weakest and strongest categories based on history."""
    from app.models.user import User
    user = User.query.get(user_id)
    if not user:
        return None

    category_stats = {}
    try:
        if user.category_stats and user.category_stats != '{}':
            category_stats = json.loads(user.category_stats)
    except (json.JSONDecodeError, TypeError):
        category_stats = {}

    return category_stats


def generate_coach_advice(user_id):
    """Generate AI-powered coaching advice based on player performance.

    Uses OpenAI GPT to analyze the player's weak and strong categories
    and provide motivational advice.
    """
    from app.models.user import User
    from app.models.question import Category

    user = User.query.get(user_id)
    if not user:
        return None

    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key or api_key == 'your-actual-api-key':
        # Fallback: use built-in template-based advice
        return _fallback_coach_advice(user)

    # Get category performance stats
    category_stats = {}
    try:
        if user.category_stats and user.category_stats != '{}':
            category_stats = json.loads(user.category_stats)
    except (json.JSONDecodeError, TypeError):
        category_stats = {}

    # Build category analysis
    category_analysis = []
    for cat_name, stats in category_stats.items():
        if isinstance(stats, dict):
            total = stats.get('total', 0)
            correct = stats.get('correct', 0)
            if total > 0:
                accuracy = (correct / total) * 100
                category_analysis.append({
                    'category': cat_name,
                    'accuracy': round(accuracy, 1),
                    'total': total,
                    'correct': correct
                })

    if not category_analysis:
        return _fallback_coach_advice(user)

    # Sort by accuracy
    category_analysis.sort(key=lambda x: x['accuracy'])
    weakest = category_analysis[0]
    strongest = category_analysis[-1]

    # Build prompt for OpenAI
    categories_text = "\n".join([
        f"- {c['category']}: {c['accuracy']}% accuracy ({c['correct']}/{c['total']} correct)"
        for c in category_analysis
    ])

    prompt = (
        f"Тоглогчийн асуултын тоглоомын статистикийг шинжилж, "
        f"урам зориг өгөх 2 өгүүлбэр зөвлөгөө гаргаж өг.\n\n"
        f"Тоглогч: {user.username} (Level {user.level})\n"
        f"Нийт тоглолт: {user.games_played}\n"
        f"Нийт зөв хариулт: {user.total_correct}/{user.total_questions} ({user.accuracy:.1f}%)\n\n"
        f"Категорийн нарийвчилсан:\n{categories_text}\n\n"
        f"Хамгийн сул: {weakest['category']} ({weakest['accuracy']}%)\n"
        f"Хамгийн хүчтэй: {strongest['category']} ({strongest['accuracy']}%)\n\n"
        f"Зөвхөн Монгол хэл дээр 2 өгүүлбэртэй зөвлөгөө бич. "
        f"Хүмүүстэй харилцах, урам зориг өгөх байдлаар бич."
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
            temperature=0.8,
            max_tokens=300
        )
        advice = response.choices[0].message.content.strip()
        return advice
    except Exception as e:
        current_app.logger.error(f"AI Coach error: {e}")

    return _fallback_coach_advice(user)


def _fallback_coach_advice(user):
    """Template-based coach advice when OpenAI is not available."""
    import random

    tips_weak = [
        f"🎯 {user.username}, сул талдаа илүү их цаг зарцуулбал түвшин чинь хурдан дээшлэх болно!",
        f"💪 Сул категоридоо өдөр бүр 5 асуулт хариулж дасгал хий! Бага багаар сайжирна.",
        f"📚 Сул тал дээрээ тогтмол суралцаж бай. Зөвхөн хүчтэй тал дээрээ тоглохоор түвшин чинь гацна.",
        f"🔥 Сул категоридоо алдаа гаргахдаа бүү сэтгэлээр уна! Алдаа бол суралцах боломж.",
    ]

    tips_strong = [
        f"🏆 Хүчтэй тал чинь {user.username}! Үүнийгээ ашиглаж нойлд бусдыг давж чадна!",
        f"⭐ Хүчтэй талдаа тулгуурлаж, сул талдаа анхаарах нь түвшин чинь хурдан дээшлэх түлхүүр!",
        f"🌟 Чамайг энэ хэмжээнд хүргэсэн хүчтэй тал чинь гайхалтай! Үүнийгээ хадгал.",
        f"🎖️ Хүчтэй талдаа тулгуурлаж, шинэ категорид руу тэмүүлээрэй!",
    ]

    return {
        'weak_tip': random.choice(tips_weak),
        'strong_tip': random.choice(tips_strong),
        'is_ai': False
    }
