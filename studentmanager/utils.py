import random
import re
from studentmanager.models import *

from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter


def is_valid_ssn(ssn, date_of_birth):
    return re.fullmatch('([0-9]{6})([A\\-+])(00[2-9]|0[1-9][0-9]|[1-8][0-9][0-9])([0-9A-FHJ-NPR-Y])', ssn) is not None \
        and ssn[0:6] == date_of_birth.strftime("%d%m%y") \
        and ssn[10] == generate_control_character(ssn) \
        and ssn[6] == generate_century_character(date_of_birth)


def generate_control_character(ssn):
    char_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'H', 'J', 'K', 'L',
                 'M', 'N', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y']
    num = float(ssn[0:6] + ssn[7:10])
    mod = round(num % 31)
    return char_list[mod]


def generate_century_character(date):
    year_digits = date.year // 100
    year_map = {18: '+', 19: '-', 20: 'A'}

    return year_map[year_digits]


def generate_ssn(date):
    date_string = date.strftime("%d%m%y")
    century_character = generate_century_character(date)
    serial_number = random.randrange(2, 900)
    partial_ssn = f'{date_string}{century_character}{serial_number:03d}'
    control_character = generate_control_character(partial_ssn)
    return f'{partial_ssn}{control_character}'


class StudentConverter(BaseConverter):

    def to_python(self, student_ssn):
        db_student = Student.query.filter_by(ssn=student_ssn).first()
        if db_student is None:
            raise NotFound
        return db_student

    def to_url(self, db_student):
        return db_student.ssn
