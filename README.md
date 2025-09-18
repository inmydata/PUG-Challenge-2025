# OpenEdge × LiveKit AI Agent Workshop

Build an AI agent that reads and writes to a Progress OpenEdge database and books automotive service appointments. This workshop is designed for **OpenEdge developers with no prior Python/agent experience**. You’ll follow a guided path, copying working examples at each step and learning how they fit together.

> We’ll use **PASOE REST services** for data access, a small **Python driver** to call those services, and a **LiveKit agent** (with OpenAI) that converses with users, manages car records, and schedules bookings. We’ll initially run the agent through the **LiveKit Agents Playground** and if time, implement a React front end and python token service to complete the app.

---

## What You’ll Build

- **OpenEdge REST services** for `Car` and `Booking` records.
- A small, testable **Python driver** (`OEDatabaseDriver`) that calls those REST endpoints.
- A **LiveKit agent** that uses function tools to call your driver:
  - Lookup/add car details.
  - Offer/confirm bookings.
- A **multi-agent** version showing a handoff from an **Account agent** → **Booking agent**.
- *(Optional, if time permits)* A lightweight **React + Token server** demo UI.

You’ll **copy** the code for each step from the provided `examples/` folders and focus on wiring/config + understanding.

---

## Prerequisites

- **Progress OpenEdge Developers Kit** (CLASSROOM edition is suffice) [https://www.progress.com/oedk](https://www.progress.com/oedk)
- **Visual Studio Code** (Code editor for python and js) — <https://code.visualstudio.com/>
- **Node.js** (for React frontend) — <https://nodejs.org/>
- **Python 3.10+** (venv)
- A modern browser with mic access (if testing voice)
- **Accounts/keys:**
  - **LiveKit** (API key/secret, room host)
  - **OpenAI** (API key)

> You’ll place secrets in a local `.env` file during setup.

---

## Useful Links

- **Progress OpenEdge Developers Kit** [https://www.progress.com/oedk](https://www.progress.com/oedk)
- **Visual Studio Code** — <https://code.visualstudio.com/>
- **Python** (For agent server-side code) — <https://www.python.org/downloads/>
- **LiveKit** — <https://livekit.io/>
- **LiveKit Agents Playground** — <https://agents-playground.livekit.io/>
- **OpenAI Platform** (Create API key) — <https://platform.openai.com/>
- **Node.js** (Optional frontend) — <https://nodejs.org/>

---

## Repository Layout (at a glance)

```
/openedge/            # ABL handlers/services templates for Car/Booking
/python/
  /step1/             # OEDatabaseDriver env sanity-check
  /step2/             # save_car() via POST
  /step3/             # get_car() via GET + dataclass
  /step4-agent/       # Single-agent (car lookup/add) with LiveKit
  /step5-bookings/    # Adds booking tools + driver methods
  /step6-multiagent/  # AccountAgent → BookingAgent handoff
/frontend/            # (Optional) React demo UI
/token-server/        # (Optional) LiveKit token server (Python)
README.md
```

*(Exact names may vary; follow the workshop instructions.)*

---

## Quick Start (Python)

1) **Create & activate venv**
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

2) **Install dependencies**
```bash
pip install -r requirements.txt
```

3) **Create `.env`**
```ini
# OpenEdge (PASOE REST) base URL
OE_SERVICE_URL=http://localhost:8080/oeautos/rest/

# LiveKit (agent runtime)
LIVEKIT_URL=wss://<your-host>.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

# OpenAI
OPENAI_API_KEY=...
```

4) **Smoke test** (Step 1)
```bash
python python/step1/OEDatabaseDriver.py
# Should print OE_SERVICE_URL
```

---

## Workshop Steps (copy code from examples; focus on config + understanding)

### 1) OpenEdge: Build the **Car** REST Service (PASOE)

- Create (or use) an OE workspace and database, add a **REST** transport project (e.g., `AgentTools`).  
- Add **`carRestHandler`** and define a REST service **`carService`** with endpoints:
  - `POST /carService/saveCar` → **SaveCar** — form params: `reg, make, model, year` → returns `"OK"` on success
  - `GET  /carService/getCar`  → **GetCar**  — query param: `reg` → returns JSON with `ttCar` array
- **Publish** `carService` to your PASOE instance and verify it’s reachable (URL based on `OE_SERVICE_URL`).

> Don’t hand-type handlers — **copy** the handler/service artifacts from `openedge/` examples and adjust names/paths as needed.

### 2) Python Driver: **save_car()**

- In `OEDatabaseDriver`, load `.env`, set `BASE_URL = OE_SERVICE_URL`.
- Implement `save_car(reg, make, model, year)` using `requests.post` with `application/x-www-form-urlencoded` to `carService/saveCar`.
- Expect `"OK"` on success; handle HTTP errors gracefully.

Run a quick script (provided in `python/step2/`) to save a test car and print success/failure.

### 3) Python Driver: **get_car()** + `Car` dataclass

- Add a simple `@dataclass Car(reg, make, model, year:int)`.
- Implement `get_car(reg)` using `requests.get` to `carService/getCar?reg=...` and parse JSON.  
  Look for `ttCar` list; map the first item to `Car` or return `None` if not found.
- Test with the provided `python/step3/` script.

### 4) LiveKit Agent: **Single Agent** (car lookup/add)

- Create an `Assistant` class (subclass of `livekit.agents.Agent`) with **instructions** and a **welcome message**.
- Expose driver calls as **function tools** (decorator) so the LLM can invoke them:
  - `lookup_car_by_registration_number_in_database(reg)` → calls `driver.get_car(...)`
  - `add_car_details_to_database(reg, make, model, year)` → calls `driver.save_car(...)`
  - `get_details_of_current_car()` → returns last retrieved/created car
- Configure OpenAI + LiveKit from `.env`. Start the agent main (`python python/step4-agent/main.py`).

**Test in the browser** using **LiveKit Agents Playground**: connect to your running agent and try a simple flow (see *Testing* below).

### 5) Extend Backend + Agent: **Bookings**

- Add a **`bookingRestHandler`** and publish a `bookingService` with endpoints such as:
  - `GET  /bookingService/getBooking?reg=...` → current booking (if any)
  - `POST /bookingService/saveBooking` → create booking for `reg` on `date` with `description`
  - `GET  /bookingService/nextAvailable?startDate=...` → next available slot
- Extend `OEDatabaseDriver` with `get_booking`, `save_booking`, `get_next_available_booking`.
- Add agent tools:
  - `get_the_date_today()`
  - `get_next_available_booking_date(earliest_date)`
  - `book_appointment(reg, date, description)`
  - `get_booking(reg)`
- Update instructions so the agent **offers to make/check bookings** after account lookup.

### 6) **Multi‑Agent** Refactor (handoff)

- Split into `AccountAssistant` (find/create car) and `BookingAssistant` (schedule/look up bookings).
- After a successful lookup/create, **handoff** by returning a `BookingAssistant(car=...)` from the account agent’s tool.
- Booking agent starts with the car in context and focuses only on scheduling.

Start with `python/step6-multiagent/main.py` and repeat the Playground test.

---

## Testing the Agent (suggested flow)

In the **LiveKit Agents Playground**:

1. The agent greets and asks for your **registration**.  
2. Provide a reg (e.g., `AB12 CDE`).  
   - If found, it shows car details.  
   - If not, it asks for **make, model, year** and adds the car.  
3. The agent asks if you’d like to **book an appointment** or **check existing**.  
4. Try “Book me in for the next available date for an annual service.”  
   - Agent retrieves next slot, confirms, and saves the booking.  
5. Ask “What’s my next booking?” to verify.

---

## Environment & Scripts

- **Python venv**: keep dependencies isolated (`python -m venv .venv` → activate → `pip install -r requirements.txt`).
- **.env**: never commit secrets; store `OE_SERVICE_URL`, LiveKit & OpenAI keys locally.
- **Run steps**: each `python/stepX` folder contains a small script (`main.py` or similar) to run that step.

---

## Troubleshooting

- **PASOE service not reachable**: confirm it’s **published**, note the correct **port/context**, and that `OE_SERVICE_URL` ends with `/rest/`.
- **CORS/401** when testing from browsers: use the **Agents Playground** (server‑side agent) to avoid direct browser calls to PASOE.
- **LiveKit connection**: verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` in `.env`.
- **OpenAI**: ensure `OPENAI_API_KEY` is set and your model name is valid for your account.

---

## (Optional) Bonus: React Frontend + Token Server

If you want a small UI after the workshop:

- **Frontend**: `npm create vite@latest frontend -- --template react`, then `npm install`, and add LiveKit components:
  ```bash
  npm install @livekit/components-react @livekit/components-styles livekit-client
  ```
  Replace the default assets with the `frontend/step*` example content; paste a test token or wire a token server.
- **Token Server (Python)**: create `token-server/`, copy example files, `pip install -r requirements.txt`, set LiveKit env in `.env`, and run `python server.py`.
- Point the frontend to your token endpoint and start with `npm run dev`.

---

## Appendix A — Python Intro for OpenEdge Developers (Quick Notes)

- **Whitespace = blocks** (no `END.`). Indentation is syntax.  
- **Run files directly** (`python myfile.py`); manage deps with **venv + pip** (`requirements.txt`).  
- **Functions** use `def` and return values directly (multiple returns via tuples).  
- **Dataclasses** (`@dataclass`) create light DTOs for records like `Car`.  
- **Requests** library is the go‑to for HTTP calls (`requests.get/post`, `r.json()`).  
- **OO Basics**: `class`, `__init__`, `self` (like `THIS-OBJECT`, but explicit). Inherit with `class Sub(Super):`.

Try this warm‑up:
```python
# hello_agent.py
import requests

def main():
    resp = requests.get("https://httpbin.org/get")
    print("Status:", resp.status_code)
    print("JSON:", resp.json())

if __name__ == "__main__":
    main()
```

---

## License

MIT 

---

## Acknowledgements

- LiveKit Agents
- Progress OpenEdge
- OpenAI
