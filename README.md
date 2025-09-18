# AI Assistant Workshop: Progress OpenEdge + LiveKit + OpenAI

Build an agentic AI assistant that **reads/writes** to a Progress **OpenEdge** database (via PASOE REST),
powered by **Python + LiveKit Agents + OpenAI**, with a **React** frontend for real‑time interaction.

This README is written for **OpenEdge developers new to Python/LiveKit** and is organized to let you
**replicate the build from scratch**.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Repository Layout](#repository-layout)
3. [Useful Links](#useful-links)
4. [Environment Variables](#environment-variables)
5. [Part A — Setup Notes (Do These First)](#part-a--setup-notes-do-these-first)
    - [A1. Create OpenEdge DB & PASOE REST](#a1-create-openedge-db--pasoe-rest)
    - [A2. Build the Python OEDatabaseDriver](#a2-build-the-python-oedatabasedriver)
    - [A3. Create LiveKit & OpenAI Accounts](#a3-create-livekit--openai-accounts)
    - [A4. Build the Agent Backend](#a4-build-the-agent-backend)
    - [A5. Frontend (React + LiveKit)](#a5-frontend-react--livekit)
    - [A6. Token Server (for secure LiveKit tokens)](#a6-token-server-for-secure-livekit-tokens)
6. [Part B — Step-by-Step Workshop (Concepts + Code)](#part-b--step-by-step-workshop-concepts--code)
    - [Step 1: Environment Setup & Connectivity Test](#step-1-environment-setup--connectivity-test)
    - [Step 2: Save Car via REST](#step-2-save-car-via-rest)
    - [Step 3: Retrieve Car via REST](#step-3-retrieve-car-via-rest)
    - [Step 4: Single Agent with Tools (LiveKit Agents)](#step-4-single-agent-with-tools-livekit-agents)
    - [Step 5: Booking Appointments](#step-5-booking-appointments)
    - [Step 6: Multi-Agent Handoff (Account → Booking)](#step-6-multi-agent-handoff-account--booking)
7. [Troubleshooting](#troubleshooting)
8. [License](#license)

---

## Prerequisites

- **Progress OpenEdge** (PASOE, OE Explorer/Management, PDSOE)
- **Node.js** (for React frontend) — https://nodejs.org/
- **Python 3.10+** (venv)
- A modern browser with mic access (if testing voice)
- Accounts/keys:
  - **LiveKit** (API key/secret, room host)
  - **OpenAI** (API key)

---

## Repository Layout

> You can adapt these names — the workshop zip may already include these folders.

```
/backend
  OEDatabaseDriver.py
  agent.py
  accountAgent.py        # (Step 6, optional)
  bookingAgent.py        # (Step 6, optional)
  prompts.py
  main.py
  requirements.txt
  .env               
/frontend
  (Vite React app)
/token-server
  server.py
  requirements.txt
  .env       
```
---
## Useful Links

- **Python** (For agent serverside code) — [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **LiveKit** — [https://livekit.io/](https://livekit.io/)
- **LiveKit Playground** (To test agent) — [https://agents-playground.livekit.io/](https://agents-playground.livekit.io/)
- **OpenAI Platform** (To create OpenAI API Key) [https://platform.openai.com/](https://platform.openai.com/)
- **Node.js** (for React frontend) — [https://nodejs.org/](https://nodejs.org/)

## Environment Variables

### Backend `.env`
```
OE_SERVICE_URL=http://localhost:8080/oeautos/rest/
OPENAI_API_KEY=sk-...
LIVEKIT_API_KEY=lk_...
LIVEKIT_API_SECRET=...
LIVEKIT_HOST=wss://<your-livekit-host>
```

### Token Server `.env`
```
LIVEKIT_API_KEY=lk_...
LIVEKIT_API_SECRET=...
```

---

## Part A — Setup Notes (Do These First)

> This section mirrors your workshop notes and should be completed **in order**.

### A1. Create OpenEdge DB & PASOE REST

1) **Directories**
```
C:\OpenEdge\WRK\oeautos
C:\OpenEdge\WRK\oeautos\db
```

2) **Database**
- Create db: `prodb oeautos empty`
- Load schema: import `oeautos.df`
- Add DB to OE Explorer / start broker

3) **Create PASOE instance**
- Instance name: `oeautos`
- AdminServer: `localhost`
- Security model: `Developer`
- Check **Autostart**

4) **Configure PASOE ABL application**
- Add startup params:
  ```
  -db oeautos -H localhost -S <DB_PORT>
  ```
- Add to **PROPATH**: `C:\OpenEdge\WRK\oeautos`
- Start AppServer

5) **Create PDSOE Project**
- Workspace: `C:\OpenEdge\WRK\oeautos`
- New project: **AgentTools**
- Transport: **REST**
- Add database connection (localhost / <DB_PORT>)

6) **Create WebHandler**
- Name: `carRestHandler`
- Unselect all method stubs
- Paste template from workshop files
  - `SaveCar(reg, make, model, year)` → returns `"OK"`
  - `GetCar(reg)` → returns `ttCar` (JSON)

7) **Define REST Service**
- Service: `carService`
- Base URI: `/carService`
- Resource **POST** `/saveCar` → `carRestHandler.SaveCar`
  - form params: `reg, make, model, year` → bind to params
  - response: **body** (text `"OK"`)
- Resource **GET** `/getCar` → `carRestHandler.GetCar`
  - query param: `reg`
  - response: **ttCar** → body (JSON)
- **Publish** service
- In **Servers** view: Add/Remove → deploy `carService` → Finish

**Endpoints**
```
POST http://localhost:8080/oeautos/rest/carService/saveCar
GET  http://localhost:8080/oeautos/rest/carService/getCar?reg=ABC123
```

---

### A2. Build the Python OEDatabaseDriver

From a shell in `/backend`:

1) **Create venv & install base deps**
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate
# macOS/Linux:
# source .venv/bin/activate

echo python-dotenv > requirements.txt
pip install -r requirements.txt
```

2) **Create `.env`**
```env
OE_SERVICE_URL=http://localhost:8080/oeautos/rest/
```

3) **Create `OEDatabaseDriver.py` (Step 1 sanity check)**
```python
from dotenv import load_dotenv
import os

load_dotenv(".env", override=True)
print(os.getenv("OE_SERVICE_URL"))
```

4) **Add `requests` & implement save/get (Steps 2–3)**
```bash
echo requests >> requirements.txt
pip install -r requirements.txt
```

```python
# OEDatabaseDriver.py
import os, requests
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv(".env", override=True)
BASE_URL = os.getenv("OE_SERVICE_URL")

@dataclass
class Car:
    reg: str
    make: str
    model: str
    year: int

class OEDatabaseDriver:
    def save_car(self, reg: str, make: str, model: str, year: int) -> bool:
        url = f"{BASE_URL}carService/saveCar"
        payload = {"reg": reg, "make": make, "model": model, "year": str(year)}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            r = requests.post(url, data=payload, headers=headers, timeout=10)
            r.raise_for_status()
            return r.text.strip().upper() == "OK"
        except requests.RequestException as e:
            print(f"save_car failed: {e}")
            return False

    def get_car(self, reg: str) -> Optional[Car]:
        url = f"{BASE_URL}carService/getCar"
        headers = {"Accept": "application/json"}
        try:
            r = requests.get(url, params={"reg": reg}, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            print(f"get_car failed: {e}")
            return None

        cars = data.get("ttCar") or []
        if not cars:
            return None
        c = cars[0]
        return Car(
            reg=c.get("reg",""),
            make=c.get("make",""),
            model=c.get("model",""),
            year=int(c.get("year",0) or 0),
        )
```

---

### A3. Create LiveKit & OpenAI Accounts

- **LiveKit**
  - Sign up → Create Project
  - **Settings → API Keys → Create Key**
  - Put values into backend `.env` as `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and your `LIVEKIT_HOST` (wss://… if using LiveKit Cloud)

- **OpenAI**
  - Create account → Add billing if required → **Create API Key**
  - Put into backend `.env` as `OPENAI_API_KEY`

---

### A4. Build the Agent Backend

1) **Add Agent dependencies**
```bash
# in /backend (venv active)
cat >> requirements.txt <<EOF
livekit-agents[openai,silero,turn-detector]
livekit-plugins-openai
livekit-plugins-silero
EOF
pip install -r requirements.txt
```

2) **Create `prompts.py`**
```python
INSTRUCTIONS = """
You are a friendly UK-based automotive service assistant.
Ask for the car registration, try to find it in OpenEdge.
If not found, ask for make/model/year and create it.
Then offer to check existing bookings or schedule a new one.
Ask one question at a time.
"""
WELCOME_MESSAGE = "Hello! Welcome to AutoAssist. What is your car registration?"
```

3) **Create `agent.py` (single-agent version, Step 4 + booking hooks)**
```python
import logging
from typing import Optional, Annotated
from datetime import date

from livekit_agents import Agent, function_tool
from OEDatabaseDriver import OEDatabaseDriver, Car
from prompts import INSTRUCTIONS

log = logging.getLogger(__name__)
driver = OEDatabaseDriver()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)
        self._car: Optional[Car] = None

    @function_tool
    async def lookup_car_by_registration_number_in_database(self, reg: Annotated[str,"Car registration number"]):
        reg_n = reg.upper().replace(" ","")
        log.info("lookup car %s", reg_n)
        car = driver.get_car(reg_n)
        if car is None:
            return "Car not found"
        self._car = car
        return f"Found {car.make} {car.model} ({car.year})."

    @function_tool
    async def add_car_details_to_database(self,
        reg: Annotated[str,"Reg"],
        make: Annotated[str,"Make"],
        model: Annotated[str,"Model"],
        year: Annotated[int,"Year"]):
        reg_n = reg.upper().replace(" ","")
        ok = driver.save_car(reg_n, make, model, year)
        if not ok:
            return "Unable to save car"
        self._car = Car(reg=reg_n, make=make, model=model, year=year)
        return "Car saved."

    @function_tool
    async def get_details_of_current_car(self):
        if not self._car:
            return "No car on file yet."
        c = self._car
        return f"Current car: {c.reg} — {c.make} {c.model}, {c.year}."
```

4) **Create `main.py`**
```python
import os, asyncio
from livekit_agents import AgentSession, OpenAI
from agent import Assistant
from prompts import WELCOME_MESSAGE

async def main():
    llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo")
    agent = Assistant()
    session = AgentSession(agent=agent, llm=llm)
    await session.run(input_prompt=WELCOME_MESSAGE)

if __name__ == "__main__":
    asyncio.run(main())
```

5) **Run backend**
```bash
python main.py
```

---

### A5. Frontend (React + LiveKit)

1) **Scaffold**
```bash
# from repo root
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install @livekit/components-react @livekit/components-styles livekit-client
```

2) **Minimal UI** (example)
```jsx
// src/App.jsx
import { useState } from "react";
import { LiveKitRoom, DisconnectButton } from "@livekit/components-react";
import "@livekit/components-styles";

const SERVER_URL = import.meta.env.VITE_LIVEKIT_HOST; // wss://...

export default function App() {
  const [token, setToken] = useState("");

  const connect = async () => {
    const room = "autoassist";
    const user = "User";
    const r = await fetch(`http://localhost:5000/token?room=${room}&user=${user}`);
    const { token } = await r.json();
    setToken(token);
  };

  return (
    <div style={{ padding: 24 }}>
      {!token ? (
        <button onClick={connect}>Connect to Assistant</button>
      ) : (
        <LiveKitRoom serverUrl={SERVER_URL} token={token} connect options={{ audio: true }}>
          <p>Connected. Speak to the assistant…</p>
          <DisconnectButton />
        </LiveKitRoom>
      )}
    </div>
  );
}
```

3) **Run frontend**
```bash
npm run dev
```

---

### A6. Token Server (for secure LiveKit tokens)

1) **Setup**
```bash
# /token-server
python -m venv .venv
.\.venv\Scriptsctivate
pip install flask livekit-server-sdk python-dotenv
```

2) **`.env`**
```env
LIVEKIT_API_KEY=lk_...
LIVEKIT_API_SECRET=...
```

3) **`server.py`**
```python
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from livekit_server_sdk import TokenCreator

load_dotenv()
tc = TokenCreator(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))

app = Flask(__name__)

@app.get("/token")
def token():
    room = request.args.get("room","autoassist")
    user = request.args.get("user","User")
    token = tc.create_join_token(room, user)
    return jsonify({"token": token})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
```

4) **Run token server**
```bash
python server.py
```

---

## Part B — Step-by-Step Workshop (Concepts + Code)

### Step 1: Environment Setup & Connectivity Test
Use `python-dotenv` to load `.env` and print `OE_SERVICE_URL` to confirm config. *(See A2.3 code.)*

### Step 2: Save Car via REST
Implement `save_car()` using `requests.post` with `application/x-www-form-urlencoded`. Success if response body is `"OK"`. *(See A2.4 code.)*

### Step 3: Retrieve Car via REST
Implement `get_car()` using `requests.get` with `Accept: application/json`. Parse `ttCar` array and map to a `Car` dataclass. *(See A2.4 code.)*

### Step 4: Single Agent with Tools (LiveKit Agents)
Create `Assistant` extending `Agent`, add `@function_tool` methods:
- `lookup_car_by_registration_number_in_database(reg)`
- `add_car_details_to_database(reg, make, model, year)`
- `get_details_of_current_car()`
Run via `AgentSession` + OpenAI. *(See A4.)*

### Step 5: Booking Appointments
Extend driver with booking endpoints (e.g., `get_next_available_booking`, `save_booking`, `get_booking`) and add matching agent tools (`get_next_available_booking_date`, `book_appointment`, `get_booking`). Update prompts to offer booking after account lookup.

### Step 6: Multi-Agent Handoff (Account → Booking)
Split into `AccountAssistant` (find/create car) and `BookingAssistant` (scheduling). On success in account agent:
```python
return BookingAssistant(car=self.car), "Transfer to booking agent"
```
Booking agent receives `car` context and continues with booking tools.

---

## Troubleshooting

- **OpenEdge REST 404/500**: Check service is **published** and deployed to PASOE; confirm base URL and paths.
- **DB not updating**: Verify `-db` params on PASOE agent and DB broker port; ensure handler logic commits/returns `"OK"`.
- **CORS on token fetch**: Enable CORS on token server or proxy through Vite dev server.
- **No audio**: Browser mic permission; correct `LIVEKIT_HOST` (wss://…); both agent and client joined same room.
- **Tool not called**: Ensure function signatures are decorated with `@function_tool` and names are descriptive; update prompts to instruct expected behavior.

---

## License

This workshop content is provided for educational use within your project or organization. Adapt as needed. Include attribution to the workshop authors as appropriate.
