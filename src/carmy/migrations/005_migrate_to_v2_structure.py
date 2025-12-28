"""Migrate historical data from v1 to v2 structure.

Migration: 005
Date: 2024-12-28

Migrates:
- WeeklyPlan -> WeekSkeleton (without MonthPlan linkage for now)
- PlanMeal -> MealSlot + CookingEvent
- Generates CookingRhythm from historical patterns
"""

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def upgrade(engine: Engine) -> None:
    """Migrate historical data to v2 structure."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Step 1: Migrate WeeklyPlans to WeekSkeletons
        _migrate_weekly_plans(session)

        # Step 2: Migrate PlanMeals to MealSlots and CookingEvents
        _migrate_plan_meals(session)

        # Step 3: Generate CookingRhythm from patterns
        _generate_cooking_rhythm(session)

        session.commit()
        print("Migration completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        session.close()


def _migrate_weekly_plans(session: Session) -> None:
    """Migrate WeeklyPlans to WeekSkeletons."""
    print("Migrating WeeklyPlans to WeekSkeletons...")

    # Get all weekly plans
    result = session.execute(text("""
        SELECT id, year, week_number, start_date, notes, created_at
        FROM weekly_plans
        ORDER BY year, week_number
    """))

    count = 0
    for row in result:
        plan_id, year, week_number, start_date, notes, created_at = row

        # Calculate end_date (6 days after start)
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        end_date = start_date + timedelta(days=6)

        # Check if skeleton already exists
        existing = session.execute(text("""
            SELECT id FROM week_skeletons WHERE year = :year AND week_number = :week
        """), {"year": year, "week": week_number}).fetchone()

        if existing:
            continue

        # Create WeekSkeleton
        session.execute(text("""
            INSERT INTO week_skeletons
            (year, week_number, start_date, end_date, status, notes, created_at)
            VALUES (:year, :week, :start, :end, 'completed', :notes, :created)
        """), {
            "year": year,
            "week": week_number,
            "start": start_date.isoformat() if isinstance(start_date, date) else start_date,
            "end": end_date.isoformat(),
            "notes": notes,
            "created": created_at,
        })
        count += 1

    print(f"  Created {count} WeekSkeletons")


def _migrate_plan_meals(session: Session) -> None:
    """Migrate PlanMeals to MealSlots and CookingEvents."""
    print("Migrating PlanMeals to MealSlots and CookingEvents...")

    # Build mapping from weekly_plan to week_skeleton
    skeleton_map = {}
    skeletons = session.execute(text("""
        SELECT id, year, week_number, start_date FROM week_skeletons
    """))
    for row in skeletons:
        skeleton_map[(row[1], row[2])] = {"id": row[0], "start_date": row[3]}

    # Get plan to year/week mapping
    plan_map = {}
    plans = session.execute(text("""
        SELECT id, year, week_number FROM weekly_plans
    """))
    for row in plans:
        plan_map[row[0]] = (row[1], row[2])

    # Get all plan_meals with their meal info
    result = session.execute(text("""
        SELECT pm.id, pm.plan_id, pm.meal_id, pm.day_of_week, pm.meal_slot,
               pm.is_leftover, pm.notes, m.effort_level
        FROM plan_meals pm
        LEFT JOIN meals m ON pm.meal_id = m.id
        ORDER BY pm.plan_id, pm.day_of_week, pm.meal_slot
    """))

    meal_slot_count = 0
    cooking_event_count = 0

    # Group meals by plan and day to identify cooking events
    meals_by_plan_day = defaultdict(list)
    for row in result:
        pm_id, plan_id, meal_id, day_of_week, meal_slot, is_leftover, notes, effort_level = row
        meals_by_plan_day[(plan_id, day_of_week)].append({
            "pm_id": pm_id,
            "meal_id": meal_id,
            "meal_slot": meal_slot or "lunch",  # Default to lunch
            "is_leftover": is_leftover,
            "notes": notes,
            "effort_level": effort_level or "medium",
        })

    # Process each plan/day combination
    for (plan_id, day_of_week), meals in meals_by_plan_day.items():
        if plan_id not in plan_map:
            continue

        year, week = plan_map[plan_id]
        if (year, week) not in skeleton_map:
            continue

        skeleton_info = skeleton_map[(year, week)]
        skeleton_id = skeleton_info["id"]
        start_date = skeleton_info["start_date"]

        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        # Calculate actual date
        if day_of_week is not None:
            meal_date = start_date + timedelta(days=day_of_week)
        else:
            # No day assigned, put on first day
            meal_date = start_date

        # Group by meal_id to create cooking events
        fresh_meals = [m for m in meals if not m["is_leftover"] and m["meal_id"]]
        leftover_meals = [m for m in meals if m["is_leftover"]]

        # Create cooking events for fresh meals
        cooking_event_map = {}  # meal_id -> cooking_event_id
        for meal in fresh_meals:
            if meal["meal_id"] in cooking_event_map:
                continue  # Already created event for this meal

            # Create cooking event
            session.execute(text("""
                INSERT INTO cooking_events
                (week_skeleton_id, meal_id, cook_date, serves_days, portions,
                 effort_level, event_type, was_made)
                VALUES (:skeleton_id, :meal_id, :cook_date, 1, 4,
                        :effort, 'regular', 1)
            """), {
                "skeleton_id": skeleton_id,
                "meal_id": meal["meal_id"],
                "cook_date": meal_date.isoformat(),
                "effort": meal["effort_level"],
            })
            cooking_event_count += 1

            # Get the created event ID
            event_id = session.execute(text("SELECT last_insert_rowid()")).scalar()
            cooking_event_map[meal["meal_id"]] = event_id

        # Create meal slots for all meals
        for meal in meals:
            meal_slot = meal["meal_slot"] or "lunch"
            source = "leftover" if meal["is_leftover"] else "fresh"
            cooking_event_id = cooking_event_map.get(meal["meal_id"]) if not meal["is_leftover"] else None

            # Check if slot already exists
            existing = session.execute(text("""
                SELECT id FROM meal_slots
                WHERE date = :date AND meal_time = :time
            """), {"date": meal_date.isoformat(), "time": meal_slot}).fetchone()

            if existing:
                # Update existing slot if needed
                continue

            session.execute(text("""
                INSERT INTO meal_slots
                (week_skeleton_id, date, meal_time, meal_id, source,
                 cooking_event_id, status, notes)
                VALUES (:skeleton_id, :date, :time, :meal_id, :source,
                        :event_id, 'completed', :notes)
            """), {
                "skeleton_id": skeleton_id,
                "date": meal_date.isoformat(),
                "time": meal_slot,
                "meal_id": meal["meal_id"],
                "source": source,
                "event_id": cooking_event_id,
                "notes": meal["notes"],
            })
            meal_slot_count += 1

    print(f"  Created {cooking_event_count} CookingEvents")
    print(f"  Created {meal_slot_count} MealSlots")


def _generate_cooking_rhythm(session: Session) -> None:
    """Generate CookingRhythm from historical cooking patterns."""
    print("Generating CookingRhythm from history...")

    # Analyze cooking events by day of week
    result = session.execute(text("""
        SELECT
            CAST(strftime('%w', cook_date) AS INTEGER) as dow,
            COUNT(*) as cook_count,
            effort_level
        FROM cooking_events
        GROUP BY dow, effort_level
    """))

    # Collect stats per day
    day_stats = defaultdict(lambda: {"total": 0, "efforts": defaultdict(int)})
    for row in result:
        # SQLite %w: 0=Sunday, 1=Monday, etc. Convert to 0=Monday
        sqlite_dow = row[0]
        dow = (sqlite_dow - 1) % 7  # Convert to Monday=0
        count = row[1]
        effort = row[2]

        day_stats[dow]["total"] += count
        day_stats[dow]["efforts"][effort] += count

    # Calculate total events for probability
    total_events = sum(d["total"] for d in day_stats.values())
    if total_events == 0:
        print("  No cooking events found, skipping rhythm generation")
        return

    # Create rhythm entries for each day
    for dow in range(7):
        stats = day_stats[dow]
        cook_prob = stats["total"] / total_events * 7 if total_events > 0 else 0.5  # Normalize
        cook_prob = min(1.0, cook_prob)  # Cap at 1.0

        # Find typical effort
        efforts = stats["efforts"]
        typical_effort = max(efforts, key=efforts.get) if efforts else None

        # Typical types based on day
        typical_types = []
        if dow == 4:  # Friday
            typical_types = ["fun_food"]
        elif dow == 5:  # Saturday
            typical_types = ["big_cook"]
        elif dow == 1:  # Tuesday
            typical_types = ["fozelek", "main_course"]

        # Check if entry exists
        existing = session.execute(text("""
            SELECT id FROM cooking_rhythm WHERE day_of_week = :dow
        """), {"dow": dow}).fetchone()

        if existing:
            session.execute(text("""
                UPDATE cooking_rhythm
                SET cook_probability = :prob, typical_effort = :effort,
                    typical_types = :types, confidence = :conf
                WHERE day_of_week = :dow
            """), {
                "dow": dow,
                "prob": cook_prob,
                "effort": typical_effort,
                "types": str(typical_types),
                "conf": min(0.9, stats["total"] / 20),  # More data = more confidence
            })
        else:
            session.execute(text("""
                INSERT INTO cooking_rhythm
                (day_of_week, cook_probability, typical_effort, typical_types, confidence)
                VALUES (:dow, :prob, :effort, :types, :conf)
            """), {
                "dow": dow,
                "prob": cook_prob,
                "effort": typical_effort,
                "types": str(typical_types),
                "conf": min(0.9, stats["total"] / 20),
            })

    print("  Created CookingRhythm for all 7 days")


def downgrade(engine: Engine) -> None:
    """Remove migrated data from v2 tables (keeps original v1 data)."""
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM cooking_rhythm"))
        conn.execute(text("DELETE FROM meal_slots"))
        conn.execute(text("DELETE FROM cooking_events"))
        conn.execute(text("DELETE FROM week_skeletons"))
        conn.commit()
