from dotenv import load_dotenv
import os

load_dotenv(".env", override=True)

print(os.getenv("OE_SERVICE_URL"))
