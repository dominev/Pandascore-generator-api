#duominev
#Генератор сайта киберспортивных матчей

import os
import requests
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

# PANDASCORE API
load_dotenv()
API_KEY = os.getenv("PANDASCORE_API_KEY")
if not API_KEY:
    raise ValueError("PANDASCORE_API_KEY не найден в .env файле")

# Конфиг
BASE_URL = "https://api.pandascore.co"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
OUTPUT_DIR = "output"
TEMPLATE_DIR = "templates"

# Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("page.html")

def fetch_matches(date_str):
    """Получить матчи за указанную дату (YYYY-MM-DD) через API pandascore"""
    params = {
        "filter[begin_at]": date_str,
        "sort": "begin_at",
        "per_page": 20
    }
    try:
        response = requests.get(f"{BASE_URL}/matches", headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса для {date_str}: {e}")
        return []

def format_matches(matches):
    """В формат шаблона"""
    formatted = []
    for m in matches:
        teams = "TBD vs TBD"
        if "opponents" in m and m["opponents"]:
            names = []
            for opp in m["opponents"]:
                if opp and "name" in opp:
                    names.append(opp["name"])
                else:
                    names.append("TBD")
            teams = " vs ".join(names)
        elif "name" in m and m["name"]:
            teams = m["name"]

        # Локал время начало
        begin_at = m.get("begin_at")
        if begin_at:
            dt = datetime.fromisoformat(begin_at.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M")
        else:
            time_str = "Время не указано"

        # Статус матча
        status = m.get("status", "unknown")
        status_map = {
            "not_started": ("⏳ Не начался", ""),
            "running": ("🔴 В эфире", "running"),
            "finished": ("✅ Завершён", "finished"),
            "postponed": ("⏸ Отложен", ""),
            "canceled": ("🚫 Отменён", "")
        }
        status_text, status_class = status_map.get(status, ("Статус неизвестен", ""))
        if status == "finished":
            status_class = "finished"
        elif status == "running":
            status_class = "running"

        # Счёт (если есть)
        score = ""
        if "results" in m and m["results"]:
            # Берем первый результат
            res = m["results"][0]
            if "score" in res:
                score = res["score"]
            elif "scores" in res and len(res["scores"]) >= 2:
                score = f"{res['scores'][0]} - {res['scores'][1]}"

        league = m.get("league", {}).get("name", "Неизвестная лига")

        formatted.append({
            "teams": teams,
            "time": time_str,
            "status_text": status_text,
            "status_class": status_class,
            "score": score,
            "league": league
        })
    return formatted

def generate_page(date, date_display, title, description, filename):
    """Генерация HTML для указанной даты"""
    raw_matches = fetch_matches(date)
    matches = format_matches(raw_matches)
    html = template.render(
        title=title,
        description=description,
        date_display=date_display,
        matches=matches
    )
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Сгенерирована страница: {filename}")

def main():
    # Папка output (для вывода)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Вычисляем даты
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # Фомартирование
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    generate_page(
        date=yesterday_str,
        date_display=yesterday.strftime("%d %B %Y"),
        title="Киберспорт: матчи за вчера",
        description="Результаты вчерашних киберспортивных матчей из разных дисциплин",
        filename="yesterday.html"
    )
    generate_page(
        date=today_str,
        date_display=today.strftime("%d %B %Y"),
        title="Киберспорт: матчи сегодня",
        description="Расписание и статус сегодняшних киберспортивных матчей",
        filename="today.html"
    )
    generate_page(
        date=tomorrow_str,
        date_display=tomorrow.strftime("%d %B %Y"),
        title="Киберспорт: матчи завтра",
        description="Анонс завтрашних киберспортивных матчей",
        filename="tomorrow.html"
    )

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0;url=today.html"></head><body></body></html>')
    print("ОК. Все файлы находятся в папке 'output'.")

if __name__ == "__main__":
    main()