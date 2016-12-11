# This file was originally taken from cx_Freeze by Anthony Tuininga, and is licensed under the  PSF license.

"""
This module contains utility functions shared between distlib modules.
"""


def normalize_to_list(value):
    """
    Takes the different formats of options containing multiple values and
    returns the value as a list object.
    """
    if value is None:
        normalizedValue = []
    elif isinstance(value, str):
        normalizedValue = value.split(',')
    else:
        normalizedValue = list(value)

    return normalizedValue
