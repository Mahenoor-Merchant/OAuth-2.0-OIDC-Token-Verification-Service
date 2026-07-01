import os
from typing import List

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

ENV_NAME = "development"


def to_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def coerce_value(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def normalize_key(key):
    key = key.strip()
    if key == "NUM_WORKERS":
        return "workers"
    if key.startswith("APP_"):
        key = key[4:]
    return key.strip().lower()


def load_yaml_config():
    filename = f"config.{ENV_NAME}.yaml"
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    result = {}
    for key, value in data.items():
        nk = normalize_key(str(key))
        result[nk] = coerce_value(nk, value)
    return result


def load_dotenv_config():
    data = dotenv_values(".env")
    result = {}
    for key, value in data.items():
        if value is None:
            continue
        nk = normalize_key(str(key))
        result[nk] = coerce_value(nk, value)
    return result


def load_os_env_config():
    result = {}
    for key, value in os.environ.items():
        if key.startswith("APP_"):
            nk = normalize_key(key)
            result[nk] = coerce_value(nk, value)
    return result


def parse_cli_overrides(items: List[str]):
    result = {}
    for item in items:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        nk = normalize_key(key)
        result[nk] = coerce_value(nk, value)
    return result


@app.get("/effective-config")
def effective_config(set: List[str] = Query(default=[])):
    config = DEFAULTS.copy()
    config.update(load_yaml_config())
    config.update(load_dotenv_config())
    config.update(load_os_env_config())
    config.update(parse_cli_overrides(set))

    response = {
        "port": int(config.get("port", 8000)),
        "workers": int(config.get("workers", 1)),
        "debug": bool(config.get("debug", False)),
        "log_level": str(config.get("log_level", "info")),
        "api_key": "****",
    }
    return response