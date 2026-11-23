import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import csv
import io

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
DATABASE = os.environ.get("DATABASE_PATH", "results.db")
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "teacher123")

QUESTIONS = [
    {
        "question": "Во время какого путешествия Христофор Колумб достиг материковой части Южной Америки?",
        "options": ["Первого, в 1492 году", "Третьего, в 1498 году", "Четвёртого, в 1502 году"],
        "answer": 1,
        "explanation": "Во время третьего путешествия в 1498 году экспедиция Колумба достигла района залива Пария у берегов Южной Америки."
    },
    {
        "question": "Какой мореплаватель помог европейцам осознать, что открытые земли — это часть ранее неизвестного им материка?",
        "options": ["Америго Веспуччи", "Фернан Магеллан", "Джеймс Кук"],
        "answer": 0,
        "explanation": "Письма и описания Америго Веспуччи сыграли важную роль в распространении представления о Новом Свете."
    },
    {
        "question": "С какой территорией связана экспедиция Педру Алвариша Кабрала 1500 года?",
        "options": ["Перу", "Бразилия", "Аргентина"],
        "answer": 1,
        "explanation": "Экспедиция Кабрала достигла побережья территории современной Бразилии в 1500 году."
    },
    {
        "question": "Что особенно интересовало Александра фон Гумбольдта во время путешествия по Южной Америке?",
        "options": ["Только торговые пути", "Природа, климат, растения и рельеф", "Только древние города"],
        "answer": 1,
        "explanation": "Гумбольдт комплексно изучал природу материка, климат, высотную поясность, растения и рельеф."
    },
    {
        "question": "На каком корабле Чарльз Дарвин совершил кругосветное путешествие, во время которого исследовал Южную Америку?",
        "options": ["«Санта-Мария»", "«Бигль»", "«Виктория»"],
        "answer": 1,
        "explanation": "Дарвин путешествовал на корабле «Бигль» в 1831–1836 годах."
    },
    {
        "question": "В каком году экспедиция Педру Кабрала достигла побережья современной Бразилии?",
        "options": ["1498", "1500", "1519"],
        "answer": 1,
        "explanation": "Это произошло в 1500 году."
    },
    {
        "question": "Какое значение имели экспедиции Гумбольдта?",
        "options": ["Они дали научные описания природы и закономерностей материка", "Они доказали, что Южная Америка — остров", "Они открыли морской путь в Индию"],
        "answer": 0,
        "explanation": "Исследования Гумбольдта внесли большой вклад в географию, ботанику и изучение природных взаимосвязей."
    },
    {
        "question": "Какой вывод можно сделать из истории исследования Южной Америки?",
        "options": ["Материк был изучен за одно путешествие", "Его изучение продолжалось столетиями и включало разные науки", "Исследователи изучали только побережье"],
        "answer": 1,
        "explanation": "Изучение материка было длительным процессом: от морских экспедиций до комплексных научных исследований."
    }
]

STATIONS = [
    {
        "slug": "columbus", "name": "Христофор Колумб", "years": "1498 год",
        "tagline": "Третье путешествие",
        "text": "Во время третьего путешествия через Атлантический океан экспедиция Христофора Колумба достигла района острова Тринидад и залива Пария у северного побережья Южной Америки. Колумб не понял, что перед ним отдельный материк: он продолжал связывать открытые земли с Азией.",
        "fact": "Важно: Колумб достиг материковой части Южной Америки в 1498 году, но не был первым человеком, жившим на этом материке."
    },
    {
        "slug": "vespucci", "name": "Америго Веспуччи", "years": "Конец XV — начало XVI века",
        "tagline": "Новый Свет",
        "text": "Америго Веспуччи участвовал в плаваниях вдоль восточного побережья Южной Америки и описывал увиденные земли. Его письма помогли распространить среди европейцев представление о том, что это не Азия, а ранее неизвестная им часть света. Название «Америка» образовано от латинизированной формы его имени.",
        "fact": "Название материка связано с именем Америго Веспуччи, хотя история его появления сложнее, чем одно отдельное открытие."
    },
    {
        "slug": "cabral", "name": "Педру Алвариш Кабрал", "years": "1500 год",
        "tagline": "Побережье Бразилии",
        "text": "Португальская экспедиция под руководством Педру Алвариша Кабрала в 1500 году достигла побережья территории современной Бразилии. Это событие стало важным этапом в истории европейского освоения восточной части Южной Америки.",
        "fact": "С экспедицией Кабрала связывают начало португальского присутствия на территории современной Бразилии."
    },
    {
        "slug": "humboldt", "name": "Александр фон Гумбольдт", "years": "1799–1804 годы",
        "tagline": "Учёный-естествоиспытатель",
        "text": "Александр фон Гумбольдт вместе с Эме Бонпланом исследовал районы Южной Америки. Учёные изучали климат, растения, высотную поясность, рельеф, реки и взаимосвязи в природе. Их работы стали важной основой научного изучения материка.",
        "fact": "Гумбольдт рассматривал природу как единую систему, в которой компоненты тесно связаны."
    },
    {
        "slug": "darwin", "name": "Чарльз Дарвин", "years": "1831–1836 годы",
        "tagline": "Путешествие на «Бигле»",
        "text": "Во время кругосветного плавания на корабле «Бигль» Чарльз Дарвин посещал разные районы Южной Америки. Он наблюдал животных и растения, изучал геологическое строение, ископаемые остатки и изменения природы. Эти наблюдения позднее стали важными для развития его научных идей.",
        "fact": "Путешествие на «Бигле» было кругосветным, а наблюдения в Южной Америке сыграли важную роль в научной работе Дарвина."
    }
]

def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                answers_json TEXT NOT NULL,
                completed_at TEXT NOT NULL
            )
        """)
        conn.commit()

@app.route("/")
def index():
    return render_template("index.html", stations=STATIONS)

@app.route("/station/<slug>")
def station(slug):
    item = next((s for s in STATIONS if s["slug"] == slug), None)
    if not item:
        return redirect(url_for("index"))
    return render_template("station.html", station=item, stations=STATIONS)

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        name = request.form.get("student_name", "").strip()[:80]
        class_name = request.form.get("class_name", "").strip()[:30]
        if not name or not class_name:
            flash("Укажите имя и класс, чтобы отправить результат.")
            return redirect(url_for("quiz"))

        answers = []
        score = 0
        for i, q in enumerate(QUESTIONS):
            raw = request.form.get(f"q{i}")
            try:
                selected = int(raw)
            except (TypeError, ValueError):
                selected = -1
            correct = selected == q["answer"]
            score += int(correct)
            answers.append({
                "selected": selected,
                "correct": correct,
                "correct_answer": q["answer"],
                "explanation": q["explanation"]
            })

        completed_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        with db() as conn:
            cur = conn.execute(
                "INSERT INTO results (student_name, class_name, score, total, answers_json, completed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, class_name, score, len(QUESTIONS), json.dumps(answers, ensure_ascii=False), completed_at)
            )
            result_id = cur.lastrowid
            conn.commit()
        return redirect(url_for("result", result_id=result_id))

    return render_template("quiz.html", questions=QUESTIONS)

@app.route("/result/<int:result_id>")
def result(result_id):
    with db() as conn:
        row = conn.execute("SELECT * FROM results WHERE id = ?", (result_id,)).fetchone()
    if not row:
        return redirect(url_for("index"))
    answers = json.loads(row["answers_json"])
    return render_template("result.html", row=row, answers=answers, questions=QUESTIONS)

def teacher_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("teacher_logged_in"):
            return redirect(url_for("teacher_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == TEACHER_PASSWORD:
            session["teacher_logged_in"] = True
            return redirect(url_for("teacher_dashboard"))
        flash("Неверный пароль.")
    return render_template("teacher_login.html")

@app.route("/teacher/logout")
def teacher_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/teacher")
@teacher_required
def teacher_dashboard():
    with db() as conn:
        rows = conn.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
    return render_template("teacher.html", rows=rows)

@app.route("/teacher/export.csv")
@teacher_required
def export_csv():
    with db() as conn:
        rows = conn.execute("SELECT student_name, class_name, score, total, completed_at FROM results ORDER BY id DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Имя ученика", "Класс", "Баллы", "Всего вопросов", "Дата и время"])
    for row in rows:
        writer.writerow([row["student_name"], row["class_name"], row["score"], row["total"], row["completed_at"]])
    return Response("\\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=rezultaty_kvest.csv"})

init_db()

if __name__ == "__main__":
    app.run(debug=True)
