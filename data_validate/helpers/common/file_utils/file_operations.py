import os
from pathlib import Path

def get_last_directory_name(path):
    return Path(path).name

def create_directory(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)