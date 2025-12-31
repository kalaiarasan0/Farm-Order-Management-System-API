from sqlalchemy.orm import Session, selectinload
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models.tracking_tables import AnimalEvent
from app.models.common import Animal as Main_Animal


def create_event(db: Session, data: dict) -> AnimalEvent:
    try:
        event = AnimalEvent(
            animal_id=data.get("animal_id"),
            event_type=data.get("event_type"),
            event_date=data.get("event_date"),
            notes=data.get("notes"),
        )

        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except SQLAlchemyError:
        db.rollback()
        raise


def update_event_all(db: Session, event_id: int, data: dict) -> AnimalEvent:
    try:
        event = db.query(AnimalEvent).filter(AnimalEvent.id == event_id).first()
        if event is None:
            raise ValueError("Event not found")

        for field, value in data.items():
            if value is None:
                continue

            if hasattr(event, field):
                setattr(event, field, value)

        db.commit()
        db.refresh(event)
        return event
    except SQLAlchemyError:
        db.rollback()
        raise


def update_event_notes(db: Session, event_id: int, notes: str) -> AnimalEvent:
    try:
        event = db.query(AnimalEvent).filter(AnimalEvent.id == event_id).first()
        if event is None:
            raise ValueError("Event not found")

        event.notes = notes
        db.commit()
        db.refresh(event)
        return event
    except SQLAlchemyError:
        db.rollback()
        raise


def list_events(
    db: Session, db_main: Session, limit: int = 50, offset: int = 0
) -> List[AnimalEvent]:
    events = (
        db.query(AnimalEvent)
        .options(selectinload(AnimalEvent.animal))
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Collect main_animal_ids
    main_animal_ids = {event.animal.main_animal_id for event in events if event.animal}

    if main_animal_ids:
        main_animals = (
            db_main.query(Main_Animal).filter(Main_Animal.id.in_(main_animal_ids)).all()
        )
        main_animal_map = {ma.id: ma for ma in main_animals}

        for event in events:
            if event.animal and event.animal.main_animal_id in main_animal_map:
                ma = main_animal_map[event.animal.main_animal_id]
                event.animal_species = ma.species
                event.animal_name = ma.name
                # Mapping name to breed for backward compatibility if needed, or just attaching name
                event.animal_breed = ma.name

    return events


def get_animal_event(db: Session, db_main: Session, event_id: int) -> AnimalEvent:
    event = db.query(AnimalEvent).filter(AnimalEvent.id == event_id).first()
    if event is None:
        raise ValueError("Event not found")

    if event.animal:
        main_animal = (
            db_main.query(Main_Animal)
            .filter(Main_Animal.id == event.animal.main_animal_id)
            .first()
        )
        if main_animal:
            event.animal_species = main_animal.species
            event.animal_name = main_animal.name
            event.animal_breed = main_animal.name

    return event


def delete_event(db: Session, event_id: int) -> None:
    try:
        event = db.query(AnimalEvent).filter(AnimalEvent.id == event_id).first()
        if event is None:
            raise ValueError("Event not found")
        db.delete(event)
        db.commit()
        return event
    except SQLAlchemyError:
        db.rollback()
        raise


# if __name__ == "__main__":
#     from app.db import TrackingSessionLocal
#     with TrackingSessionLocal() as db:
#         events = list_events(db, limit=50, offset=0)
#         for event in events:
#             print("*" * 10 + "Event Details" + "*" * 10)
#             print(vars(event))

#             print("*" * 10 + "Animal Details" + "*" * 10)
#             print(vars(event.animal))
#             print("*" * 120)
