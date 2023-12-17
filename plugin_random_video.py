# Случайное проигрывание видео
# author: Seliverstov

import subprocess
from pathlib import Path
from random import choice
from typing import Dict

from fuzzywuzzy.process import extract as fuzzy_extract

from vacore import VACore

video_folder_path = Path("")
fullscreen = False
close_at_the_end = False
video_player_path = ""
warm_up_folder_name = ""


# функция на старте
def start(core: VACore):
    manifest = {
        "name": "Случайное MPC-HC проигрывание видео",
        "version": "0.1",
        "require_online": False,

        "description": "Запуск случайного видео из целевой подпапки.",

        "options_label": {
            "player": "Какой видеоплейер использовать. Если не указано, то берет настройки из core",
            "video_player_path": "Путь до папки с видео",
            "warm_up_folder_name": "Имя папки с зарядками",
            "fullscreen": "Запускать медиаплеер в полноэкранном режиме? Поддерживается для vlc и mpc",
            "close_at_the_end": "Закрывать медиаплеер после конца видеролика? Поддерживается для vlc и mpc"
        },

        "default_options": {
            "folder_path": "",
            "warm_up_folder_name": "Зарядка",
            "video_player_path": "",
            "fullscreen": False,
            "close_at_the_end": False
        },

        "commands": {
            "видео|тренировка": play_rnd_video,
            "зарядка": start_rnd_warm_up_video,
        }
    }
    return manifest


def start_with_options(core: VACore, manifest: dict):
    global video_folder_path, fullscreen, close_at_the_end, video_player_path, warm_up_folder_name
    options = manifest["options"]
    video_folder_path = Path(options["video_folder_path"])
    fullscreen = options["fullscreen"]
    warm_up_folder_name = options["warm_up_folder_name"]
    close_at_the_end = options["close_at_the_end"]
    video_player_path = options["video_player_path"] or core.mpcHcPath
    return manifest


def start_rnd_warm_up_video(core: VACore, query: str):
    play_rnd_video(core, query=warm_up_folder_name)


def play_rnd_video(core: VACore, query: str):
    if video_folder_path == "":
        core.say("Не установлена папка с видео")
        return

    if query == "":
        core.say("Пожалуйста, уточните, из какой папки открыть видео?")
        core.context_set(play_rnd_video)
        return

    video_folders = get_video_folders_dict()
    folder = find_best_match_folder_name(query=query, video_folders=video_folders)
    if folder:
        videos = video_folders[folder]
        if videos:
            video = choice(videos)
            start_current_video(core, video)
            return
        else:
            core.say("В этой папке нет видео.")
            core.context_set(play_rnd_video)
            return

    core.say("не нашёл, повторите название.")
    core.context_set(play_rnd_video)


def start_current_video(core: VACore, video: Path):
    player = video_player_path or core.mpcHcPath
    options = []
    if 'vlc' in player.lower():
        if fullscreen:
            options.append('--fullscreen')
        if close_at_the_end:
            options.append('--play-and-exit')
    elif 'mpc' in player.lower():
        if fullscreen:
            options.append('/fullscreen')
        if close_at_the_end:
            options.append('/play')
            options.append('/close')
    print(f'Запускаю файл {video}')
    core.say('Запускаю!')
    subprocess.Popen([player, video, *options])


def get_video_folders_dict() -> Dict[str, list[Path]]:
    """
    Возвращает список команд и соответствующий ему список видео.
    Ищет видео во вложенных папках первого уровня.
    """
    video_extensions = {'.mp4', '.avi', '.mkv', '.flv', '.mov', '.wmv'}
    res = {}
    dirs = [f for f in video_folder_path.iterdir() if f.is_dir()]
    for dir in dirs:
        dir_path = Path(video_folder_path, dir)
        video_files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix in video_extensions]
        res[dir.stem.lower()] = video_files
    return res


def find_best_match_folder_name(query: str, video_folders: dict, threshold=50) -> str | None:
    res = fuzzy_extract(query, video_folders.keys(), limit=1)
    if res and res[0][1] >= threshold:
        name = res[0][0]
        print(f'{query} => {name}. {res[0][1]}% совпадение')
        return res[0][0]
