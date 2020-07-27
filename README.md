# Project Setup

## 1. Setup pyenv for python version management & install python 3.8.3
(You can skip this step if python 3.8.x is already installed in your system)

i. Install Prerequisites packages for Ubuntu:
```shell
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
```
ii. Install pyenv:
```shell
curl https://pyenv.run | bash
```

iii. Add to path - add these lines to ~/.bashrc:
```shell
export PATH="/home/coderbaby/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
iv. Install python 3.8.3
```shell
pyenv install 3.8.3
pyenv global 3.8.3
```

## 2. Project Setup

i. Install OS level dependancies:
```shell
sudo apt-get install default-libmysqlclient-dev
```

ii. Clone Project Repository, Cretae VirtualEnv & Install python dependencies
```shell
cd <YOUR_WORKING_DIRECTORY>
git clone https://github.com/abutalhadanish/supplyr-backend.git
cd supplyr-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

iii. Add local settings & run migrations

Add ```supplyr/settings_local.py``` with following contents:
```python
from .settings import *

CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',
]

DATABASE['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'supplyr',
        'USER': 'dbuser'
        'PASSWORD': 'dbpass'
    }
```
(replace `dbuser` and `dbpass` with your actual database username and password and create a table named `supplyr` in your database)

iv. Run in shell to create tables
```shell
python manage.py migrate
```

v. Run server to start the backend.
```shell
python manage.py runserver
```

vi. Create a user using the following command:

```shell
python manage.py createsuperuser
```