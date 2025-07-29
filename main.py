import os
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
FILENAME = os.getenv("FILENAME")
LOG_FILE = "key_log.txt"

def update_gist(content: str) -> bool:
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }
    payload = {
        "files": {
            FILENAME: {
                "content": content
            }
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] KEY: {content}\n"
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
        return True
    return False

@app.on_event("startup")
async def start_updater():
    async def periodic_update():
        while True:
            key = "AUTO-" + os.urandom(4).hex()
            update_gist(key)
            await asyncio.sleep(900)  # 15 minutes
    asyncio.create_task(periodic_update())

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    log = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            log = f.read()
    return templates.TemplateResponse("index.html", {"request": request, "status": None, "log": log})

@app.post("/update", response_class=HTMLResponse)
async def manual_update(request: Request):
    new_key = "MANUAL-" + os.urandom(4).hex()
    success = update_gist(new_key)
    log = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            log = f.read()
    return templates.TemplateResponse("index.html", {"request": request, "status": "Success" if success else "Failed", "log": log})
