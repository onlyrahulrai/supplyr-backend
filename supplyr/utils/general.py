import re

def validate_mobile_number(mobile_number):
    # mobile_pattern = re.compile("(0|91|\+91)?[6-9][0-9]{9}$") 
    mobile_pattern = re.compile("[6-9][0-9]{9}$") 
    if not mobile_pattern.match(mobile_number):
        return False
    return True