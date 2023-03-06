"""
This module contains utility functions for the application, mainly related to SSN validation
    and generation.
The function request_path_cache_key is used to correctly generate the cache keys for GET
    functions of Resources
"""
import random
import re

from flask import request


# information on how the ssn is generated and/or validate can be found at
# https://dvv.fi/en/personal-identity-code

def is_valid_ssn(ssn, date_of_birth):
    """
    Checks if the provided ssn is valid, and matches with the given date of birth.
    The function checks: length, format and allowed characters; indication of the date of birth;
        century character; control character.
    :param ssn: string representing the full ssn
    :param date_of_birth: datetime.date object representing the date of birth to check the ssn for
    :return: returns a bool indicating whether the ssn is valid or not.
    """
    return \
        re.fullmatch(
            '([0-9]{6})([A\\-+])(00[2-9]|0[1-9][0-9]|[1-8][0-9][0-9])([0-9A-FHJ-NPR-Y])',
            ssn) is not None \
        and ssn[0:6] == date_of_birth.strftime("%d%m%y") \
        and ssn[10] == generate_control_character(ssn) \
        and ssn[6] == generate_century_character(date_of_birth)


def generate_control_character(ssn):
    """
    Generates the control character (11) for the given ssn
    :param ssn: string representing the partial ssn (characters 1-10) for which to
        generate the control character
    :return: returns the appropriate control character
    """
    char_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F',
                 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y']
    num = float(ssn[0:6] + ssn[7:10])
    mod = round(num % 31)
    return char_list[mod]


def generate_century_character(date):
    """
    Generate the century character (7) for the given date, based on the year
    :param date: datetime type indicating date of birth for which to generate the character
    :return: returns the appropriate century character
    """
    year_digits = date.year // 100
    year_map = {18: '+', 19: '-', 20: 'A'}

    return year_map[year_digits]


def generate_ssn(date):
    """
    Generate a valid ssn from the fiven date of birth. The sequential section (characters 8-10)
        are randomly generated with no regard for gender or sequentiality.
    :param date: datetime.date object indicating the date of birth for which to generate a
        valid ssn
    :return: return a string indicating a valid ssn
    """
    date_string = date.strftime("%d%m%y")
    century_character = generate_century_character(date)
    serial_number = random.randrange(2, 900)
    partial_ssn = f'{date_string}{century_character}{serial_number:03d}'
    control_character = generate_control_character(partial_ssn)
    return f'{partial_ssn}{control_character}'


def request_path_cache_key(*args, **kwargs):
    """
    Helper function for caching Resources. Fix for cache.cached not working with
        request.path as default.
    Used in all get functions in the application
    :return: returns a string which is the desired cache key "request.path"
    """
    return request.path
