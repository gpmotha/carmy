"""WeekSkeleton, CookingEvent, and MealSlot API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from carmy.api.deps import get_db
from carmy.api.schemas.week import (
    CookingEventCreate,
    CookingEventResponse,
    CookingEventUpdate,
    CookingRhythmResponse,
    MealSlotCreate,
    MealSlotResponse,
    MealSlotUpdate,
    WeekSkeletonCreate,
    WeekSkeletonResponse,
    WeekSkeletonSummary,
    WeekSkeletonUpdate,
)
from carmy.models.cooking_event import CookingEvent
from carmy.models.cooking_rhythm import CookingRhythm
from carmy.models.meal import Meal
from carmy.models.meal_slot import MealSlot
from carmy.models.week_skeleton import WeekSkeleton

router = APIRouter(prefix="/weeks", tags=["weeks"])


def _get_skeleton_with_relationships(db: Session, year: int, week: int):
    """Get a week skeleton with all relationships eager loaded."""
    return db.execute(
        select(WeekSkeleton)
        .where(WeekSkeleton.year == year, WeekSkeleton.week_number == week)
        .options(
            selectinload(WeekSkeleton.cooking_events).selectinload(CookingEvent.meal),
            selectinload(WeekSkeleton.meal_slots).selectinload(MealSlot.meal),
        )
    ).scalar_one_or_none()


def _skeleton_to_dict(skeleton) -> dict:
    """Convert a WeekSkeleton to a response dict with meal names."""
    return {
        "id": skeleton.id,
        "year": skeleton.year,
        "week_number": skeleton.week_number,
        "start_date": skeleton.start_date,
        "end_date": skeleton.end_date,
        "notes": skeleton.notes,
        "month_plan_id": skeleton.month_plan_id,
        "status": skeleton.status,
        "created_at": skeleton.created_at,
        "updated_at": skeleton.updated_at,
        "cooking_events": [
            {
                "id": e.id,
                "week_skeleton_id": e.week_skeleton_id,
                "meal_id": e.meal_id,
                "cook_date": e.cook_date,
                "cook_time": e.cook_time,
                "serves_days": e.serves_days,
                "portions": e.portions,
                "effort_level": e.effort_level,
                "event_type": e.event_type,
                "was_made": e.was_made,
                "rating": e.rating,
                "notes": e.notes,
                "meal_name": e.meal.name if e.meal else None,
                "meal_nev": e.meal.nev if e.meal else None,
            }
            for e in skeleton.cooking_events
        ],
        "meal_slots": [
            {
                "id": s.id,
                "week_skeleton_id": s.week_skeleton_id,
                "date": s.date,
                "meal_time": s.meal_time,
                "meal_id": s.meal_id,
                "source": s.source,
                "cooking_event_id": s.cooking_event_id,
                "leftover_day": s.leftover_day,
                "status": s.status,
                "notes": s.notes,
                "meal_name": s.meal.name if s.meal else None,
                "meal_nev": s.meal.nev if s.meal else None,
            }
            for s in skeleton.meal_slots
        ],
    }


def get_week_dates(year: int, week: int) -> tuple[date, date]:
    """Get start and end dates for ISO week."""
    jan_4 = date(year, 1, 4)
    start_of_week_1 = jan_4 - timedelta(days=jan_4.weekday())
    start_date = start_of_week_1 + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    return start_date, end_date


# ============== WEEK SKELETON ENDPOINTS ==============

@router.get("", response_model=list[WeekSkeletonSummary])
def list_week_skeletons(
    year: int | None = Query(None, description="Filter by year"),
    month_plan_id: int | None = Query(None, description="Filter by month plan"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List week skeletons."""
    query = select(WeekSkeleton).order_by(
        WeekSkeleton.year.desc(), WeekSkeleton.week_number.desc()
    )

    if year:
        query = query.where(WeekSkeleton.year == year)
    if month_plan_id:
        query = query.where(WeekSkeleton.month_plan_id == month_plan_id)

    query = query.limit(limit)
    skeletons = db.execute(query).scalars().all()

    return [
        {
            "id": s.id,
            "year": s.year,
            "week_number": s.week_number,
            "start_date": s.start_date,
            "end_date": s.end_date,
            "status": s.status,
            "month_plan_id": s.month_plan_id,
            "cooking_event_count": len(s.cooking_events),
            "meal_slot_count": len(s.meal_slots),
        }
        for s in skeletons
    ]


@router.post("", response_model=WeekSkeletonResponse)
def create_week_skeleton(
    data: WeekSkeletonCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Create a new week skeleton."""
    # Check if skeleton already exists
    existing = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == data.year,
            WeekSkeleton.week_number == data.week_number,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Week skeleton for {data.year}-W{data.week_number} already exists"
        )

    start_date, end_date = get_week_dates(data.year, data.week_number)

    skeleton = WeekSkeleton(
        year=data.year,
        week_number=data.week_number,
        start_date=start_date,
        end_date=end_date,
        month_plan_id=data.month_plan_id,
        notes=data.notes,
    )
    db.add(skeleton)
    db.commit()
    db.refresh(skeleton)
    return _skeleton_to_dict(skeleton)


@router.get("/current", response_model=WeekSkeletonResponse)
def get_current_week_skeleton(db: Session = Depends(get_db)) -> dict:
    """Get the current week's skeleton."""
    today = date.today()
    iso = today.isocalendar()
    year, week = iso[0], iso[1]

    skeleton = _get_skeleton_with_relationships(db, year, week)

    if not skeleton:
        raise HTTPException(
            status_code=404,
            detail=f"No skeleton for {year}-W{week}"
        )

    return _skeleton_to_dict(skeleton)


@router.get("/{year}/{week}", response_model=WeekSkeletonResponse)
def get_week_skeleton(
    year: int,
    week: int,
    db: Session = Depends(get_db),
) -> dict:
    """Get a specific week skeleton."""
    skeleton = _get_skeleton_with_relationships(db, year, week)

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    return _skeleton_to_dict(skeleton)


@router.patch("/{year}/{week}", response_model=WeekSkeletonResponse)
def update_week_skeleton(
    year: int,
    week: int,
    data: WeekSkeletonUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Update a week skeleton."""
    skeleton = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == year, WeekSkeleton.week_number == week
        )
    ).scalar_one_or_none()

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    if data.month_plan_id is not None:
        skeleton.month_plan_id = data.month_plan_id
    if data.status is not None:
        skeleton.status = data.status
    if data.notes is not None:
        skeleton.notes = data.notes

    db.commit()
    db.refresh(skeleton)
    return _skeleton_to_dict(skeleton)


@router.delete("/{year}/{week}")
def delete_week_skeleton(
    year: int,
    week: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a week skeleton."""
    skeleton = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == year, WeekSkeleton.week_number == week
        )
    ).scalar_one_or_none()

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    db.delete(skeleton)
    db.commit()
    return {"success": True, "deleted": f"{year}-W{week}"}


# ============== COOKING EVENT ENDPOINTS ==============

@router.get("/{year}/{week}/events", response_model=list[CookingEventResponse])
def list_cooking_events(
    year: int,
    week: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    """List cooking events for a week."""
    skeleton = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == year, WeekSkeleton.week_number == week
        )
    ).scalar_one_or_none()

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    return [
        {
            "id": e.id,
            "week_skeleton_id": e.week_skeleton_id,
            "meal_id": e.meal_id,
            "cook_date": e.cook_date,
            "cook_time": e.cook_time,
            "serves_days": e.serves_days,
            "portions": e.portions,
            "effort_level": e.effort_level,
            "event_type": e.event_type,
            "was_made": e.was_made,
            "rating": e.rating,
            "notes": e.notes,
            "meal_name": e.meal.name if e.meal else None,
            "meal_nev": e.meal.nev if e.meal else None,
        }
        for e in skeleton.cooking_events
    ]


@router.post("/{year}/{week}/events", response_model=CookingEventResponse)
def create_cooking_event(
    year: int,
    week: int,
    data: CookingEventCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Create a cooking event for a week."""
    skeleton = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == year, WeekSkeleton.week_number == week
        )
    ).scalar_one_or_none()

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    # Verify meal exists
    meal = db.execute(select(Meal).where(Meal.id == data.meal_id)).scalar_one_or_none()
    if not meal:
        raise HTTPException(status_code=404, detail=f"Meal {data.meal_id} not found")

    event = CookingEvent(
        week_skeleton_id=skeleton.id,
        meal_id=data.meal_id,
        cook_date=data.cook_date,
        cook_time=data.cook_time,
        serves_days=data.serves_days,
        portions=data.portions,
        effort_level=data.effort_level or meal.effort_level,
        event_type=data.event_type,
        notes=data.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "week_skeleton_id": event.week_skeleton_id,
        "meal_id": event.meal_id,
        "cook_date": event.cook_date,
        "cook_time": event.cook_time,
        "serves_days": event.serves_days,
        "portions": event.portions,
        "effort_level": event.effort_level,
        "event_type": event.event_type,
        "was_made": event.was_made,
        "rating": event.rating,
        "notes": event.notes,
        "meal_name": meal.name,
        "meal_nev": meal.nev,
    }


@router.patch("/events/{event_id}", response_model=CookingEventResponse)
def update_cooking_event(
    event_id: int,
    data: CookingEventUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Update a cooking event."""
    event = db.execute(
        select(CookingEvent).where(CookingEvent.id == event_id)
    ).scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Cooking event not found")

    if data.meal_id is not None:
        event.meal_id = data.meal_id
    if data.cook_date is not None:
        event.cook_date = data.cook_date
    if data.cook_time is not None:
        event.cook_time = data.cook_time
    if data.serves_days is not None:
        event.serves_days = data.serves_days
    if data.portions is not None:
        event.portions = data.portions
    if data.effort_level is not None:
        event.effort_level = data.effort_level
    if data.event_type is not None:
        event.event_type = data.event_type
    if data.was_made is not None:
        event.was_made = data.was_made
    if data.rating is not None:
        event.rating = data.rating
    if data.notes is not None:
        event.notes = data.notes

    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "week_skeleton_id": event.week_skeleton_id,
        "meal_id": event.meal_id,
        "cook_date": event.cook_date,
        "cook_time": event.cook_time,
        "serves_days": event.serves_days,
        "portions": event.portions,
        "effort_level": event.effort_level,
        "event_type": event.event_type,
        "was_made": event.was_made,
        "rating": event.rating,
        "notes": event.notes,
        "meal_name": event.meal.name if event.meal else None,
        "meal_nev": event.meal.nev if event.meal else None,
    }


@router.delete("/events/{event_id}")
def delete_cooking_event(
    event_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a cooking event."""
    event = db.execute(
        select(CookingEvent).where(CookingEvent.id == event_id)
    ).scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Cooking event not found")

    db.delete(event)
    db.commit()
    return {"success": True, "deleted_id": event_id}


# ============== MEAL SLOT ENDPOINTS ==============

@router.get("/{year}/{week}/slots", response_model=list[MealSlotResponse])
def list_meal_slots(
    year: int,
    week: int,
    db: Session = Depends(get_db),
) -> list[dict]:
    """List meal slots for a week."""
    skeleton = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == year, WeekSkeleton.week_number == week
        )
    ).scalar_one_or_none()

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    return [
        {
            "id": s.id,
            "week_skeleton_id": s.week_skeleton_id,
            "date": s.date,
            "meal_time": s.meal_time,
            "meal_id": s.meal_id,
            "source": s.source,
            "cooking_event_id": s.cooking_event_id,
            "leftover_day": s.leftover_day,
            "status": s.status,
            "notes": s.notes,
            "meal_name": s.meal.name if s.meal else None,
            "meal_nev": s.meal.nev if s.meal else None,
        }
        for s in skeleton.meal_slots
    ]


@router.post("/{year}/{week}/slots", response_model=MealSlotResponse)
def create_meal_slot(
    year: int,
    week: int,
    data: MealSlotCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Create a meal slot for a week."""
    skeleton = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == year, WeekSkeleton.week_number == week
        )
    ).scalar_one_or_none()

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    # Check if slot already exists
    existing = db.execute(
        select(MealSlot).where(
            MealSlot.date == data.date, MealSlot.meal_time == data.meal_time
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Slot for {data.date} {data.meal_time} already exists"
        )

    meal = None
    if data.meal_id:
        meal = db.execute(select(Meal).where(Meal.id == data.meal_id)).scalar_one_or_none()

    slot = MealSlot(
        week_skeleton_id=skeleton.id,
        date=data.date,
        meal_time=data.meal_time,
        meal_id=data.meal_id,
        source=data.source,
        cooking_event_id=data.cooking_event_id,
        leftover_day=data.leftover_day,
        notes=data.notes,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    return {
        "id": slot.id,
        "week_skeleton_id": slot.week_skeleton_id,
        "date": slot.date,
        "meal_time": slot.meal_time,
        "meal_id": slot.meal_id,
        "source": slot.source,
        "cooking_event_id": slot.cooking_event_id,
        "leftover_day": slot.leftover_day,
        "status": slot.status,
        "notes": slot.notes,
        "meal_name": meal.name if meal else None,
        "meal_nev": meal.nev if meal else None,
    }


@router.patch("/slots/{slot_id}", response_model=MealSlotResponse)
def update_meal_slot(
    slot_id: int,
    data: MealSlotUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Update a meal slot."""
    slot = db.execute(
        select(MealSlot).where(MealSlot.id == slot_id)
    ).scalar_one_or_none()

    if not slot:
        raise HTTPException(status_code=404, detail="Meal slot not found")

    if data.meal_id is not None:
        slot.meal_id = data.meal_id
    if data.source is not None:
        slot.source = data.source
    if data.cooking_event_id is not None:
        slot.cooking_event_id = data.cooking_event_id
    if data.leftover_day is not None:
        slot.leftover_day = data.leftover_day
    if data.status is not None:
        slot.status = data.status
    if data.notes is not None:
        slot.notes = data.notes

    db.commit()
    db.refresh(slot)

    return {
        "id": slot.id,
        "week_skeleton_id": slot.week_skeleton_id,
        "date": slot.date,
        "meal_time": slot.meal_time,
        "meal_id": slot.meal_id,
        "source": slot.source,
        "cooking_event_id": slot.cooking_event_id,
        "leftover_day": slot.leftover_day,
        "status": slot.status,
        "notes": slot.notes,
        "meal_name": slot.meal.name if slot.meal else None,
        "meal_nev": slot.meal.nev if slot.meal else None,
    }


@router.delete("/slots/{slot_id}")
def delete_meal_slot(
    slot_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a meal slot."""
    slot = db.execute(
        select(MealSlot).where(MealSlot.id == slot_id)
    ).scalar_one_or_none()

    if not slot:
        raise HTTPException(status_code=404, detail="Meal slot not found")

    db.delete(slot)
    db.commit()
    return {"success": True, "deleted_id": slot_id}


@router.post("/slots/{slot_id}/status")
def update_slot_status(
    slot_id: int,
    status: str = Query(..., description="New status: planned, completed, skipped"),
    db: Session = Depends(get_db),
) -> dict:
    """Quick update of just the slot status."""
    valid_statuses = ["planned", "completed", "skipped"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    slot = db.execute(
        select(MealSlot).where(MealSlot.id == slot_id)
    ).scalar_one_or_none()

    if not slot:
        raise HTTPException(status_code=404, detail="Meal slot not found")

    slot.status = status
    db.commit()

    return {"success": True, "id": slot_id, "status": status}


# ============== MATERIALIZATION ENDPOINTS ==============

@router.post("/{year}/{week}/materialize")
def materialize_week(
    year: int,
    week: int,
    include_lunch: bool = Query(True, description="Include lunch slots"),
    include_soup: bool = Query(True, description="Include soup slots"),
    db: Session = Depends(get_db),
) -> dict:
    """Materialize a week skeleton into daily meal slots.

    This transforms cooking events into actual meal slots:
    - Fresh meals on cooking days
    - Leftover chains for subsequent days
    - Lunch assignments from leftovers
    - Soup slots as parallel track
    """
    from carmy.services.week_materializer import WeekMaterializer

    skeleton = db.execute(
        select(WeekSkeleton).where(
            WeekSkeleton.year == year, WeekSkeleton.week_number == week
        )
    ).scalar_one_or_none()

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    materializer = WeekMaterializer(db)
    materialized, slots = materializer.materialize_and_save(
        skeleton, include_lunch=include_lunch, include_soup=include_soup
    )

    return {
        "success": True,
        "year": year,
        "week": week,
        "slots_created": materialized.slots_created,
        "warnings": materialized.warnings,
        "summary": materializer.get_week_summary(skeleton),
    }


@router.get("/{year}/{week}/summary")
def get_week_summary(
    year: int,
    week: int,
    db: Session = Depends(get_db),
) -> dict:
    """Get a summary of a week's meal plan."""
    from carmy.services.week_materializer import WeekMaterializer

    skeleton = _get_skeleton_with_relationships(db, year, week)

    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    materializer = WeekMaterializer(db)
    summary = materializer.get_week_summary(skeleton)

    return {
        "year": year,
        "week": week,
        "status": skeleton.status,
        **summary,
    }


# ============== EXPORT ENDPOINTS ==============

@router.get("/{year}/{week}/export/ics")
def export_week_ics(
    year: int,
    week: int,
    db: Session = Depends(get_db),
):
    """Export week as ICS calendar file."""
    from fastapi.responses import Response
    from carmy.services.export import V2ExportService

    skeleton = _get_skeleton_with_relationships(db, year, week)
    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    export_service = V2ExportService(db)
    ics_content = export_service.generate_week_ics(skeleton)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=carmy-week-{year}-{week}.ics"}
    )


@router.get("/{year}/{week}/export/json")
def export_week_json(
    year: int,
    week: int,
    db: Session = Depends(get_db),
):
    """Export week as JSON."""
    from fastapi.responses import Response
    from carmy.services.export import V2ExportService

    skeleton = _get_skeleton_with_relationships(db, year, week)
    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    export_service = V2ExportService(db)
    json_content = export_service.generate_week_json(skeleton)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=carmy-week-{year}-{week}.json"}
    )


@router.get("/{year}/{week}/export/markdown")
def export_week_markdown(
    year: int,
    week: int,
    db: Session = Depends(get_db),
):
    """Export week as Markdown."""
    from fastapi.responses import Response
    from carmy.services.export import V2ExportService

    skeleton = _get_skeleton_with_relationships(db, year, week)
    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    export_service = V2ExportService(db)
    md_content = export_service.generate_week_markdown(skeleton)

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=carmy-week-{year}-{week}.md"}
    )


@router.get("/{year}/{week}/export/html")
def export_week_html(
    year: int,
    week: int,
    db: Session = Depends(get_db),
):
    """Export week as standalone HTML (for printing/sharing)."""
    from fastapi.responses import HTMLResponse
    from carmy.services.export import V2ExportService

    skeleton = _get_skeleton_with_relationships(db, year, week)
    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    export_service = V2ExportService(db)
    html_content = export_service.generate_week_html(skeleton)

    return HTMLResponse(content=html_content)


@router.get("/{year}/{week}/export/shopping")
def export_week_shopping(
    year: int,
    week: int,
    format: str = Query("text", description="Format: text, markdown, json"),
    db: Session = Depends(get_db),
):
    """Export shopping list for the week."""
    from fastapi.responses import Response
    from carmy.services.export import V2ExportService

    skeleton = _get_skeleton_with_relationships(db, year, week)
    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    export_service = V2ExportService(db)
    shopping_list = export_service.generate_shopping_list(skeleton)

    if format == "markdown":
        return Response(
            content=shopping_list.to_markdown(),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=shopping-week-{year}-{week}.md"}
        )
    elif format == "json":
        import json
        data = {
            "year": shopping_list.year,
            "week": shopping_list.week_number,
            "fresh_meals": shopping_list.fresh_meals,
            "leftover_meals": shopping_list.leftover_meals,
            "items": [
                {"name": item.name, "category": item.category}
                for item in shopping_list.items
            ],
        }
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=shopping-week-{year}-{week}.json"}
        )
    else:
        return Response(
            content=shopping_list.to_text(),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=shopping-week-{year}-{week}.txt"}
        )


@router.get("/{year}/{week}/share")
def get_share_info(
    year: int,
    week: int,
    db: Session = Depends(get_db),
) -> dict:
    """Get share token and links for a week."""
    from carmy.services.export import V2ExportService

    skeleton = _get_skeleton_with_relationships(db, year, week)
    if not skeleton:
        raise HTTPException(status_code=404, detail=f"No skeleton for {year}-W{week}")

    export_service = V2ExportService(db)
    token = export_service.generate_share_token(skeleton)

    return {
        "year": year,
        "week": week,
        "share_token": token,
        "export_links": {
            "ics": f"/api/weeks/{year}/{week}/export/ics",
            "json": f"/api/weeks/{year}/{week}/export/json",
            "markdown": f"/api/weeks/{year}/{week}/export/markdown",
            "html": f"/api/weeks/{year}/{week}/export/html",
            "shopping_text": f"/api/weeks/{year}/{week}/export/shopping?format=text",
            "shopping_markdown": f"/api/weeks/{year}/{week}/export/shopping?format=markdown",
        },
    }


# ============== COOKING RHYTHM ENDPOINT ==============

@router.get("/rhythm", response_model=list[CookingRhythmResponse])
def get_cooking_rhythm(db: Session = Depends(get_db)) -> list[dict]:
    """Get the learned cooking rhythm patterns."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    rhythms = db.execute(
        select(CookingRhythm).order_by(CookingRhythm.day_of_week)
    ).scalars().all()

    return [
        {
            "id": r.id,
            "day_of_week": r.day_of_week,
            "day_name": days[r.day_of_week],
            "cook_probability": r.cook_probability,
            "typical_effort": r.typical_effort,
            "typical_types": r.typical_types or [],
            "confidence": r.confidence,
            "calculated_at": r.calculated_at,
        }
        for r in rhythms
    ]
