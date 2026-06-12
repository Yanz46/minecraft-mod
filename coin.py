import json
import os
import requests
import zipfile
import time
from datetime import datetime
from requests.exceptions import ConnectionError, Timeout
from http.client import IncompleteRead
from urllib.parse import parse_qs, urlparse, unquote
import argparse
import tempfile
import socket
import http.server
import webbrowser
import socketserver
import threading
import uuid
import platform
import colorama
from colorama import Fore, Style
import PlayFab
from PlayFab import Search_name, LoginWithCustomId, GetEntityToken, process_friendlyuuid
import re
import shutil
import tsv
import dlc

def clear():
    # fungsi clear tetap biarkan seperti aslinya
