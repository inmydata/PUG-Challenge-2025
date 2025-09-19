from livekit.agents.llm import function_tool
from livekit.agents import RunContext
from livekit.agents import Agent, ChatContext
from prompts import BOOKING_INSTRUCTIONS
from OEDatabaseDriver import OEDatabaseDriver, Car, Booking
from typing import Annotated
from dataclasses import asdict
from datetime import date, datetime
import logging



logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

driver = OEDatabaseDriver()

class BookingAssistant(Agent):

    def __init__(self, car: Car) -> None:
        self.car = car
        super().__init__(
            instructions=BOOKING_INSTRUCTIONS
        )

    def get_car_str(self):
        car_str = ""
        for field, value in asdict(self.car).items():
            car_str += f"{field}: {value}\n"
        return car_str
    
    def date_to_long_string(self, d: date) -> str:
        day = d.day
        # Work out suffix
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix} {d.strftime('%B %Y')}"
    
    async def on_enter(self) -> None:
        booking = driver.get_booking(self.car.reg.upper().replace(" ", ""))
        if booking is not None:
            await self.session.generate_reply(
                instructions=
                    f"""Tell the user you have the following details of their car: 
                            Registration: {self.car.reg}, 
                            Make: {self.car.make},
                            Model: {self.car.model},
                            Year: {self.car.year}.
                    Also tell them they have an existing booking on {self.date_to_long_string(booking.booking_date)} with description: {booking.description}.
                    Tell them they have a existing booking on {self.date_to_long_string(booking.booking_date)} with description: {booking.description}.""")
        else:
            next_booking_date = self.date_to_long_string(driver.get_next_available_booking(date.today()))
            await self.session.generate_reply(
                instructions=
                    f"""Tell the user you have the following details of their car: 
                            Registration: {self.car.reg}, 
                            Make: {self.car.make},
                            Model: {self.car.model},
                            Year: {self.car.year}.
                    Tell them they have no existing bookings, the next available booking date is {next_booking_date}, and ask if they would like to make one.""")


    @function_tool
    async def get_car_details(self):
        logger.info("get car details")
        return f"The car details are: {self.get_car_str()}"

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
    async def book_appointment(self, date: Annotated[date, "Date for the appointment"], description: Annotated[str, "Description of the appointment"]):
        logger.info("booking appointment")
        if driver.save_booking(self.car.reg.upper().replace(" ", ""), date, description):
            return f"Appointment booked for {self.date_to_long_string(date)} with description: {description}"
        else:
            return "Failed to book appointment, please try again later"
        
    @function_tool
    async def get_booking(self):
        logger.info("get next appointment")
        booking = driver.get_booking(self.car.reg.upper().replace(" ", ""))
        if booking is None:
            return "No appointment found"
        else:
            return f"Next appointment is on {self.date_to_long_string(booking.booking_date)} with description: {booking.description}"