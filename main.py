import tkinter as tk
from tkinter import messagebox, ttk
import requests
from bs4 import BeautifulSoup
import threading
import time
import os

# Имя файла для хранения профилей
PROFILE_FILE = "profiles.txt"

# Словарь для текстов на разных языках
LANGUAGES = {
    "Русский": {
        "title": "Steam Трекер Активности",
        "profile_label": "Введите ID или числовой Steam ID:",
        "add_button": "Добавить",
        "error_empty": "Поле ввода не должно быть пустым",
        "error_invalid": "Введите правильный Steam ID",
        "activity_list": "Активность пользователей",
        "settings_label": "Настройки",
        "update_interval_label": "Интервал обновления (сек):",
        "status_not_playing": "сейчас не играет",
        "status_offline": "сейчас не в сети",
        "status_unknown": "статус неизвестен",
        "status_playing": "играет в"
    },
    "English": {
        "title": "Steam Activity Tracker",
        "profile_label": "Enter ID or numeric Steam ID:",
        "add_button": "Add",
        "error_empty": "Input field cannot be empty",
        "error_invalid": "Enter a valid Steam ID",
        "activity_list": "User Activity",
        "settings_label": "Settings",
        "update_interval_label": "Update Interval (sec):",
        "status_not_playing": "is not playing right now",
        "status_offline": "is currently offline",
        "status_unknown": "status is unknown",
        "status_playing": "is playing"
    },
}

# Начальный язык и интервал обновления
current_language = "Русский"
update_interval = 15


def get_steam_activity(profile_url):
    """
    Парсинг страницы профиля Steam, чтобы узнать, во что играет пользователь.
    Если пользователь не играет, выводится сообщение об этом.
    """
    try:
        response = requests.get(profile_url)
        if response.status_code != 200:
            return f"{texts['error_invalid']} ({response.status_code})"

        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение имени пользователя
        persona_name = soup.find('span', class_='actual_persona_name')
        persona_name = persona_name.get_text(strip=True) if persona_name else "Unknown"

        # Проверка статуса пользователя (в сети, не в сети, играет)
        status_block = soup.find('div', class_='profile_in_game_header')
        if status_block is None:
            # Пользователь не в игре, проверяем общий статус
            online_status = soup.find('div', class_='profile_in_game')
            if online_status:
                status_text = online_status.get_text(strip=True)
                if "В сети" in status_text or "Online" in status_text:
                    return f"{persona_name} {texts['status_not_playing']}"
                elif "Не в сети" in status_text or "Offline" in status_text:
                    return f"{persona_name} {texts['status_offline']}"
                else:
                    return f"{persona_name} {texts['status_unknown']}"
            else:
                return f"{persona_name} {texts['status_unknown']}"

        # Если пользователь в игре, извлекаем название игры
        current_game = soup.find('div', class_='profile_in_game_name')
        if current_game:
            return f"{persona_name} {texts['status_playing']} {current_game.get_text(strip=True)}"
        else:
            return f"{persona_name} {texts['status_unknown']}"
    except Exception as e:
        return f"{texts['error_invalid']}: {e}"


def update_activity():
    """
    Фоновый поток для обновления активности пользователей.
    """
    while True:
        activity_list.delete(0, tk.END)  # Очистить список

        # Проверяем каждый профиль в списке
        for profile_url in profiles:
            activity = get_steam_activity(profile_url)
            activity_list.insert(tk.END, activity)  # Добавляем результат в список

        time.sleep(update_interval)  # Обновлять через заданный интервал


def add_profile():
    """
    Добавление нового профиля в список и сохранение в файл.
    """
    user_input = profile_entry.get().strip()
    if not user_input:
        messagebox.showerror("Ошибка", texts["error_empty"])
        return

    # Проверяем, что добавлено: ID или числовой Steam ID
    if user_input.isdigit():
        profile_url = f"https://steamcommunity.com/profiles/{user_input}"
    else:
        profile_url = f"https://steamcommunity.com/id/{user_input}"

    if profile_url not in profiles:
        profiles.append(profile_url)  # Добавляем ссылку в список
        profile_entry.delete(0, tk.END)  # Очищаем поле ввода
        save_profiles()  # Сохраняем в файл
    else:
        messagebox.showinfo("Информация", "Этот профиль уже добавлен.")


def save_profiles():
    """
    Сохранение профилей в файл.
    """
    with open(PROFILE_FILE, "w", encoding="utf-8") as file:
        for profile in profiles:
            file.write(profile + "\n")


def load_profiles():
    """
    Загрузка профилей из файла.
    """
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as file:
            for line in file:
                profile_url = line.strip()
                if profile_url and profile_url not in profiles:
                    profiles.append(profile_url)


def change_language(selected_language):
    """
    Смена языка интерфейса.
    """
    global texts
    texts = LANGUAGES[selected_language]

    # Обновляем текст интерфейса
    root.title(texts["title"])
    profile_label.config(text=texts["profile_label"])
    add_button.config(text=texts["add_button"])
    activity_label.config(text=texts["activity_list"])
    settings_label.config(text=texts["settings_label"])
    update_interval_label.config(text=texts["update_interval_label"])


def change_update_interval(new_interval):
    """
    Изменение интервала обновления активности.
    """
    global update_interval
    update_interval = int(new_interval)


# Создание GUI
root = tk.Tk()
texts = LANGUAGES[current_language]  # Установка начального языка

root.title(texts["title"])

# Список для хранения профилей
profiles = []
load_profiles()  # Загрузка профилей из файла

# Верхняя часть окна (ввод ссылки)
frame_top = tk.Frame(root)
frame_top.pack(pady=10)

profile_label = tk.Label(frame_top, text=texts["profile_label"])
profile_label.pack(side=tk.LEFT, padx=5)

profile_entry = tk.Entry(frame_top, width=40)
profile_entry.pack(side=tk.LEFT, padx=5)

add_button = tk.Button(frame_top, text=texts["add_button"], command=add_profile)
add_button.pack(side=tk.LEFT, padx=5)

# Поле для отображения активности
frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=10)

activity_label = tk.Label(frame_bottom, text=texts["activity_list"])
activity_label.pack()

activity_list = tk.Listbox(frame_bottom, width=80, height=20)
activity_list.pack()

# Добавляем профили из памяти в интерфейс
for profile in profiles:
    activity_list.insert(tk.END, f"Загружен профиль: {profile}")

# Нижняя часть окна (настройки)
frame_settings = tk.Frame(root)
frame_settings.pack(pady=10)

settings_label = tk.Label(frame_settings, text=texts["settings_label"])
settings_label.pack()

update_interval_label = tk.Label(frame_settings, text=texts["update_interval_label"])
update_interval_label.pack(side=tk.LEFT, padx=5)

interval_var = tk.StringVar(value=str(update_interval))
interval_menu = ttk.Combobox(frame_settings, textvariable=interval_var, values=[10, 15, 20, 25, 30, 35, 40, 45])
interval_menu.pack(side=tk.LEFT, padx=5)
interval_menu.bind("<<ComboboxSelected>>", lambda e: change_update_interval(interval_var.get()))

# Добавление меню для выбора языка
language_menu = tk.Menu(root)
root.config(menu=language_menu)

language_submenu = tk.Menu(language_menu, tearoff=0)
language_menu.add_cascade(label="Language", menu=language_submenu)

for lang in LANGUAGES.keys():
    language_submenu.add_command(label=lang, command=lambda l=lang: change_language(l))

# Запуск потока для обновления активности
thread = threading.Thread(target=update_activity, daemon=True)
thread.start()

# Запуск основного цикла
root.mainloop()
