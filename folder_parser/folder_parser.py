import os
import re
from pathlib import Path
from datetime import time
import enum

from store import ERROR_EXTENSIONS
import utils
from rich.prompt import Prompt, IntPrompt
import shutil


USER = os.environ.get('USER_NAME', 'er')
PASSWORD = os.environ.get('USER_PASSWORD', 'qwerty123')
PARSING_DISK = os.environ.get('PARSING_DISK_NAME', 'C')
SOURCE_DISK = os.environ.get('SOURCE_DISK_NAME', 'W')

BASE_TYPES = ['db', 'combo']


class Status(enum):
    PARSE = 'for parsing'
    DONE = 'done'
    SKIP = 'skipped'


class Direcotry:

    def __init__(self, path, base_type, status=Status.PARSE):
        if base_type not in BASE_TYPES:
            raise ValueError(f"Wrong base type provided: {base_type}")
        self.path = path if isinstance(path, Path) else Path(path)
        self.name = self.path.name
        self.base_type = base_type
        self.status = status

        if self.status == Status.Parse:
            self.command_file = open(os.path.join(self.path, '_command_.txt'), 'w', encoding='utf-8', errors='replace')
            self.all_files = self._get_all_files()
            self.base_info = self._get_base_info()

    def iterate(self):
        for file in self.all_files:
            yield file

    def write_commands(self, commands: dict):
        """ Принимает команды в виде словаря {rewrite_file: command} """
        if not self.command_file:
            raise AttributeError("У папки нет command-файла. Проверьте статус папки (PARSE)")
        for f_name, command in commands:
            self.command_file.write(f_name)
            self.command_file.write(command)

    def close(self):
        if self.command_file:
            self.command_file.close()

    def move_to(self, destination):
        # path_source = C:\Source\db\database\item1
        # path_source = C:\Source\combo\database
        path_source = str(self.path)
        if not os.path.exists(path_source):
            return "Папка не существует"
        # base_source = S:\Source\db\database\item1
        base_source = path_source.replace(f'{PARSING_DISK}:', f'{SOURCE_DISK}:')

        # basedir = C:\Source\db\database
        base_dir = os.path.join(*Path(path_source).parts[:4])

        if self.type_base == 'combo':
            # base = database
            base = Path(path_source).parts[3]

            # base_dest = S:\Error\combo
            base_dest = os.path.join(f'{SOURCE_DISK}:\\', destination.capitalize(), self.type_base)

            # path_move = C:\Error\combo
            path_move = os.path.join(f'{PARSING_DISK}:\\', destination.capitalize(), self.type_base)

        else:
            # C:\Souce\db\database\item1
            # _database = item1
            base = Path(path_source).parts[4]
            # base = database
            _database = Path(path_source).parts[3]

            # path_move = C:\Error\db\database
            path_move = Path(os.path.join(f'{PARSING_DISK}:\\', destination.capitalize(), self.type_base, _database))

            # base_dest = S:\Error\db\database
            base_dest = os.path.join(f'{SOURCE_DISK}:\\', destination.capitalize(), self.type_base, _database)

        os.makedirs(str(path_move), exist_ok=True)
        if os.path.exists(os.path.join(path_move, base)):
            shutil.rmtree(os.path.join(path_move, base))
        # Перемещение
        shutil.move(str(path_source), str(path_move))
        shutil.move(base_source, base_dest)
        # Чистка пустых папок
        if os.path.exists(base_dir) and not os.listdir(base_dir):
            shutil.rmtree(base_dir)
        _base_rm = os.path.join(*Path(base_source).parts[:4])
        if os.path.exists(_base_rm) and not os.listdir(_base_rm):
            shutil.rmtree(_base_rm)


    def _get_all_files(self):
        """ Возвращает все файлы кроме readme, _command_ и т.п. """
        all_files: list[Path] = []
        for root, dirs, files in os.walk(self.path):
            files = list(filter(lambda x: not utils.is_escape_file(x), files))
            return [Path(os.path.join(root, f)) for f in files]

    def _get_base_info(self):
        source = ''
        date = ''
        name, source, date = self._get_info_from_readme()
        if not name:
            name = self._get_base_name_from_folder()
        if not source:
            source = 'OLD DATABASE' if self.base_type == 'db' else 'OLD COMBO'
        if not date and self.base_type == 'combo':
            date = self._get_date_from_folder(self)

        # Если дата в неверном формате, то взять дату создания файла
        if not re.search(r'\d{4}-\d{2}-\d{2}', date):
            date = self._get_oldest_file_date()
        return {'name': name, 'date': date, 'source': source}

    def _get_base_name_from_folder(self):
        if utils.check_base_name(self.path.absolute().parent.name):
            if self.base_type == 'db':
                return self.path.absolute().parent.name
            else:
                name = self.name.split('_', 2)[2].replace('_', ' ')
        return None

    def _get_date_from_folder(self):
        return self.name.split('_', 2)[0]

    def _get_oldest_file_date(self):
        dates = []
        for file_path in self.all_files:
            file = Path(file_path)
            create_date = file.stat().st_mtime
            str_date = time.ctime(create_date)
            date = time.strptime(str_date)
            dates.append(date.strftime("%Y-%m-%d"))
        date = min(dates)
        return date

    def _get_info_from_readme(self):
        path_to_readme = os.path.join(self.path, 'readme.txt')
        if not os.path.exists(path_to_readme):
            return None, None, None
        encoding = utils.get_encodinging_file(path_to_readme)
        readme_string = open(os.path.join(self.path, 'readme.txt'), encoding=encoding).readlines()
        _date = readme_string[0].replace("\n", "")
        _source = None
        _name = readme_string[0].replace("\n", "")
        for line in readme_string:
            if re.match(r'https?://', line):
                _source = re.match(r'https?://[\w\d\-=\\/\._\?]+', line.replace("\n", "")).group(0)
                break
            elif re.match(r'OLD (D|C)', line):
                _source = re.match(r'OLD (D|C)[\w]+', line.replace("\n", "")).group(0)
                break
        return _name, _source, _date


class FolderParser:
    def __init__(self, base_type):
        if base_type not in BASE_TYPES:
            raise ValueError(f"Wrong base type provided: {base_type}")
        self.base_type = base_type
        self.path = os.path.join(PARSING_DISK, 'Source')
        
        self.get_complete_dirs()    # устанавливает: complete_dirs_name, complete_dirs, complete_dirs_file
        self.get_passed_dirs()      # устанавливает: passed_dirs_name, passed_dirs, passed_dirs_file


    def get_complete_dirs(self):
        """ Читаем из файла все завершённые папки, открываем dirs_complete.txt для записи """
        self.complete_dirs_name = Path(os.path.join(self.path, 'dirs_complete.txt'))
        if self.complete_dirs_name.exists():
            with open(self.complete_dirs_name, 'r', encoding='utf-8', errors='replace') as f:
                self.complete_dirs = list(map(lambda x: x.strip(), f.readlines()))
        else:
            self.complete_dirs = []
        self.complete_dirs_file = open(self.complete_dirs_name, 'a+', encoding='utf-8', errors='replace')

    def get_passed_dirs(self):
        """ Читаем из файла все пропущенные папки, открываем dirs_passed.txt для записи """
        self.passed_dirs_name = Path(os.path.join(self.path, 'dirs_passed.txt'))
        if self.passed_dirs_name.exists():
            with open(self.passed_dirs_name, 'r', encoding='utf-8', errors='replace') as f:
                self.passed_dirs = list(map(lambda x: x.strip(), f.readlines()))
        else:
            self.passed_dirs = []
        self.passed_dirs_file = open(self.passed_dirs_name, 'a+', encoding='utf-8', errors='replace')

    @property
    def all_folder_paths(self):
        """ Возвращает все папки для парсинга в виде Path """
        try:
            return self._all_folder_paths
        except AttributeError:
            self._all_folder_paths = []
            if self.base_type == 'db':
                for root_name in os.listdir(self.path):
                    if not os.path.isdir(os.path.join(self.path, root_name)):
                        continue
                    for item_name in os.listdir(os.path.join(self.path, root_name)):
                        item = Path(os.path.join(self.path, root_name, item_name))
                        if item.is_dir():
                            self._all_folder_paths.append(item)
            else:
                for root_name in os.listdir(self.path):
                    combo_dir = Path(os.path.join(self.path, root_name))
                    if combo_dir.is_dir():
                        self._all_folder_paths.append(combo_dir)
            return self._all_folder_paths
    
    def iterate(self):
        for folder in self.all_folder_paths:
            if str(folder.absolute()) in self.complete_dirs:
                self.current_folder = Direcotry(folder, self.base_type, status=Status.DONE)
            elif str(folder.absolute()) in self.passed_dirs:
                self.current_folder = Direcotry(folder, self.base_type, status=Status.SKIP)
            self.current_folder = Direcotry(folder, self.base_type)

            yield self.current_folder

    def close_folder(self):
        self.current_folder.close()

    def skip_folder(self, move_to=None):
        self.passed_dirs.append(str(self.current_folder.path))
        self.passed_dirs_file.write(str(self.current_folder.path) + '\n')
        self.current_folder.status = Status.SKIP
        self.current_folder.close()
        if move_to:
            self.current_folder.move_to(move_to)

    def done_folder(self):
        self.complete_dirs.append(str(self.current_folder.path))
        self.complete_dirs_file.write(str(self.current_folder.path) + '\n')
        self.current_folder.status = Status.DONE
        self.current_folder.close()

    def finish(self):
        self.complete_dirs_file.close()
        self.passed_dirs_file.close()