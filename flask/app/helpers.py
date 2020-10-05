def check_password(input_string):
    if any(char.isdigit() for char in input_string) \
        and any(char.islower() for char in input_string) \
        and any(char.isupper() for char in input_string) \
        and any(not char.isalnum() for char in input_string):
        return True
    else:
        return False
