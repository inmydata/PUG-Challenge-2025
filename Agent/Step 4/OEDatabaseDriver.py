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
        url = f"{BASE_URL}carService/saveCar"

        payload = {
            "reg": reg,
            "make": make,
            "model": model,
            "year": str(year)  # send as string for form-urlencoded
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()

            # Success check: API returns "OK"
            if response.text.strip().upper() == "OK":
                return True
            else:
                print(f"Unexpected response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return False

    def get_car(self, reg: str) -> Optional[Car]:
        """
        Look up a car by registration.
        Returns a Car if found, otherwise None.
        """
        url = f"{BASE_URL}carService/getCar"
        headers = {"Accept": "application/json"}

        try:
            r = requests.get(url, params={"reg": reg}, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()

            cars = data.get("ttCar") or []
            if not cars:
                return None

            c = cars[0]
            return Car(
                reg=c.get("reg", ""),
                make=c.get("make", ""),
                model=c.get("model", ""),
                year=int(c.get("year")) if c.get("year") is not None else 0,
            )
        except requests.RequestException as e:
            # Bubble up or log as you prefer; returning None keeps the same signature
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



