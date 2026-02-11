from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from app.models.tables import Animal as Main_Animal, AnimalEvent
from fastapi import HTTPException
from sqlalchemy import select, func
from app.schemas.users import User


async def create_event(db: AsyncSession, data: dict, current_user: User) -> AnimalEvent:
    try:
        total_price = data.get("event_milk_quantity") * data.get("event_milk_rate") if data.get("event_type").lower() == "milk" else 0
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
        select(AnimalEvent)
        .filter(AnimalEvent.created_by == str(current_user.unique_id))
        .filter(func.lower(AnimalEvent.event_type) == "milk")
        .options(selectinload(AnimalEvent.animal))
        .offset(offset)
        .limit(limit)
    )

    if animal_id is not None:
        query = query.filter(AnimalEvent.animal_id == animal_id)

    result = await db.execute(query)
    events = result.scalars().all()

    count_query = (
        select(func.count(AnimalEvent.id))
        .filter(AnimalEvent.created_by == str(current_user.unique_id))
        .filter(func.lower(AnimalEvent.event_type) == "milk")
    )

    if animal_id is not None:
        count_query = count_query.filter(AnimalEvent.animal_id == animal_id)

    count_result = await db.execute(count_query)
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


# if __name__ == "__main__":
#     pass
