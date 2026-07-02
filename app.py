from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import base64
import uuid
import urllib3
import re
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ============================================================
# ===== ДАННЫЕ GIGACHAT ======================================
# ============================================================

CLIENT_ID = "019f1f2f-6e45-7e08-b4b7-d62f4e3ea80e"
CLIENT_SECRET = "fdc83b5c-3559-4937-8cd4-c11cb3f2c0f1"
SCOPE = "GIGACHAT_API_PERS"

# ============================================================
# ===== ФУНКЦИИ GIGACHAT =====================================
# ============================================================

def get_gigachat_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {auth_base64}"
    }

    data = {"scope": SCOPE}

    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
        if response.status_code != 200:
            print(f"Ошибка токена: {response.status_code}")
            return None
        return response.json().get("access_token")
    except Exception as e:
        print(f"Ошибка получения токена: {e}")
        return None

def generate_questions_gigachat(text, count=3):
    token = get_gigachat_token()
    if not token:
        return get_fallback_questions(count)

    if len(text) > 2000:
        text = text[:1500] + "... (текст сокращен)"

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    levels = []
    if count <= 3:
        levels = ["Легкий", "Средний", "Сложный"]
    elif count <= 5:
        levels = ["Легкий", "Легкий", "Средний", "Средний", "Сложный"]
    else:
        easy = count // 3
        medium = count // 3
        hard = count - easy - medium
        levels = ["Легкий"] * easy + ["Средний"] * medium + ["Сложный"] * hard

    prompt = f"""
Ты — школьный методист. Проанализируй текст и сгенерируй {count} вопросов.

Текст:
{text}

Требования:
1. Вопросы должны быть разного уровня сложности: {', '.join(levels)}
2. Для каждого вопроса напиши краткий ответ для учителя
3. Ответь ТОЛЬКО JSON

Формат ответа:
{{"questions": [{{"level": "Легкий", "question": "вопрос", "teacher_answer": "ответ"}}, ...]}}
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": "Ты — методист. Отвечай только JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }

    try:
        response = requests.post(url, json=payload, headers=headers, verify=False, timeout=60)

        if response.status_code != 200:
            return get_fallback_questions(count)

        try:
            result = response.json()
        except json.JSONDecodeError:
            return get_fallback_questions(count)

        if 'choices' not in result or not result['choices']:
            return get_fallback_questions(count)

        if 'message' not in result['choices'][0]:
            return get_fallback_questions(count)

        ai_text = result['choices'][0]['message']['content']

        if "не обладает собственным мнением" in ai_text or "нейросетевой моделью" in ai_text:
            return get_fallback_questions(count)

        ai_text = ai_text.strip()
        if ai_text.startswith('```json'):
            ai_text = ai_text[7:]
        if ai_text.startswith('```'):
            ai_text = ai_text[3:]
        if ai_text.endswith('```'):
            ai_text = ai_text[:-3]
        ai_text = ai_text.strip()

        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if json_match:
            ai_text = json_match.group()
        else:
            return get_fallback_questions(count)

        try:
            data = json.loads(ai_text)
        except json.JSONDecodeError:
            return get_fallback_questions(count)

        if 'questions' not in data:
            return get_fallback_questions(count)

        questions = data['questions']
        if not questions:
            return get_fallback_questions(count)

        if len(questions) > count:
            questions = questions[:count]
        elif len(questions) < count:
            fallback = get_fallback_questions(count)
            for i in range(len(questions), count):
                if i < len(fallback['questions']):
                    questions.append(fallback['questions'][i])

        data['questions'] = questions
        return data

    except requests.exceptions.Timeout:
        return get_fallback_questions(count)
    except requests.exceptions.RequestException:
        return get_fallback_questions(count)
    except Exception:
        return get_fallback_questions(count)

def get_fallback_questions(count=3):
    all_topics = [
        {"level": "Легкий", "question": "Что такое фотосинтез?", "answer": "Процесс преобразования световой энергии в химическую энергию органических веществ"},
        {"level": "Легкий", "question": "Где происходит фотосинтез?", "answer": "В хлоропластах растительных клеток"},
        {"level": "Легкий", "question": "Какой газ выделяется при фотосинтезе?", "answer": "Кислород (O2)"},
        {"level": "Легкий", "question": "Что такое хлорофилл?", "answer": "Зеленый пигмент, улавливающий световую энергию"},
        {"level": "Легкий", "question": "Какие этапы фотосинтеза существуют?", "answer": "Световая и темновая фазы"},
        {"level": "Средний", "question": "Почему фотосинтез важен для жизни на Земле?", "answer": "Обеспечивает кислородом атмосферу и создает органические вещества"},
        {"level": "Средний", "question": "Какие факторы влияют на скорость фотосинтеза?", "answer": "Интенсивность света, температура, концентрация CO2, наличие воды"},
        {"level": "Средний", "question": "В чем отличие световой фазы от темновой?", "answer": "Световая происходит только на свету, темновая может идти в темноте"},
        {"level": "Средний", "question": "Какие функции выполняет клеточная мембрана?", "answer": "Защитную, транспортную, рецепторную и коммуникационную"},
        {"level": "Сложный", "question": "Что произойдет, если фотосинтез полностью прекратится?", "answer": "Исчезнут растения, затем травоядные животные, затем хищники, в конце человек"},
        {"level": "Сложный", "question": "Как человек использует знание о фотосинтезе?", "answer": "В сельском хозяйстве, биотехнологиях, создании искусственных фотосинтетических систем"},
        {"level": "Сложный", "question": "Как изменение климата влияет на фотосинтез?", "answer": "Повышение CO2 может увеличить скорость, но засуха и повышение температуры снижают эффективность"},
    ]

    random.shuffle(all_topics)

    questions = []
    for i in range(min(count, len(all_topics))):
        questions.append({
            "level": all_topics[i]["level"],
            "question": all_topics[i]["question"],
            "teacher_answer": all_topics[i]["answer"]
        })

    while len(questions) < count:
        for topic in all_topics:
            if len(questions) >= count:
                break
            questions.append({
                "level": topic["level"],
                "question": topic["question"] + f" (вариант {len(questions)+1})",
                "teacher_answer": topic["answer"]
            })

    return {"questions": questions}

# ============================================================
# ===== МАРШРУТЫ ==============================================
# ============================================================

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    text = data.get('text', '')
    count = data.get('count', 3)

    if count < 3:
        count = 3
    elif count > 10:
        count = 10

    if not text or len(text) < 10:
        return jsonify({"error": "Текст слишком короткий (минимум 10 символов)"}), 400

    result = generate_questions_gigachat(text, count)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "GigaChat"})

if __name__ == '__main__':
    print("=" * 50)
    print("Сервер запущен: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
