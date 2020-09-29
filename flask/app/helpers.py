def has_number(input_string):
    return any(char.isdigit() for char in input_string)


def has_lower(input_string):
    return any(char.islower() for char in input_string)


def has_upper(input_string):
    return any(char.isupper() for char in input_string)


def has_symbol(input_string):
    return any(not char.isalnum() for char in input_string)


def check_password(input_string):
    if any(char.isdigit() for char in input_string) and any(char.islower() for char in input_string) and any(char.isupper() for char in input_string) and any(not char.isalnum() for char in input_string):
        return True
    else:
        return False
