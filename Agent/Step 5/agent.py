from livekit.agents.llm import function_tool
from livekit.agents import Agent
from prompts import INSTRUCTIONS
from OEDatabaseDriver import OEDatabaseDriver, Car, Booking
from typing import Annotated
from dataclasses import asdict
from datetime import date, datetime
import logging



logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

driver = OEDatabaseDriver()

class Assistant(Agent):

    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)
        self._car_details = Car()
        
    def get_car_str(self):
        car_str = ""
        for field, value in asdict(self._car_details).items():
            car_str += f"{field}: {value}\n"
        return car_str
    
    @function_tool
    async def lookup_car_by_registration_number_in_database(self, reg: Annotated[str, "Car registration number"]):
        logger.info("lookup car - reg: %s", reg)
        
        result = driver.get_car(reg.upper().replace(" ", ""))
        if result is None:
            return "Car not found"
        
        self._car_details = result
        return f"The car details are: {self.get_car_str()}"
    
    @function_tool
    async def get_details_of_current_car(self):
        logger.info("get car  details")
        return f"The car details are: {self.get_car_str()}"
    
    @function_tool
    async def add_car_details_to_database(
        self, 
        reg: Annotated[str, "The registration number (reg) of the car"],
        make: Annotated[str, "The make of the car "],
        model: Annotated[str, "The model of the car"],
        year: Annotated[int, "The year of the car"]
    ):
        reg = reg.replace(" ", "").upper()
        logger.info("create car - reg: %s, make: %s, model: %s, year: %s", reg, make, model, year)
        result = driver.save_car(reg, make, model, year)
        if result is None:
            return "Failed to create car"
        
        self._car_details = Car(reg=reg, make=make, model=model, year=year)
        
        return "car created!"
    
    def date_to_long_string(self, d: date) -> str:
        day = d.day
        # Work out suffix
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix} {d.strftime('%B %Y')}"

    @function_tool
    async def get_the_date_today(self):
        logger.info("lookup today's date")
        date_str = self.date_to_long_string(date.today())
        return f"The date today is {date_str}"
    
    @function_tool
    async def get_next_available_booking_date(self, earliest_date: Annotated[date, "Earliest date for booking"]):
        logger.info("lookup next available booking slot")
        date_str = self.date_to_long_string(driver.get_next_available_booking(earliest_date))
        return f"The next available booking date is {date_str}"
    
    @function_tool 
    async def book_appointment(self, reg: Annotated[str, "Car registration number"], date: Annotated[date, "Date for the appointment"], description: Annotated[str, "Description of the appointment"]):
        logger.info("booking appointment")
        if driver.save_booking(reg.upper().replace(" ", ""), date, description):
            return f"Appointment booked for {self.date_to_long_string(date)} with description: {description}"
        else:
            return "Failed to book appointment, please try again later"
        
    @function_tool
    async def get_booking(self, reg: Annotated[str, "Car registration number"]):
        logger.info("get next appointment")
        booking = driver.get_booking(reg.upper().replace(" ", ""))
        if booking is None:
            return "No appointment found"
        else:
            return f"Next appointment is on {self.date_to_long_string(booking.booking_date)} with description: {booking.description}"