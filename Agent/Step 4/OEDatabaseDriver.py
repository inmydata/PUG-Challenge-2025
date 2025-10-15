from dotenv import load_dotenv
import os
import requests
from dataclasses import dataclass
from typing import Optional

load_dotenv(".env", override=True)

import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_URL = os.getenv("OE_SERVICE_URL")

@dataclass
class Car:
    def __init__(self, reg: str = "", make: str = "", model: str = "", year: int = 0):
        self.reg = reg
        self.make = make
        self.model = model
        self.year = year
    reg: str
    make: str
    model: str
    year: int

class OEDatabaseDriver:
    def save_car(self, reg: str, make: str, model: str, year: int) -> bool:
        """
        Calls the car service API to save a car.

        Args:
            reg (str): Vehicle registration number
            make (str): Car make (e.g., "Audi")
            model (str): Car model (e.g., "A4")
            year (int): Year of manufacture

        Returns:
            bool: True if save was successful, False otherwise
        """
        url = f"{BASE_URL}carService"

        payload = {
            "reg": reg,
            "make": make,
            "model": model,
            "year": str(year)  # API expects year as string
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                if response.text.strip().upper() == "OK":
                    return True
                else:
                    print(f"Unexpected response: {response.text}")
                    return False

            elif response.status_code == 409:
                # Duplicate registration case
                print(f"Conflict: {response.text.strip()}")
                return False

            else:
                print(f"Unexpected status {response.status_code}: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return False

    def get_car(self, reg: str) -> Optional[Car]:
        """
        Look up a car by registration.
        Returns a Car if found, otherwise None.
        """
        url = f"{BASE_URL}carService"
        headers = {"Accept": "application/json"}

        try:
            r = requests.get(url, params={"reg": reg}, headers=headers, timeout=10)

            if r.status_code == 200:
                # Body is a single car object
                try:
                    data = r.json()
                except ValueError:
                    print(f"Unexpected non-JSON response: {r.text}")
                    return None

                return Car(
                    reg=str(data.get("reg", "")),
                    make=str(data.get("make", "")),
                    model=str(data.get("model", "")),
                    year=int(data.get("year")) if data.get("year") is not None else 0,
                )

            elif r.status_code in (204, 404):
                # Not found
                return None

            else:
                print(f"Unexpected status {r.status_code}: {r.text}")
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None


# Example usage:
if __name__ == "__main__":
    driver = OEDatabaseDriver()
    car = driver.get_car("GJ24YBR")
    if car:
        print("Found:", car)
    else:
        print("No car found for that reg.")



