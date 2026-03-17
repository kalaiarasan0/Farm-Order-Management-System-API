from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
import re
from datetime import datetime
from app.models.tables import Animal as Main_Animal, AnimalEvent, MilkCollection, Tracking_Animal
from fastapi import HTTPException
from sqlalchemy import select, func
from app.schemas.users import User


async def create_event(db: AsyncSession, data: dict, current_user: User) -> AnimalEvent:
    try:
        # Check if the event type is 'milk' and divert to MilkCollection
        if data.get("event_type", "").lower() == "milk":
            total_price = data.get("event_milk_quantity", 0) * data.get(
                "event_milk_rate", 0
            )
            milk_event = MilkCollection(
                animal_id=data.get("animal_id"),
                collection_date=data.get("event_date"),
                collection_time=data.get("event_milk_time"),
                quantity=data.get("event_milk_quantity"),
                milk_snf=data.get("event_milk_snf"),
                milk_fat=data.get("event_milk_fat"),
                milk_water=data.get("event_milk_water"),
                milk_session=data.get("event_milk_session"),
                rate=data.get("event_milk_rate"),
                total_price=total_price,
                notes=data.get("notes"),
                created_by=str(current_user.unique_id),
            )
            db.add(milk_event)
            await db.commit()
            await db.refresh(milk_event)
            # We return the milk_event, but the API will largely ignore it now based on the new schema intent
            # However, for consistency in type hinting, we might need to adjust or just return it as a similar object
            return milk_event
        else:
            # Existing logic for other events
            total_price = 0  # Default for non-milk events unless specified

            event = AnimalEvent(
                animal_id=data.get("animal_id"),
                event_type=data.get("event_type"),
                event_date=data.get("event_date"),
                notes=data.get("notes"),
                milk_quantity=data.get("event_milk_quantity"),
                milk_rate=data.get("event_milk_rate"),
                milk_snf=data.get("event_milk_snf"),
                milk_fat=data.get("event_milk_fat"),
                milk_time=data.get("event_milk_time"),
                milk_water=data.get("event_milk_water"),
                milk_session=data.get("event_milk_session"),
                total_price=total_price,
                created_by=str(current_user.unique_id),
            )

            db.add(event)
            await db.commit()
            await db.refresh(event)
            return event
    except SQLAlchemyError:
        await db.rollback()
        raise


async def create_bulk_milk_collection(db: AsyncSession, data: dict, current_user: User) -> List[MilkCollection]:
    try:
        animals_portions = data.get("animals", [])
        if not animals_portions:
            raise ValueError("No animals provided for bulk collection")

        sms_note = data.get("sms_note", "")
        if not sms_note:
            raise ValueError("sms_note is required")

        # Example SMS: "NAME-511/0463/0014 2026-03-13/E Qty(Ltrs):7.50 Fat%:3.60 Snf%:7.90 Rate:36.70/Lt Amt:Rs.275.25 MilkyMist"
        
        # Parse logic
        try:
            # Date and Session: "2026-03-13/E"
            date_session_match = re.search(r"(\d{4}-\d{2}-\d{2})/([ME])", sms_note)
            event_date = datetime.strptime(date_session_match.group(1), "%Y-%m-%d").date() if date_session_match else None
            event_milk_session = date_session_match.group(2) if date_session_match else None
            if not event_date:
                raise ValueError("Could not parse date from sms_note")

            # Qty(Ltrs):7.50
            qty_match = re.search(r"Qty\(Ltrs\):([\d.]+)", sms_note)
            total_quantity = float(qty_match.group(1)) if qty_match else 0.0

            # Fat%:3.60
            fat_match = re.search(r"Fat%:([\d.]+)", sms_note)
            event_milk_fat = float(fat_match.group(1)) if fat_match else None

            # Snf%:7.90
            snf_match = re.search(r"Snf%:([\d.]+)", sms_note)
            event_milk_snf = float(snf_match.group(1)) if snf_match else None

            # Rate:36.70/Lt
            rate_match = re.search(r"Rate:([\d.]+)/Lt", sms_note)
            event_milk_rate = float(rate_match.group(1)) if rate_match else 0.0
            
            event_milk_time = None
            event_milk_water = None
            notes = sms_note
            
        except Exception as e:
            raise ValueError(f"Failed to parse sms_note: {str(e)}")

        # Fetch animals by tag_ids
        tag_ids = [ap["tag_id"] for ap in animals_portions]
        result = await db.execute(
            select(Tracking_Animal).filter(Tracking_Animal.tag_id.in_(tag_ids))
        )
        animals_db = result.scalars().all()
        tag_id_to_animal_id = {animal.tag_id: animal.id for animal in animals_db}

        missing_tags = set(tag_ids) - set(tag_id_to_animal_id.keys())
        if missing_tags:
            raise ValueError(f"Animals not found for tag_ids: {', '.join(missing_tags)}")

        milk_events = []
        for ap in animals_portions:
            tag_id = ap["tag_id"]
            percentage = ap["percentage"]
            animal_id = tag_id_to_animal_id[tag_id]

            # Separate milk quantity and amount for this animal
            animal_qty = (total_quantity * percentage) / 100.0
            total_price = animal_qty * event_milk_rate

            if event_milk_session == "E":
                event_milk_session = "PM"
                event_milk_time = "18:00"
            elif event_milk_session == "M":
                event_milk_session = "AM"
                event_milk_time = "06:00"

            milk_event = MilkCollection(
                animal_id=animal_id,
                collection_date=event_date,
                collection_time=event_milk_time,
                quantity=animal_qty,
                milk_snf=event_milk_snf,
                milk_fat=event_milk_fat,
                milk_water=event_milk_water,
                milk_session=event_milk_session,
                rate=event_milk_rate,
                total_price=total_price,
                notes=notes,
                created_by=str(current_user.unique_id),
            )
            milk_events.append(milk_event)
            db.add(milk_event)

        await db.commit()
        return milk_events
    except SQLAlchemyError:
        await db.rollback()
        raise


async def update_event_all(
    db: AsyncSession, event_id: int, data: dict, current_user: User
) -> AnimalEvent:
    try:
        event = await db.get(AnimalEvent, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")

        for field, value in data.items():
            if value is None:
                continue

            if hasattr(event, field):
                setattr(event, field, value)

        event.updated_by = str(current_user.unique_id)

        await db.commit()
        await db.refresh(event)
        return event
    except SQLAlchemyError:
        await db.rollback()
        raise


async def update_event_notes(
    db: AsyncSession, event_id: int, notes: str, current_user: User
) -> AnimalEvent:
    try:
        event = await db.get(AnimalEvent, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")

        event.notes = notes
        event.updated_by = str(current_user.unique_id)
        await db.commit()
        await db.refresh(event)
        return event
    except SQLAlchemyError:
        await db.rollback()
        raise


async def list_events(
    db: AsyncSession, current_user: User, limit: int = 50, offset: int = 0
) -> List[AnimalEvent]:
    result = await db.execute(
        select(AnimalEvent)
        .filter(AnimalEvent.created_by == str(current_user.unique_id))
        .options(selectinload(AnimalEvent.animal))
        .limit(limit)
        .offset(offset)
    )
    events = result.scalars().all()

    # Collect category_ids
    category_ids = {event.animal.category_id for event in events if event.animal}

    if category_ids:
        result_main = await db.execute(
            select(Main_Animal).filter(Main_Animal.id.in_(category_ids))
        )
        main_animals = result_main.scalars().all()
        main_animal_map = {ma.id: ma for ma in main_animals}

        for event in events:
            if event.animal and event.animal.category_id in main_animal_map:
                ma = main_animal_map[event.animal.category_id]
                event.animal_species = ma.species
                event.animal_name = ma.name
                # Mapping name to breed for backward compatibility if needed, or just attaching name
                event.animal_breed = ma.name

    return events


async def get_animal_event(
    db: AsyncSession, event_id: int, current_user: User
) -> AnimalEvent:
    # Need to load animal relation
    result = await db.execute(
        select(AnimalEvent)
        .filter(AnimalEvent.created_by == str(current_user.unique_id))
        .options(selectinload(AnimalEvent.animal))
        .filter(AnimalEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.animal:
        result_main = await db.execute(
            select(Main_Animal).filter(Main_Animal.id == event.animal.category_id)
        )
        main_animal = result_main.scalar_one_or_none()

        if main_animal:
            event.animal_species = main_animal.species
            event.animal_name = main_animal.name
            event.animal_breed = main_animal.name

    return event


async def delete_event(db: AsyncSession, event_id: int, current_user: User) -> None:
    try:
        event = await db.get(AnimalEvent, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        if event.created_by != str(current_user.unique_id):
            raise HTTPException(
                status_code=403, detail="You are not authorized to delete this event"
            )
        await db.delete(event)
        await db.commit()
        return event
    except SQLAlchemyError:
        await db.rollback()
        raise


async def get_animal_event_by_animal_id(
    db: AsyncSession,
    animal_id: int,
    current_user: User,
    offset: int = 0,
    limit: int = 50,
) -> List[dict]:
    result = await db.execute(
        select(AnimalEvent)
        .filter(AnimalEvent.created_by == str(current_user.unique_id))
        .options(selectinload(AnimalEvent.animal))
        .filter(AnimalEvent.animal_id == animal_id)
        .offset(offset)
        .limit(limit)
    )
    events = result.scalars().all()

    count_result = await db.execute(
        select(func.count(AnimalEvent.id))
        .filter(AnimalEvent.created_by == str(current_user.unique_id))
        .filter(AnimalEvent.animal_id == animal_id)
    )
    count = count_result.scalar_one()
    # Collect category_ids
    category_ids = {event.animal.category_id for event in events if event.animal}

    if category_ids:
        result_main = await db.execute(
            select(Main_Animal).filter(Main_Animal.id.in_(category_ids))
        )
        main_animals = result_main.scalars().all()
        main_animal_map = {ma.id: ma for ma in main_animals}

        for event in events:
            if event.animal and event.animal.category_id in main_animal_map:
                ma = main_animal_map[event.animal.category_id]
                event.animal_species = ma.species
                event.animal_name = ma.name
                # Mapping name to breed for backward compatibility if needed, or just attaching name
                event.animal_breed = ma.name

    return events, count


async def get_animal_event_by_filter_milk(
    db: AsyncSession,
    animal_id: Optional[int],
    current_user: User,
    offset: int = 0,
    limit: int = 50,
):
    query = (
        select(MilkCollection)
        .filter(MilkCollection.created_by == str(current_user.unique_id))
        .options(selectinload(MilkCollection.animal))
        .offset(offset)
        .limit(limit)
    )

    if animal_id is not None:
        query = query.filter(MilkCollection.animal_id == animal_id)

    result = await db.execute(query)
    milk_collection = result.scalars().all()

    count_query = select(func.count(MilkCollection.id)).filter(
        MilkCollection.created_by == str(current_user.unique_id)
    )

    if animal_id is not None:
        count_query = count_query.filter(MilkCollection.animal_id == animal_id)

    count_result = await db.execute(count_query)
    count = count_result.scalar_one()

    # Collect category_ids
    category_ids = {
        event.animal.category_id for event in milk_collection if event.animal
    }

    if category_ids:
        result_main = await db.execute(
            select(Main_Animal).filter(Main_Animal.id.in_(category_ids))
        )
        main_animals = result_main.scalars().all()
        main_animal_map = {ma.id: ma for ma in main_animals}

        for event in milk_collection:
            if event.animal and event.animal.category_id in main_animal_map:
                ma = main_animal_map[event.animal.category_id]
                event.animal_species = ma.species
                event.animal_name = ma.name
                event.animal_breed = ma.name
            # Attach tag_id regardless of category lookup
            if event.animal:
                event.animal_tag_id = event.animal.tag_id

    return milk_collection, count


async def get_distinct_animal_event_types(
    db: AsyncSession, current_user: User
) -> List[str]:
    result = await db.execute(
        select(func.distinct(AnimalEvent.event_type)).filter(
            AnimalEvent.created_by == str(current_user.unique_id)
        )
    )
    return result.scalars().all()


# if __name__ == "__main__":
#     pass
