import re
from hash_identifer import identify_hashes

class Validator:

    def __init__(self, keys_and_cols_name, num_columns, delimiter):
        self.input_columns_name = keys_and_cols_name
        self.output_data = {}
        self.num_columns = num_columns
        self.delimiter = delimiter
        self.columns_name_index = self.handler_keys()
        self.generator = FieldsGenerator(self.columns_name_index)
        self.handlers_dict = {
                                'user_mail_name': self._umn_handler,
                                'usermail': self._um_handler,
                                'username': self._un_handler,
                                'password': self._p_handler,
                                'hash': self._h_handler,
                                'tel': self._t_handler,
                            }

    def handler_keys(self):
        """

        @return: result = {'username': [0],
                            'usermail': [1, 2],
                            'password': [3],
                            'tel': [4, 5]}
        """
        result = {}
        for item in sorted(self.input_columns_name, key=lambda i: i[0]):
            result.setdefault(item[1], [])
            result[item[1]].extend([int(item[0]) - 1])
        return result

    def _umn_handler(self, value: str) -> dict:
        result = {}
        _value = value
        name = 'usermail' if self._is_usermail(_value) else 'username'
        if name == 'username' and not self._is_username(_value):
            _value = ''
        result[name] = _value
        return result

    def _p_handler(self, value: str) -> dict:
        result = {}
        _value = value
        algorithm = self._get_hash_type(_value) or ''
        if not algorithm:
            name = 'userpass_plain'
        else:
            name = 'hash'
        result['algorithm'] = algorithm
        result[name] = _value
        return result

    def _un_handler(self, value: str) -> dict:
        result = {}
        _value = value
        name = 'username'
        if name == 'username' and not self._is_username(_value):
            _value = ''
        result[name] = _value
        return result

    def _um_handler(self, value: str) -> dict:
        result = {}
        _value = value
        name = 'usermail'
        result[name] = _value if self._is_usermail(_value) else ''
        return result

    def _h_handler(self, value: str) -> dict:
        result = {}
        _value = value
        name = 'hash'
        algorithm = self._get_hash_type(_value) or 'unknown'
        result['algorithm'] = algorithm
        result[name] = _value
        return result

    def _t_handler(self, value: str) -> dict:
        result = {}
        _value = value
        name = 'tel'
        result[name] = _value if self._is_tel(_value) else ''
        return result

    def split_line_to_fields(self, line: str) -> list:
        _fields = []
        pattern_fields = re.compile(f'^' +
                             f'(?:((?:\"[^\"]*?\")|(?:[^{self.delimiter}]*)){self.delimiter})' * (self.num_columns - 1) +
                             f'((?:\"[^\"]*?\")|(?:[^{self.delimiter}]*))')
        match_fields = re.match(pattern_fields, line)
        if match_fields:
            _fields = list(match_fields.groups())
        return _fields

    def _delete_blank_of_line(self, input_string: str) -> str:

        DELETE_VALUES = r'(\bNULL\b)|(\bnull\b)|(<blank>)|(["]{3})'

        clean_string = re.sub(r'(\n$)|(\r$)', '', input_string)
        clean_string = re.sub(DELETE_VALUES, "", clean_string)
        return clean_string

    def _is_username(self, value: str) -> bool:
        if re.match(r"^[^|/\\\[\]\(\):;,@]{3,16}$", value):
            return True
        return False

    def _is_usermail(self, value: str) -> bool:
        if re.match(r"[\w\d_\.+\-@!#/$*\^]+@[\d\w.\-_]+\.[\w]{2,5}", value):
            return True
        return False

    def get_usermail(self, value: str) -> str:
        return re.search(r"[\w\d_\.+\-@!#/$*\^]+@[\d\w.\-_]+\.[\w]{2,5}", value).group(0)

    def _is_hash(self, value: str) -> bool:
        return self._get_hash_type(value)

    def _is_tel(self, value: str) -> bool:
        if re.match(r'[+]?[\d\.\s\(]{2,}[_\-]?\d+[_\-]?[\d\.\)\s]+', value):
            return True
        return False

    def _get_hash_type(self, value):
        # for pandas nan
        if str(value) == 'nan' or value == None:
            return ''
        algorithms = identify_hashes(value)
        return algorithms[0] if algorithms else ''

    def handler_fields(self, fields) -> list:
        _result_fields = []
        for generete_fields in self.generator.get_generate_fields(fields):
            output_data = {}
            for cols_name, value in generete_fields.items():
                if cols_name in self.handlers_dict.keys():
                    output_data.update(self.handlers_dict[cols_name](value))
                else:
                    output_data.update({cols_name: value})
            yield output_data

    def get_fields(self, line: str) -> dict:
        """
        Return dict{field_name: field_value}
        """
        return self.run(line)


    def run(self, line):
        new_line = self._delete_blank_of_line(line)
        fields = self.split_line_to_fields(new_line)
        self.handler_fields(fields)
        return self.output_data



class FieldsGenerator:

    def __init__(self, columns_name_index):
        self.input_columns_name_index = columns_name_index
        self.columns_name_index = columns_name_index
        self.handlers = {}
        self.count_output_results = self._get_count_output_results()

    def _prepare_input_fields(self, fields):
        username_index = self.input_columns_name_index.get('username')
        self.columns_name_index = self.input_columns_name_index.copy()
        if username_index:
            username_value = fields[username_index[0]]
            if username_index and self.is_usermail(username_value):
                self.columns_name_index.pop('username')
                if not self.columns_name_index.get('usermail'):
                    self.columns_name_index['usermail'] = username_index
                else:
                    self.columns_name_index['usermail'].extend(username_index)
        return self.columns_name_index

    def is_usermail(self, value: str) -> bool:
        if re.match(r"[\w\d_\.+\-@!#/$*\^]+@[\d\w.\-_]+\.[\w]{2,5}", value):
            return True
        return False

    def _get_count_output_results(self):
        values = [item for key, item in self.columns_name_index.items() if key != 'user_additional_info']
        return len(max(values, key=lambda item: len(item)))

    def _create_handler_fields(self, fields):
        handlers = {}
        for cols_name, indexes in self.columns_name_index.items():
            if cols_name != 'user_additional_info':
                handlers[cols_name] = self._handler_fields(fields=fields, indexes=indexes)
            else:
                handlers[cols_name] = self._handler_uai_fields(fields=fields, indexes=indexes)
        return handlers

    def _handler_fields(self, fields, indexes):
        result = None
        for i in indexes:
            result = fields[i]
            yield result
        while True:
            yield result

    def _handler_uai_fields(self, fields, indexes):
        result = '|'.join(fields[i] for i in indexes)
        while True:
            yield result

    def get_generate_fields(self, fields):
        self._prepare_input_fields(fields)
        self.handlers = self._create_handler_fields(fields)
        count_result = 0

        while count_result < self.count_output_results:
            output_data = {}
            count_result += 1
            for cols_name, indexes in self.columns_name_index.items():

                output_data[cols_name] = next(self.handlers[cols_name])
            yield output_data


