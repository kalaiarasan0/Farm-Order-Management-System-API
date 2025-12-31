from enum import Enum

class AnimalSource(Enum):
    birth = "birth"
    purchase = "purchase"

class AnimalStatus(Enum):
    alive = "alive"
    sold = "sold"
    dead = "dead"
    transferred = "transferred"
    in_inventory = "in_inventory"