from rich.prompt import Prompt, IntPrompt
from rich.console import Console
from rich.progress import Progress, track
from pathlib import Path
import subprocess
import os

from folder_parser.folder_parser import Direcotry, FolderParser
from interface import UserInterface
from reader.reader import Reader
from validator.validator import Validator
from writer.writer import Writer, WriterFile
from file_handler import FileHandler
from store import PATTERN_TEL_PASS, PATTERN_USERMAIL_USERNAME_PASS

user = os.environ.get('USER_NAME')
password = os.environ.get('USER_PASSWORD')
PD = os.environ.get('PARSING_DISK_NAME')
SD = os.environ.get('SOURCE_DISK_NAME')
console = Console()

class Engine:

    def __init__(self, auto_parse, full_auto):
        self.type_base = None
        self.auto_parse = auto_parse
        self.full_auto = full_auto
        self.file_handler = None
        self.handler_folders = None
        self.all_files_status = set()
        self.interface = UserInterface()

    def autoparse(self, file):
        if self.auto_parse and self.file_handler.delimiter and (self.file_handler.is_simple_file(PATTERN_TEL_PASS, file)):
            self.file_handler.get_keys('1=tel, 2=password')
            self.all_files_status.add('pass')
            self.file_handler.num_columns = 1
            console.print('[cyan]' + 'Автопарсинг tel password')
            return True
        elif self.auto_parse and self.file_handler.delimiter and (self.file_handler.is_simple_file(PATTERN_USERMAIL_USERNAME_PASS, file)):
            self.file_handler.get_keys(f'1=user_mail_name, 2=password')
            self.all_files_status.add('pass')
            self.file_handler.num_columns = 1
            console.print('[cyan]' + f'Автопарсинг umn password')
            return True
        else:
            return False

    def rehandle_file_parameters(self):
        self.file_handler.handle_file()
        self.file_handler.get_delimiter()
        self.file_handler.get_num_columns()
        self.file_handler.get_column_names(self.full_auto)
        self.interface.show_file(self.file_handler.file)
        self.interface.show_delimiter(self.file_handler.delimiter)
        self.interface.show_num_columns(self.file_handler.num_columns)

    def manual_parsing_menu(self):
        mode = self.interface.ask_mode_handle()
        while True:
            if mode == 'p':
                self.all_files_status.add('pass')
                self.handler_folders.skip_folder()
                break
            elif mode == 'l':
                self.all_files_status.add('trash')
                break
            elif mode == 'o':
                # Открыть в EmEditor
                subprocess.run(f'Emeditor {self.file_handler.file_path}')
                self.rehandle_file_parameters()
            elif mode == 'n':
                # Открыть в Notepad++
                subprocess.run(f'notepad++ {self.file_handler.file_path}')
                self.rehandle_file_parameters()
            elif mode == 'd':
                self.file_handler.delimiter = self.interface.ask_delimiter()
            elif mode == 'e':
                # Перенести папку в ERROR
                print(dir)
                self.all_files_status.add('error')
                try:
                    self.handler_folders.skip_folder(move_to='Error')
                    break
                except Exception as ex:
                    console.print(f'[magenta]Не могу переместить[/magenta]: "[red]{ex}[/red]"')
                    answer = Prompt.ask(f"[green]Если все ОК нажмите Enter", choices=['y', 'n'], default='y')
                    if answer == 'y':
                        mode = 'p'
                        break
            elif mode == 't':
                try:
                    self.all_files_status.add('trash')
                    self.handler_folders.skip_folder(move_to='Trash')
                except Exception as ex:
                    console.print(f'[magenta]Не могу переместить[/magenta]: "[red]{ex}[/red]"')
                    answer = Prompt.ask(f"[green]Если все ОК нажмите Enter", choices=['y', 'n'], default='y')
                    if answer == 'y':
                        mode = 'p'
                        break
            else:
                mode = self.interface.ask_mode_handle()
        self.interface.show_num_columns(self.file_handler.num_columns + 1)
        self.interface.ask_num_cols(self.file_handler.num_columns + 1)

    def parsing_file(self, read_file):
        self.file_handler = FileHandler(read_file, read_file.file_path)
        self.rehandle_file_parameters()
        if not self.auto_parse or not self.autoparse(read_file):
            self.manual_parsing_menu()

        with console.status('[bold blue]Подсчет строк...', spinner='point', spinner_style="bold blue") as status:
            count_rows_in_file = self.file_handler.get_count_rows()
            console.print(f'[yellow]Строк в файле: {count_rows_in_file}')
        validator = Validator(self.file_handler.keys, self.file_handler.num_columns, self.file_handler.delimiter)

        for line in  track(read_file, description='[bold blue]Парсинг файла...', total=count_rows_in_file):

            for fields_data in validator.get_fields(line):



    def start(self):
        self.handler_folders = FolderParser(self.type_base)
        for dir in self.handler_folders.iterate():
            self.all_files_status.clear()

            for file in dir.iterate():
                read_file = Reader(file)
                self.parsing_file(read_file)
                self.writer = Writer(dir.base_type, dir.name,)
