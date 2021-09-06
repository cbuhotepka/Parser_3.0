from rich.prompt import Prompt, IntPrompt
from rich.console import Console
import os

console = Console()


class UserInterface:

    def ask_type_base(self):
        type_base = Prompt.ask('Тип папки', choices=['combo', 'db'])
        return type_base

    def ask_delimiter(self):
        _delimiter = Prompt.ask('[magenta]Разделитель', choices=[':', ',', ';', r'\t', '|'])
        _delimiter = '\t' if _delimiter == '\\t' else _delimiter
        console.print(f'[magenta]Разделитель[/magenta]: [red]Отсутствует![/red]')
        return _delimiter

    def ask_num_cols(self, num_columns):
        input_num_columns = IntPrompt.ask('Количество столбцов', default=num_columns + 1) - 1
        return input_num_columns

    def ask_cols_keys(self, find_keys):
        keys = Prompt.ask(f'[cyan]Колонки {find_keys}')
        return keys

    def ask_mode_handle(self):
        answer = Prompt.ask(f"[green]Если все ОК нажмите Enter",
                            choices=['p', 'l', 'o', 'n', 'd', 'e', 't'],
                            default='')
        return answer

    def show_delimiter(self, delimiter):
        if delimiter:
            console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
        else:
            console.print(f'[magenta]Разделитель[/magenta]: [red]Отсутствует![/red]')

    def show_num_columns(self, num_columns):
        console.print(f'[magenta]Количество столбцов[/magenta]: "[green]{num_columns}[/green]"')

    def show_file(self, file):
        """Print 15 line from parsing file
            Args:
                file (Reader()): file for parsing
            """
        console.print(f'[bold magenta]{file.absolute()}')
        console.print("[magenta]" + '-' * 200, overflow='crop')
        for i, line in enumerate(file):
            line_to_show = line[:1000] if len(line) > 3000 else line
            try:
                console.print(line_to_show, end='', )
                if i > 15:
                    break
            except:
                continue
        print('\n')

    def _handler_user_input(self):
        pass