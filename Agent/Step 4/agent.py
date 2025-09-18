from livekit.agents.llm import function_tool
from livekit.agents import Agent
from prompts import INSTRUCTIONS
from OEDatabaseDriver import OEDatabaseDriver, Car
from typing import Annotated
from dataclasses import asdict
import logging
import enum


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