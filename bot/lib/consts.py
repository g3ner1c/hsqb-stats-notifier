"""Constants and aliases."""

import os
from json import load

try:
    from dotenv import load_dotenv

    load_dotenv()

except ImportError:
    if os.path.exists(".env"):
        print(
            ".env file found but dotenv is not installed, please install the dev dependencies with 'poetry install'"  # noqa: E501
        )
        exit(1)


CLIENT_ID = os.getenv("CLIENT_ID")
INVITE = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot"

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    print(
        "no token found, please add a token to a .env file or set the TOKEN environment variable"
    )
    exit(1)

CONFIG_PATH = "config.json"

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        with open("config_default.json") as default:
            f.write(default.read())

with open(CONFIG_PATH) as f:
    config = load(f)

PREFIX = config["prefix"]
C_NEUTRAL = int(config["embed_colors"]["neutral"], 16)
C_ERROR = int(config["embed_colors"]["error"], 16)
C_SUCCESS = int(config["embed_colors"]["success"], 16)

HSQB = "https://hsquizbowl.org/db/"

# mongodb

MONGODB_HOST = os.getenv("MONGODB_HOST")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")

MONGODB_URI = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}/?retryWrites=true&w=majority"  # noqa: E501
