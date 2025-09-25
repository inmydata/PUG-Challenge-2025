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


    def get_next_available_booking(self, start_date: date) -> Optional[date]:
        """
        Calls the booking service to get the next available booking date.

        Args:
            start_date (date): Starting date for the search

        Returns:
            Optional[date]: Next available booking date, or None if not found
        """
        url = f"{BASE_URL}bookingService/getNextAvailableBooking"

        # Format date as DD-MM-YYYY
        formatted_date = start_date.strftime("%d-%m-%Y")

        try:
            r = requests.get(url, params={"startDate": formatted_date}, timeout=10)
            r.raise_for_status()

            response_text = r.text.strip().strip('"')  # handles if quotes are returned
            if response_text:
                return datetime.strptime(response_text, "%d-%m-%Y").date()
            else:
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None


    def save_booking(self, reg: str, booking_date: date, description: str) -> bool:
        """
        Save a booking via AgentTools booking service.

        Args:
            reg (str): Vehicle registration number
            booking_date (date): Booking date as a Python date
            description (str): Booking description

        Returns:
            bool: True if booking saved successfully, False otherwise
        """
        url = f"{BASE_URL}bookingService/saveBooking"

        formatted_date = booking_date.strftime("%d-%m-%Y")

        payload = {
            "reg": reg,
            "bookingDate": formatted_date,
            "description": description,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()

            if response.text.strip().upper() == "OK":
                return True
            else:
                print(f"Unexpected response: {response.text}")
                return False

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return False

    def get_booking(self, reg: str) -> Optional[Booking]:
        """
        Fetch booking details for a given registration number.

        Args:
            reg (str): Vehicle registration number

        Returns:
            Optional[Booking]: Booking details if found, otherwise None
        """
        url = f"{BASE_URL}bookingService/getBooking"

        try:
            r = requests.get(url, params={"reg": reg}, timeout=10)
            r.raise_for_status()

            data = r.json()
            resp = data.get("response")
            if not resp:
                return None

            booking_date_str = resp.get("BookingDate")
            description = resp.get("Description", "")

            if booking_date_str:
                booking_date = datetime.strptime(booking_date_str, "%d-%m-%Y").date()
                return Booking(booking_date=booking_date, description=description)
            else:
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None


