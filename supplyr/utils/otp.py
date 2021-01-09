from random import randint
import requests

def generate_otp():
    otp = str(randint(0, 9999)).zfill(4)
    return otp

def send_otp(mobile_number, otp):
    url = f"https://api.msg91.com/api/v5/otp?&authkey=351304AbploZRnayb5ff793bbP1&template_id=5ff796c39f41550aeb128c17&mobile={'91'+str(mobile_number)}&otp={otp}"
    r = requests.get(url)
    return r.status_code == 200