from dotenv import load_dotenv
import os
import requests
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

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
    
@dataclass
class Booking:
    def __init__(self, booking_date: Optional[date] = None, description: str = ""):
        self.booking_date = booking_date # type: ignore
        self.description = description
    booking_date: date
    description: str

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


    def get_next_available_booking(self, start_date: date) -> Optional[date]:
        """
        GET  {BASE_URL}booking/next?startDate=DD-MM-YYYY
        200 -> {"BookingDate":"15-10-2025"}
        """
        url = f"{BASE_URL}booking/next"
        formatted_date = start_date.strftime("%d-%m-%Y")

        try:
            r = requests.get(url, params={"startDate": formatted_date}, headers={"Accept": "application/json"}, timeout=10)

            if r.status_code == 200:
                data = r.json()
                bd = data.get("BookingDate")
                return datetime.strptime(bd, "%d-%m-%Y").date() if bd else None
            elif r.status_code in (204, 404):
                return None
            else:
                print(f"Unexpected status {r.status_code}: {r.text}")
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None


    def save_booking(self, reg: str, booking_date: date, description: str) -> bool:
        """
        POST {BASE_URL}booking
        Body (JSON): {"reg": "...", "date": "DD-MM-YYYY", "description":"..."}
        200 -> "OK"
        409 -> "A booking for the date ... already exists"
        """
        url = f"{BASE_URL}booking"
        payload = {
            "reg": reg,
            "date": booking_date.strftime("%d-%m-%Y"),
            "description": description,
        }

        try:
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)

            if r.status_code == 200:
                return r.text.strip().upper() == "OK"
            elif r.status_code == 409:
                print(f"Conflict: {r.text.strip()}")
                return False
            else:
                print(f"Unexpected status {r.status_code}: {r.text}")
                return False

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return False


    def get_booking(self, reg: str) -> Optional[Booking]:
        """
        GET  {BASE_URL}booking/getbooking?reg=ABC123
        200 -> {"BookingDate":"DD-MM-YYYY","Description":"..."}
        204/404 -> no content
        """
        url = f"{BASE_URL}booking/getbooking"

        try:
            r = requests.get(url, params={"reg": reg}, headers={"Accept": "application/json"}, timeout=10)

            if r.status_code == 200:
                data = r.json()
                bd = data.get("BookingDate")
                desc = data.get("Description", "")
                if not bd:
                    return None
                return Booking(booking_date=datetime.strptime(bd, "%d-%m-%Y").date(), description=desc)

            elif r.status_code in (204, 404):
                return None
            else:
                print(f"Unexpected status {r.status_code}: {r.text}")
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

