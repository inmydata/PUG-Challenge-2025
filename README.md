# OpenEdge × LiveKit AI Agent Workshop

Build an AI agent that reads and writes to a Progress OpenEdge database and books automotive service appointments. This workshop is designed for **OpenEdge developers with no prior Python/agent experience**. You’ll follow a guided path, copying working examples at each step and learning how they fit together.

> We’ll use **PASOE WEB Transport services** for data access, a small **Python driver** to call those services, and a **LiveKit agent** (with OpenAI) that converses with users, manages car records, and schedules bookings. We’ll initially run the agent through the **LiveKit Agents Playground** and if time, implement a React front end and python token service to complete the app.

---

## What You’ll Build

- **OpenEdge WEB transport services** for `Car` and `Booking` records.
- A small, testable **Python driver** (`OEDatabaseDriver`) that calls those REST endpoints.
- A **LiveKit agent** that uses function tools to call your driver:
  - Lookup/add car details.
  - Offer/confirm bookings.
- A **multi-agent** version showing a handoff from an **Account agent** → **Booking agent**.
- *(Optional, if time permits)* A lightweight **React + Token server** demo UI.
- *(Optional, if time permits)* A bookings **MCP Server** and dynamic **MCP Client**.

You’ll **copy** the code for each step from the provided `examples/` folders and focus on wiring/config + understanding.

---

## Prerequisites

- **Progress OpenEdge Developers Kit** (CLASSROOM edition is sufficient) — [Progress OpenEdge Developers Kit](https://www.progress.com/oedk)
- **Visual Studio Code** (Code editor for Python and JavaScript) — [Visual Studio Code](https://code.visualstudio.com/)
- **Node.js** (for React frontend) — [Node.js](https://nodejs.org/)
- **Python 3.10+** (venv)
- A modern browser with microphone access (if testing voice)
- **Accounts/keys:**
  - **LiveKit** (API key/secret, URL)
  - **OpenAI** (API key)

> You’ll place secrets in a local `.env` file during setup.

---

## Useful Links

- [Progress OpenEdge Developers Kit](https://www.progress.com/oedk)
- [Visual Studio Code](https://code.visualstudio.com/)
- [Python downloads](https://www.python.org/downloads/)
- [LiveKit](https://livekit.io/)
- [LiveKit Agents Playground](https://agents-playground.livekit.io/)
- [OpenAI Platform](https://platform.openai.com/)
- [Node.js](https://nodejs.org/)

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
  /step10/            # (Optional) MCP Server and dynamic client
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
   - Instance Directory: `C:\OpenEdge\WRK\oeautos\PAS`
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
    - Enter the correct **User name** and **Password** values to connect to OpenEdge Explorer, press **Finish**
    - Press **Apply and close**
    - Select **[machine-name].oeautos** in **Progress Application Server for OpenEdge**
    - Select **oeautos** under **ABL Application** and press Finish

11. Add a new web handler:

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
---

### Step 2: Python Driver – Environment & Connectivity

1. Install VS Code and Python (if you don't already have them):

   - [Visual Studio Code](https://code.visualstudio.com/)
   - [Python downloads](https://www.python.org/downloads/)

2. Create directory `C:\Work\Agent` and open it in VS Code.

3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Create a `C:\Work\Agent\requirements.txt` file and add:

   ```text
   python-dotenv
   ```

   Then install:

   ```powershell
   pip install -r requirements.txt
   ```

5. Create a `.env` file with:

   ```text
   OE_SERVICE_URL=http://localhost:8080/AgentTools/web/
   ```

6. Copy `OEDatabaseDriver.py` Step 2 code to `C:\Work\Agent\OEDatabaseDriver.py` (load `.env` and print `OE_SERVICE_URL`).

7. Run the code to test:

   ```powershell
   py OEDatabaseDriver.py
   ```

---

### Step 3: Python Driver – Saving Cars

1. Copy `requirements.txt` and `OEDatabaseDriver.py` from Step 3 into `C:\Work\Agent` (note: `requests` has been added to `requirements.txt`).

1. Install new dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

1. Review the `save_car` method.

1. Run the code to test:

   ```powershell
   py OEDatabaseDriver.py
   ```

1. Use `OpenEdge\ViewCars.w` to confirm the record has been created.

---

### Step 4: Python Driver – Retrieving Cars

1. Copy `OEDatabaseDriver.py` from Step 4 into `C:\Work\Agent`.

1. Review the `get_car` method.

1. Run the code to test:

   ```powershell
   py OEDatabaseDriver.py
   ```

---

### Step 5: Introducing the AI Agent (LiveKit Integration)

1. Copy contents of Step 5 into `C:\Work\Agent`.

1. Install new dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

1. Create a **LiveKit** account:

   - Go to [LiveKit](https://livekit.io/)
   - Click **Start Building** and create an account
   - Create your first project (for example: `PUG Challenge`)
   - Complete any onboarding steps
   - In **Settings** → **API Keys**, reveal the secret and copy the credentials
   - Paste the values into your `.env` file

1. Create an **OpenAI** account:

   - Create an account at [OpenAI Platform](https://platform.openai.com/)
   - From the account settings, create a new API key
   - Add `OPENAI_API_KEY=[YOUR KEY]` to your `.env` file and save

1. Review the code.

1. Start the agent:

   ```powershell
   py main.py dev
   ```

1. Log into the [LiveKit Agents Playground](https://agents-playground.livekit.io/) and connect.

1. Verify the agent can create and look up cars in the database.

---

### Step 6: Booking Functionality

1. Add a new OpenEdge web handler for bookings (`bookingHandler`) — copy code from Step 6.

1. Add a new ABL Service (`bookingService`) with transport **WEB** and service name `bookingService`.

1. Select existing Web Handler: `bookingHandler`.

1. Add resource URIs:

   - `/booking`
   - `/booking/{method}`

1. Save your changes and publish to the server.

1. Copy in code from Step 6 and review.

1. Start the agent:

   ```powershell
   py main.py dev
   ```

1. Log into the [LiveKit Agents Playground](https://agents-playground.livekit.io/) and connect.

1. Verify the agent can create and look up bookings in the database.

---

### Step 7: Multi-Agent Architecture

1. Copy in code from Step 7 and review.

1. Start the agent:

   ```powershell
   py main.py dev
   ```

1. Log into the [LiveKit Agents Playground](https://agents-playground.livekit.io/) and check agent behaviour.

---

## (Optional) Bonus: React Frontend + Token Server and MCP Server

### Step 8: Frontend (optional)

1. If you don’t already have it, download and install [Node.js](https://nodejs.org/).

1. Open a new terminal and change directory to `C:\Work`.

1. Scaffold a Vite React app:

   ```powershell
   npm create vite@latest frontend -- --template react
   ```

1. Open the `frontend` directory in a new VS Code window.

1. Install dependencies:

   ```powershell
   npm install
   npm install @livekit/components-react @livekit/components-styles livekit-client --save
   ```

1. Delete `C:\Work\frontend\src\assets` and `C:\Work\frontend\public` (if present).

1. Copy in contents of `frontend\step 1` from the examples.

1. Log in to LiveKit, go to Settings → API Keys → Generate Token.

1. Copy the token into `src/components/LiveKitModal.jsx` (as indicated in the frontend example).

1. Create a `.env` file and enter:

   ```text
   VITE_LIVEKIT_URL=[YOUR LIVEKIT URL]
   ```

1. Run the front end with:

   ```powershell
   npm run dev
   ```

---

### Step 9: Token Server (optional)

1. Create directory `C:\Work\TokenServer` and open it in VS Code.

1. Open a new terminal.

1. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

1. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

1. Copy the TokenServer example files from the workshop.

1. Install requirements:

   ```powershell
   pip install -r requirements.txt
   ```

1. Enter LiveKit values into `.env`.

1. Start the server:

   ```powershell
   py server.py
   ```

1. Copy contents of `frontend\step 2` (optional) and run the frontend if desired:

   ```powershell
   npm run dev
   ```

---

### Step 10: MCP Server and dynamic client (optional)

See the [MCP Server documentation](./Agent/Step%2010/bookings_mcp/README.md) for details.

1. Copy in code from Step 10 and review.

1. Start the agent:

   ```powershell
   py main.py dev
   ```

1. Log into the LiveKit Agents Playground and check agent behaviour.

---

## Testing the Agent (suggested flow)

In the **LiveKit Agents Playground**:

1. The agent greets and asks for your **registration**.

1. Provide a reg (e.g., `AB12 CDE`).

   - If found, it shows car details.
   - If not, it asks for **make, model, year** and adds the car.

1. The agent asks if you’d like to **book an appointment** or **check existing**.

1. Try: “Book me in for the next available date for an annual service.”

   - Agent retrieves next slot, confirms, and saves the booking.

1. Ask “What’s my next booking?” to verify.

---

## Environment & Scripts

- **Python venv**: keep dependencies isolated (`python -m venv .venv` → activate → `pip install -r requirements.txt`).
- **.env**: never commit secrets; store `OE_SERVICE_URL`, LiveKit & OpenAI keys locally.
- **Run steps**: each `python/stepX` folder contains a small script (`main.py` or similar) to run that step.

---

## Troubleshooting

- **PASOE service not reachable**: confirm it’s published, note the correct port/context, and that `OE_SERVICE_URL` ends with `/rest/`.
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
