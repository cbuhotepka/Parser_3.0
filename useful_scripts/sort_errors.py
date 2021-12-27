import os
import shutil
from pathlib import Path
from typing import Generator

from rich.console import Console
from rich.prompt import Prompt

import logging

PD = 'C'
console = Console()

TYPE_BASE = ''
START_PATH = os.path.join('\\192.168.88.210\\blitz_error\\errors_do_not_touch\\1', TYPE_BASE)
DESTINATION = os.path.join('\\192.168.88.210\\blitz_error\\errors_sorted\\')

log = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(START_PATH, 'sorting.log'))
log.addHandler(file_handler)

PATH_MOVE = {
    '.txt': os.path.join(DESTINATION, 'CSV', TYPE_BASE),
    '.csv': os.path.join(DESTINATION, 'CSV', TYPE_BASE),
    '.tsv': os.path.join(DESTINATION, 'CSV', TYPE_BASE),
    '.xls': os.path.join(DESTINATION, 'XLS', TYPE_BASE),
    '.xlsx': os.path.join(DESTINATION, 'XLS', TYPE_BASE),
    '.dat': os.path.join(DESTINATION, 'CRONOS', TYPE_BASE),
    '.tad': os.path.join(DESTINATION, 'CRONOS', TYPE_BASE),
    '.sql': os.path.join(DESTINATION, 'SQL', TYPE_BASE),
    '.json': os.path.join(DESTINATION, 'JSON', TYPE_BASE),
}


def start():
    if TYPE_BASE == 'db':
        iter_dirs = iter_for_db(START_PATH)
    else:
        iter_dirs = iter_for_combo(START_PATH)
    start_check(iter_dirs)


def iter_for_db(start_path):
    parsing_complete = get_list_dirs_for_pass(start_path)

    _counter = len(os.listdir(start_path))
    for root_name in os.listdir(start_path):
        _counter -= 1
        print()
        console.print(f"[bold green]Папок осталось {_counter}")
        if not os.path.isdir(os.path.join(start_path, root_name)):
            continue
        for item_name in os.listdir(os.path.join(start_path, root_name)):
            item = Path(os.path.join(start_path, root_name, item_name))
            if item.is_dir():
                if str(item.absolute()) in parsing_complete:
                    console.print(f'[bold yellow]{item.absolute()}')
                else:
                    console.print(f'[bold green]{item.absolute()}')
                    yield item
            else:
                continue


def iter_for_combo(start_path):
    parsing_complete = get_list_dirs_for_pass(start_path)

    # Генератор, возвращает папку в каталоге ~/Source/combo
    _counter = len(os.listdir(start_path))
    for p in os.listdir(start_path):
        item = Path(os.path.join(start_path, p))
        if item.is_dir():
            _counter -= 1
            print()
            console.print(f"[bold green]Папок осталось {_counter}")
            if str(item.absolute()) in parsing_complete:
                console.print(f'[bold green]{item.absolute()}')
                continue
            yield item


def get_list_dirs_for_pass(path):
    if os.path.exists(os.path.join(path, 'check_complete.txt')):
        parsing_complete = Path(os.path.join(path, 'check_complete.txt')).open(encoding='utf-8').readlines()
        parsing_complete = list(map(lambda x: x.replace('\n', ''), parsing_complete))
    else:
        parsing_complete = []

    return parsing_complete


def move_dir(base_dir, dest_path):
    if not os.path.exists(dest_path):
        log.debug(f'Создание папок {dest_path}')
        os.makedirs(dest_path, exist_ok=True)
    try:
        log.debug(f'Перемещение {base_dir} -> {dest_path}')
        with console.status('[bold blue]Перемещение папки...', spinner='point', spinner_style="bold blue"):
            shutil.move(base_dir, dest_path)
    except OSError as ex:
        log.debug(f'Ошибка перемещения {ex}')
        console.print(f"[bold red]{base_dir} - Не могу переместить!")
    finally:
        log.debug('-' * 30)
        log.debug(' ')


def start_check(all_dirs: Generator):
    # Итерируемся по каталогам
    done_check_path = os.path.join(START_PATH, 'check_complete.txt')

    for dir in all_dirs:
        if TYPE_BASE == 'db':
            base_dir = os.path.join(*Path(dir.absolute()).parts[:5])
        else:
            base_dir = os.path.join(*Path(dir.absolute()).parts[:4])
        # (1) - Инициализация папки
        path_to_dir = str(dir.absolute())
        all_files = get_all_files_in_dir(path_to_dir)
        log.debug(f'>>>\nПроверка папки -> {path_to_dir}')
        if not all_files:
            console.print(f"[bold red]{path_to_dir} - Папка пуста")
            log.debug(f'---\nПапак пуста -> {path_to_dir}\n---')
            continue
        console.print(f"[bold cyan]{path_to_dir}")
        console.print(f"[bold green]--Файлов в папке -> {len(all_files)}")

        extensions = get_extensions(all_files)
        log.debug(f'Полученные расширения --> {extensions}')
        if len(extensions) > 1:
            console.print(f"[bold red]{path_to_dir} - Mixed")
            log.debug(f'Папка Mixed!!\n\n')
        elif elem := extensions.pop() in PATH_MOVE.keys():
            dest_path = PATH_MOVE[elem]
            move_dir(base_dir, dest_path)
        else:
            console.print(f"[bold red]I not know what do!")
            log.debug('I not know what do!')


def get_extensions(all_files: list) -> set:
    # set расширений
    log.debug('Проверка расширений....')
    all_extension = set()
    # Обработака command файла
    for file in all_files:
        all_extension.add(file.suffix.lower())
    return all_extension


def get_all_files_in_dir(path_to_dir):
    # Сбор всех файлов с папки
    all_files: list[Path] = []
    for root, dirs, files in os.walk(path_to_dir):
        files = list(filter(lambda x: x == 'readme.txt', files))
        all_files.extend([Path(os.path.join(root, f)) for f in files])
    return all_files


if __name__ == '__main__':
    TYPE_BASE = Prompt.ask('Тип папки', choices=['combo', 'db'])
    start()
