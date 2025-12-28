# Phase 8: Planning Board - Test Plan

## Overview
This document describes test cases for the Planning Board feature (Phase 8) of the Carmy meal planner application.

## Test Environment Setup

```bash
# Install test dependencies
pip install httpx pytest pytest-asyncio

# Run all tests
pytest tests/test_board.py -v
```

---

## 1. Board API Endpoints

### 1.1 Weekly Board API

| Test ID | Endpoint | Method | Description | Expected |
|---------|----------|--------|-------------|----------|
| API-W1 | `/api/board/week/{year}/{week}` | GET | Get board data for specific week | 200, BoardData schema |
| API-W2 | `/api/board/current` | GET | Get current week's board | 200, BoardData schema |
| API-W3 | `/api/board/week/2024/53` | GET | Invalid week number | Handle gracefully |

### 1.2 Monthly Board API

| Test ID | Endpoint | Method | Description | Expected |
|---------|----------|--------|-------------|----------|
| API-M1 | `/api/board/month/{year}/{month}` | GET | Get board data for specific month | 200, MonthBoardData schema |
| API-M2 | `/api/board/month/current` | GET | Get current month's board | 200, MonthBoardData schema |
| API-M3 | `/api/board/month/2024/13` | GET | Invalid month number | 422 or error handling |

### 1.3 Slot Operations API

| Test ID | Endpoint | Method | Description | Expected |
|---------|----------|--------|-------------|----------|
| API-S1 | `/api/board/slot` | POST | Assign meal to slot (single) | 200, slot created |
| API-S2 | `/api/board/slot` | POST | Assign meal with chain | 200, chain created |
| API-S3 | `/api/board/slot/{id}` | PUT | Move meal to different slot | 200, slot updated |
| API-S4 | `/api/board/slot/{id}` | DELETE | Remove meal from slot | 200, slot deleted |
| API-S5 | `/api/board/slot/{id}?break_chain=true` | DELETE | Remove entire chain | 200, chain deleted |

### 1.4 Chain Operations API

| Test ID | Endpoint | Method | Description | Expected |
|---------|----------|--------|-------------|----------|
| API-C1 | `/api/board/chain/{chain_id}/extend` | POST | Extend leftover chain | 200, days added |
| API-C2 | `/api/board/chain/{chain_id}/shrink` | POST | Shrink leftover chain | 200, day removed |
| API-C3 | `/api/board/chain/{chain_id}` | DELETE | Delete entire chain | 200, chain deleted |

### 1.5 Search API

| Test ID | Endpoint | Method | Description | Expected |
|---------|----------|--------|-------------|----------|
| API-SR1 | `/api/board/search?q=soup` | GET | Search meals by name | 200, list of PoolMeal |
| API-SR2 | `/api/board/search?q=a` | GET | Search with < 2 chars | 200, empty list |
| API-SR3 | `/htmx/board/search?q=soup` | GET | HTMX search endpoint | 200, HTML fragment |

---

## 2. Page Routes

### 2.1 Weekly View Pages

| Test ID | Route | Description | Expected |
|---------|-------|-------------|----------|
| PG-W1 | `/board` | Board home (current week) | 200, week.html rendered |
| PG-W2 | `/board/week/2024/52` | Specific week | 200, week.html with data |

### 2.2 Monthly View Pages

| Test ID | Route | Description | Expected |
|---------|-------|-------------|----------|
| PG-M1 | `/board/month` | Current month | 200, month.html rendered |
| PG-M2 | `/board/month/2024/12` | Specific month | 200, month.html with data |

---

## 3. UI Component Tests

### 3.1 Weekly View UI

| Test ID | Component | Action | Expected |
|---------|-----------|--------|----------|
| UI-W1 | View Toggle | Click "Weekly" | Active state, stays on weekly |
| UI-W2 | View Toggle | Click "Monthly" | Navigate to /board/month |
| UI-W3 | Navigation | Click "Prev" | Navigate to previous week |
| UI-W4 | Navigation | Click "Next" | Navigate to next week |
| UI-W5 | Navigation | Click "Today" | Navigate to current week |
| UI-W6 | Print Button | Click | Browser print dialog |
| UI-W7 | Week Grid | Render | 7 columns (Mon-Sun) x 4 rows (meal slots) |

### 3.2 Monthly View UI

| Test ID | Component | Action | Expected |
|---------|-----------|--------|----------|
| UI-M1 | View Toggle | Click "Monthly" | Active state, stays on monthly |
| UI-M2 | View Toggle | Click "Weekly" | Navigate to /board |
| UI-M3 | Navigation | Click "Prev" | Navigate to previous month |
| UI-M4 | Navigation | Click "Next" | Navigate to next month |
| UI-M5 | Filter Tabs | Click "All" | Show all meal types |
| UI-M6 | Filter Tabs | Click "Lunch" | Show only lunch meals |
| UI-M7 | Week Label | Click "W52" | Navigate to /board/week/2024/52 |
| UI-M8 | Month Grid | Render | Calendar layout with week rows |

### 3.3 Meal Pool UI

| Test ID | Component | Action | Expected |
|---------|-----------|--------|----------|
| UI-P1 | Search | Type "soup" | Filter/search results appear |
| UI-P2 | Search | Clear input | Restore original pool |
| UI-P3 | Section Header | Click | Toggle section collapse |
| UI-P4 | Pool Meal | Drag | Start drag operation |
| UI-P5 | Suggestions | Display | Shows seasonal meals |
| UI-P6 | Recently Used | Display | Shows recent meals |

---

## 4. Drag & Drop Tests

### 4.1 Pool to Slot

| Test ID | Action | Expected |
|---------|--------|----------|
| DD-1 | Drag single-portion meal to empty slot | Meal assigned, page reloads |
| DD-2 | Drag multi-portion meal to slot | Portion dialog appears |
| DD-3 | Portion dialog - "Fill X days" | Chain created across days |
| DD-4 | Portion dialog - "Just today" | Single meal assigned |
| DD-5 | Portion dialog - "Cancel" | No changes made |
| DD-6 | Drag to occupied slot | Replaces existing meal |

### 4.2 Slot to Slot

| Test ID | Action | Expected |
|---------|--------|----------|
| DD-7 | Drag meal between slots | Meal moved via API |
| DD-8 | Drag meal to occupied slot | Meals swap positions |

### 4.3 Remove Meal

| Test ID | Action | Expected |
|---------|--------|----------|
| DD-9 | Click X on meal card | Confirm dialog, meal removed |
| DD-10 | Remove meal from chain | Single meal removed |

---

## 5. Leftover Chain Tests

### 5.1 Chain Creation

| Test ID | Scenario | Expected |
|---------|----------|----------|
| CH-1 | Create 4-day chain from Monday | Mon (cook), Tue-Thu (leftover) |
| CH-2 | Create chain near end of week | Stops at Sunday |
| CH-3 | Chain portions countdown | 4, 3, 2, 1 portions |

### 5.2 Chain Visualization

| Test ID | Element | Expected |
|---------|---------|----------|
| CH-4 | First day (cook) | Green border, cook icon |
| CH-5 | Middle days | Yellow border, leftover icon |
| CH-6 | Last day | Red border, last icon |
| CH-7 | Portions badge | Color-coded (green/yellow/red) |

### 5.3 Chain Operations

| Test ID | Operation | Expected |
|---------|-----------|----------|
| CH-8 | Extend chain | New day added if slot free |
| CH-9 | Shrink chain | Last day removed |
| CH-10 | Delete chain | All linked meals removed |

---

## 6. Keyboard Shortcuts

### 6.1 Weekly View

| Test ID | Key | Expected |
|---------|-----|----------|
| KB-W1 | `P` | Open print dialog |
| KB-W2 | `←` | Navigate to previous week |
| KB-W3 | `→` | Navigate to next week |
| KB-W4 | `T` | Navigate to today |
| KB-W5 | `M` | Switch to monthly view |
| KB-W6 | `/` | Focus search input |
| KB-W7 | `?` | Toggle keyboard hints |
| KB-W8 | `Esc` | Blur search input |

### 6.2 Monthly View

| Test ID | Key | Expected |
|---------|-----|----------|
| KB-M1 | `P` | Open print dialog |
| KB-M2 | `←` | Navigate to previous month |
| KB-M3 | `→` | Navigate to next month |
| KB-M4 | `T` | Navigate to today |
| KB-M5 | `W` | Switch to weekly view |

---

## 7. Print Tests

| Test ID | Scenario | Expected |
|---------|----------|----------|
| PR-1 | Print weekly view | Grid visible, pool hidden |
| PR-2 | Print monthly view | Calendar visible, pool hidden |
| PR-3 | Chain colors | Preserved in print |
| PR-4 | Navigation elements | Hidden in print |

---

## 8. Edge Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| EC-1 | Week 1 navigation | Handles year rollover |
| EC-2 | Week 52/53 | Correct ISO week handling |
| EC-3 | January 1 | Correct month display |
| EC-4 | December 31 | Correct week assignment |
| EC-5 | Empty plan | No errors, empty slots shown |
| EC-6 | PlanMeal with null day_of_week | Skipped, no errors |
| EC-7 | PlanMeal with null meal_slot | Skipped, no errors |

---

## Test Data Requirements

### Meals (minimum for testing)
- 1 soup with `default_portions=4`
- 1 main course with `default_portions=1`
- 1 breakfast item
- Meals tagged with different seasonality

### Plans
- 1 plan for current week with some meals assigned
- 1 plan with a leftover chain

---

## Bug Fixes Applied

| Issue | Fix |
|-------|-----|
| Monthly view error with null day_of_week | Added null check in `get_month_board()` |
| Monthly view error with null meal_slot | Added null check in `get_month_board()` |

---

## Files Modified in Phase 8

### Models
- `src/carmy/models/meal.py` - Added `default_portions`, `keeps_days`
- `src/carmy/models/plan.py` - Added `portions_remaining`, `chain_id`, `cooked_on_date`

### Migrations
- `src/carmy/migrations/001_add_portions_keeps_days.py`
- `src/carmy/migrations/002_add_plan_meal_chain_fields.py`

### API Routes
- `src/carmy/api/routes/board.py` - All board API endpoints
- `src/carmy/api/routes/htmx.py` - Board search HTMX endpoint
- `src/carmy/api/routes/pages.py` - Board page routes

### Schemas
- `src/carmy/api/schemas/board.py` - Board-specific Pydantic schemas

### Templates
- `src/carmy/api/templates/board/week.html` - Weekly view
- `src/carmy/api/templates/board/month.html` - Monthly view
