from dotenv import load_dotenv
import os
import requests

load_dotenv(".env", override=True)

# Load environment variables from .env
load_dotenv()

BASE_URL = os.getenv("OE_SERVICE_URL")

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


# Example usage
if __name__ == "__main__":
    driver = OEDatabaseDriver()
    success = driver.save_car("GJ24YBR", "Audi", "A4", 2018)
    print("Car saved successfully:", success)





