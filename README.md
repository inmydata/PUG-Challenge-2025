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

- **Progress OpenEdge Developers Kit** (CLASSROOM edition is sufficient) [https://www.progress.com/oedk](https://www.progress.com/oedk)
- **Visual Studio Code** (Code editor for python and js) — <https://code.visualstudio.com/>
- **Node.js** (for React frontend) — <https://nodejs.org/>
- **Python 3.10+** (venv)
- A modern browser with mic access (if testing voice)
- **Accounts/keys:**
  - **LiveKit** (API key/secret, URL)
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

```text
/openedge/            # ABL handlers/services templates for Car/Booking and test app
/python/
  /step2/             # OEDatabaseDriver env sanity-check
  /step3/             # save_car() via POST
  /step4/             # get_car() via GET + dataclass
  /step5/             # Single-agent (car lookup/add) with LiveKit
  /step6/             # Adds booking tools + driver methods
  /step7/             # Multi-agent architecture AccountAgent → BookingAgent handoff
/frontend/            # (Optional) React demo UI
/token-server/        # (Optional) LiveKit token server (Python)
README.md
```

---

## Workshop Steps (copy code from examples; focus on config + understanding)

### Step 1: OpenEdge Setup – Server, Database, and REST Service

1. Create working directories:

   ```text
   C:\OpenEdge\WRK\oeautos
   C:\OpenEdge\WRK\oeautos\db
   ```

2. Create an empty database:

   ```text
   prodb oeautos empty
   ```

3. Load schema file:

   ```text
   load oeautos.df
   ```

4. Add `oeautos` database to **Progress OE Explorer** and start it (make a note of the port number i.e 25150).
5. Create a new **Progress Application Server** with the following settings:

   - Instance name: `oeautos`  
   - AdminServer: `localhost`  
   - Location: Local  
   - Security model: Developer  
   - Autostart: checked  

6. Edit the `oeautos` ABL application configuration:

   - Startup parameters: `-db oeautos -H localhost -S 25150`
   - Add `C:\OpenEdge\WRK\oeautos` to PROPATH

7. Start the AppServer.
8. In **OE Developer**:

   - Choose `C:\OpenEdge\WRK\oeautos` as the new workspace
   - Create a new OpenEdge project named **AgentTools**
   - Server project
   - Transport: WEB
   - Finish → Open Perspective
   - Delete **AgentTools** → **PASOEContent** → **WEB-INF** → **openedge** → AgentToolsHandler.cls (we will create our own)
   - Delete **Defined Services** → **AgentToolsService** (we will create are own)

9. Add database to project:

   - Right-click project → **Properties** → **Progress OpenEdge** → **Database Connections** → Configure database connections 
   - Click New to add new connection for `oeautos` server.
   - Connection name: oeautos
   - Physical name: db\oeautos
   - Host name: localhost
   - Service/Port: 25150
   - Press Next to Finish, then Apply and Close
   - Select checkbox next to the new connection, Apply and Close

10. Add Server to project:

   - Right-click project → **New** → **Server**
   - Select **Progress Software Corporation** → **Progress Application Server for OpenEdge**, press Next
   - Press **Configure**
   - Select your local Explorer connection in the list, and press **Edit**
   - Enter the correcvt **User name** and **Password** values to connect to OpenEdge Explorer, press **Finish**
   - Press **Apply and close**
   - Select **[machine-name].oeautos** in **Progress Application Server for OpenEdge**
   - Select **oeautos** under **ABL Application** and press Finish

11. Add a new webhandler:

    - Name: `carHandler`  
    - Select **GET** and **POST** method stubs
    - Copy in template code

12. Add WEB service:

    - Right-click project → **New** → **ABL Service**
    - Transport: WEB  
    - Service name: `carService`  
    - Under **WebHandler**, select **Select Existing**
    - Press **Browse**
    - Select the class **carHandler** and press OK
    - Press **Add** to add a Resource URI
    - Enter */carService* as the **Resource URI**
    - Press **Finish**

13. Publish the service to the `oeautos` server:

    - In the **Servers** panel, right click **oeautos in ..** and select **Add and Remove**
    - Select carService in the **Available** list, and press **Add>**
    - Press Finish

---

### Step 2: Python Driver – Environment & Connectivity

1. Install VSCode and Python (if you don't already have them).

    - **Visual Studio Code** — <https://code.visualstudio.com/>
    - **Python** (For agent server-side code) — <https://www.python.org/downloads/>

3. Create directory C:\Work\Agent and open folder in VSCode
4. Create and activate a virtual environment:

   ```bash
   py -m venv .venv
   .\.venv\Scripts\activate
   ```

5. Create a `C:\work\Agent\requirements.txt` file and add:

   ```
   python-dotenv
   ```

   Then install:

   ```bash
   pip install -r requirements.txt
   ```

6. Create a `.env` file with:

   ```
   OE_SERVICE_URL=http://localhost:8080/AgentTools/web/
   ```

7. Copy `OEDatabaseDriver.py` Step 2 code to C:\Work\Agent\OEDatabaseDriver.py (load `.env` and print `OE_SERVICE_URL`).
8. Run the code to test

  ```bash
   py OEDatabaseDriver.py
   ```

---

### Step 3: Python Driver – Saving Cars

1. Copy requirements.txt and OEDatabaseDriver.py from Step 3 into C:\work\Agents. Note 'requests' has been added to requirements.txt and OEDatabaseDriver.py now shows errors
2. Install new dependencies

   ```bash
   pip install -r requirements.txt
   ```

2. Review save_car method
3. Run the code to test

  ```bash
   py OEDatabaseDriver.py
   ```

4. Use OpenEdge\ViewCars.w to confirm record has been created

---

### Step 4: Python Driver – Retrieving Cars

1. Copy OEDatabaseDriver.py from Step 4 into C:\work\Agents.
2. Review get_car method
3. Run the code to test

  ```bash
   py OEDatabaseDriver.py
   ```

---

### Step 5: Introducing the AI Agent (LiveKit Integration)

1. Copy contents of Step 5 into c:\work\Agent
2. Install new dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Create a **LiveKit** account:

    - Goto [https://livekit.io](https://livekit.io)
    - Click **Start Building**
    - Create account
    - Create you first project: name 'PUG Challenge'
    - Complete survey
    - **Settings** → **API Keys**
    - Select API Key
    - Press Reveal Secret
    - Copy **Environmental Variables**
    - Paste into .env

4. Create an **OpenAI** account

    - Create an account at https://platform.openai.com/ (you will need to add some credit. $5 is plenty.)
    - Click cog icon (top right) 
    - Select **API keys**
    - press **+ Create new secret key**
    - Copy secret
    - Add **OPENAI_API_KEY=\[YOUR KEY\]** to .env and save

5. Review code
6. Start agent:

  ```bash
   py main.py dev
   ```

7. Log into [https://agents-playground.livekit.io/](https://agents-playground.livekit.io/) and connect
8. Check the agent can create a car in the DB. Disconnect, and re-connect, check the agent can look up a car. 

---

### Step 6: Booking Functionality

1. Add new OpenEdge web handler for bookings (`bookingHandler`), copy code from Step 6
2. Add new ABL Service (`bookingService`)
3. Transport **WEB**
4. Service name **bookingService**
5. Select existing Web Handler: **bookingHandler**
6. Add resource URI */booking*
7. Add resource URI */booking/{method}*
8. Save your changes, and publish to the server.
9. Copy in code from STEP 6 and review.
10. Start agent:

  ```bash
   py main.py dev
   ```

9. Log into [https://agents-playground.livekit.io/](https://agents-playground.livekit.io/) and connect
10. Check the agent can create a booking in the DB. Disconnect, and re-connect, check the agent can look up a booking.  

---

### Step 7: Multi-Agent Architecture

1. Copy in code from STEP 7 and review.
2. Start agent:

  ```bash
   py main.py dev
   ```

3. Log into [https://agents-playground.livekit.io/](https://agents-playground.livekit.io/) and check agent behaviour

---

## (Optional) Bonus: React Frontend + Token Server

### Step 8: Frontend (optional)

1. If you don’t already have it, download and install node.js  [https://nodejs.org/](https://nodejs.org/)
2. Open new cmd and cd to C:\Work
3. Run command 

  ```bash
  npm create vite@latest frontend -- --template react
  ```

4. Open frontend directory in a new VSCode window
5. Install dependencies:

   ```bash
   npm install
   npm install @livekit/components-react @livekit/components-styles livekit-client --save
   ```

6. Delete “C:\Work\frontend\src\assets” and “C:\Work\frontend\public” folders
7. Copy in contents of frontend\step 1
8. Log in to https://LiveKit.io, got settings..API Keys .. Generate Token
9. Copy token to line 16 of src/components/LiveKitModal.jsx 
10. Create a .env file and enter 

  ```
  VITE_LIVEKIT_URL=[YOUR LIVEKIT URL]
  ```

11. Run front end with 

  ```bash
   npm run dev
   ```

---

### Step 9: Token Server (optional)

1. Create directory C:\work\TokenServer
2. Open a new VSCode window, and open directory C:\work\TokenServer
3. New Terminal
4. Create virtual environment

  ```bash
  py -m venv .venv 
  ```

5. Activate the virtual environment

  ```bash
  .\.venv\Scripts\activate
  ```

6. copy contents of TokenServer from the workshop files
7. Install requirements 

  ```bash
  pip install -r requirements.txt
  ```

8. Enter livekit values into .env
9. Start server 

  ```bash
  py server.py
  ```

10. Copy contents of frontend\step 2
11. Run frontend with 

  ```bash
  npm run dev”
  ```


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
- **LiveKit connection**: verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` in `.env`.
- **OpenAI**: ensure `OPENAI_API_KEY` is set and your model name is valid for your account.

---

## Appendix A — Python Intro for OpenEdge Developers (Quick Notes)

- **Whitespace = blocks** (no `END.`). Indentation is syntax.  
- **Run files directly** (`python myfile.py`); manage deps with **venv + pip** (`requirements.txt`).  
- **Functions** use `def` and return values directly (multiple returns via tuples).  
- **Dataclasses** (`@dataclass`) create light DTOs for records like `Car`.  
- **Requests** library is the go‑to for HTTP calls (`requests.get/post`, `r.json()`).  
- **OO Basics**: `class`, `__init__`, `self` (like `THIS-OBJECT`, but explicit). Inherit with `class Sub(Super):`.

---

## License

MIT

---

## Acknowledgements

- LiveKit Agents
- Progress OpenEdge
- OpenAI
