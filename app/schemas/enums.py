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


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class OrderStatus(str, Enum):
    NULL = "null"
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
