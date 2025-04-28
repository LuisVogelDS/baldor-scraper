import os
import re
from urllib.parse import urlparse


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
ASSETS_BASE_DIR = os.path.join(DATA_OUTPUT_DIR, "assets")

os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_BASE_DIR, exist_ok=True)

BASE_URL = "https://www.baldor.com/catalog/"

def get_file_extension_from_url(url: str | None) -> str | None:
    if not url: return None
    parsed_url = urlparse(url)
    path = parsed_url.path
    path_without_qs = path.split('?')[0]
    _, ext = os.path.splitext(path_without_qs)
    return ext.lower() if ext else None

def clean_filename(name: str) -> str:
    # proccesses the string to be used as a filename
    cleaned_name = re.sub(r'[^\w\-\.\(\)\[\] ]', '_', name)
    cleaned_name = re.sub(r' {2,}', ' ', cleaned_name)
    cleaned_name = re.sub(r'_{2,}', '_', cleaned_name)
    cleaned_name = cleaned_name.strip('_ ')
    return cleaned_name