import re
import csv
from rich.console import Console
from .store import ASSERT_NAME
from .interface import UserInterface

console = Console()

class FileHandler:

    def __init__(self, file):
        self.file = file
        self.delimiter = None
        self.num_columns = None
        self.interface = UserInterface()
        self.keys = None
        self.cols_name = None

    def handle_file(self):
        self.delimiter = self.get_delimiter()
        self.get_num_columns()


    def get_delimiter(self):
        """
        Получение разделителя
        :param path: путь до csv
        :return: dialect
        """
        list_line = []
        for i, line in enumerate(self.file):
            list_line.append(line)
            if i > 25:
                break

        if len(list_line) > 20:
            list_line = list_line[5:]
        try:
            return csv.Sniffer().sniff(''.join(list_line), delimiters=',:;\t').delimiter
        except csv.Error:
            return None

    def is_simple_file(self, pattern, file):
        result = 0
        for i, line in enumerate(file):
            if i > 10 and re.match(pattern, line):
                result += 1
        if result > 5:
            return True
        return False

    def get_keys(self, input_keys):
        """
        :param inp: "1=usermail, 3=username"
        :return: keys [(tuple)]: (, colsname_plain  Порядок для бд, ключи для fix.py
        """
        args_inp = input_keys.split(',')
        key_res = []
        keys = []
        for arg in args_inp:
            arg = arg.strip()
            data_key = arg.split('=')
            if len(data_key) < 2:
                raise ValueError()
            if data_key[1] in list(ASSERT_NAME.keys()):
                col_name = ASSERT_NAME[data_key[1]]
            elif data_key[1] in list(ASSERT_NAME.values()):
                col_name = data_key[1]
            else:
                raise ValueError('Bad field name')
            key_res.append(col_name)
            keys.append((data_key[0], col_name))
        colsname_plain = key_res[::]
        if 'user_additional_info' in colsname_plain:
            while colsname_plain.count('user_additional_info') > 0:
                colsname_plain.remove('user_additional_info')
            colsname_plain.append('user_additional_info')
        self.keys = keys
        self.cols_name = colsname_plain
        return keys, colsname_plain

    def get_count_rows(self):
        count = sum(1 for _ in self.file)
        return count

    def get_num_columns(self):
        _sum_delimiter = 0
        _sum_lines = 0

        pat = re.compile(f'{self.delimiter}')
        for i, line in enumerate(self.file):
            if i > 10 and (line != '' or line != '\n'):
                line = re.sub(r'(\"[^\"]*?\")', '', line)
                _sum_delimiter += len(re.findall(pat, line))
                _sum_lines += 1

        if _sum_delimiter and _sum_lines:
            _result = _sum_delimiter // _sum_lines
            self.num_columns = _result
            return _result
        return 0