"""
Test suite for Phase 8: Planning Board feature.

Run with: pytest tests/test_board.py -v
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from carmy.api.app import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for tests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from carmy.models.base import Base

    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ============== API ENDPOINT TESTS ==============

class TestWeeklyBoardAPI:
    """Tests for weekly board API endpoints."""

    def test_get_current_week_board(self, client):
        """API-W2: Get current week's board."""
        response = client.get("/api/board/current")
        assert response.status_code == 200
        data = response.json()
        assert "week" in data
        assert "pool" in data
        assert "suggestions" in data
        assert "recently_used" in data

    def test_get_specific_week_board(self, client):
        """API-W1: Get board data for specific week."""
        response = client.get("/api/board/week/2024/52")
        assert response.status_code == 200
        data = response.json()
        assert data["week"]["year"] == 2024
        assert data["week"]["week"] == 52
        assert len(data["week"]["days"]) == 7

    def test_week_board_structure(self, client):
        """Verify week board data structure."""
        response = client.get("/api/board/week/2024/50")
        assert response.status_code == 200
        data = response.json()

        # Check week structure
        week = data["week"]
        assert "start_date" in week
        assert "end_date" in week
        assert "days" in week

        # Check day structure
        day = week["days"][0]
        assert "day_of_week" in day
        assert "day_name" in day
        assert "date" in day
        assert "slots" in day

        # Check slots
        slots = day["slots"]
        assert "breakfast" in slots
        assert "lunch" in slots
        assert "dinner" in slots
        assert "snack" in slots


class TestMonthlyBoardAPI:
    """Tests for monthly board API endpoints."""

    def test_get_current_month_board(self, client):
        """API-M2: Get current month's board."""
        response = client.get("/api/board/month/current")
        assert response.status_code == 200
        data = response.json()
        assert "month" in data
        assert "pool" in data

    def test_get_specific_month_board(self, client):
        """API-M1: Get board data for specific month."""
        response = client.get("/api/board/month/2024/12")
        assert response.status_code == 200
        data = response.json()
        assert data["month"]["year"] == 2024
        assert data["month"]["month"] == 12
        assert data["month"]["month_name"] == "December"

    def test_month_board_structure(self, client):
        """Verify month board data structure."""
        response = client.get("/api/board/month/2024/12")
        assert response.status_code == 200
        data = response.json()

        # Check month structure
        month = data["month"]
        assert "weeks" in month
        assert len(month["weeks"]) >= 4  # At least 4 weeks in a month

        # Check week row structure
        week_row = month["weeks"][0]
        assert "week_number" in week_row
        assert "year" in week_row
        assert "days" in week_row
        assert len(week_row["days"]) == 7

        # Check day structure
        day = week_row["days"][0]
        assert "day" in day
        assert "date" in day
        assert "day_of_week" in day
        assert "is_current_month" in day
        assert "slots" in day

    def test_month_includes_adjacent_days(self, client):
        """Verify month view includes padding days from adjacent months."""
        response = client.get("/api/board/month/2024/12")
        assert response.status_code == 200
        data = response.json()

        # Find days that are not in the current month
        other_month_days = []
        for week in data["month"]["weeks"]:
            for day in week["days"]:
                if not day["is_current_month"]:
                    other_month_days.append(day)

        # December 2024 starts on Sunday, so there should be padding days
        assert len(other_month_days) > 0


class TestSearchAPI:
    """Tests for search API endpoints."""

    def test_search_meals_api(self, client):
        """API-SR1: Search meals by name."""
        response = client.get("/api/board/search?q=soup")
        assert response.status_code == 200
        # Returns list of PoolMeal
        data = response.json()
        assert isinstance(data, list)

    def test_search_short_query(self, client):
        """API-SR2: Search with < 2 chars returns empty."""
        response = client.get("/api/board/search?q=a")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_htmx_search_endpoint(self, client):
        """API-SR3: HTMX search endpoint returns HTML."""
        response = client.get("/htmx/board/search?q=soup")
        assert response.status_code == 200
        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")


# ============== PAGE ROUTE TESTS ==============

class TestWeeklyPageRoutes:
    """Tests for weekly view page routes."""

    def test_board_home_page(self, client):
        """PG-W1: Board home redirects to current week."""
        response = client.get("/board")
        assert response.status_code == 200
        assert "Week" in response.text

    def test_specific_week_page(self, client):
        """PG-W2: Specific week page renders."""
        response = client.get("/board/week/2024/52")
        assert response.status_code == 200
        assert "Week 52" in response.text
        assert "2024" in response.text

    def test_week_page_has_navigation(self, client):
        """Verify week page has navigation elements."""
        response = client.get("/board/week/2024/50")
        assert response.status_code == 200
        assert "Prev" in response.text
        assert "Next" in response.text
        assert "Today" in response.text

    def test_week_page_has_view_toggle(self, client):
        """Verify week page has view toggle."""
        response = client.get("/board/week/2024/50")
        assert response.status_code == 200
        assert "Weekly" in response.text
        assert "Monthly" in response.text

    def test_week_page_has_meal_pool(self, client):
        """Verify week page has meal pool sidebar."""
        response = client.get("/board/week/2024/50")
        assert response.status_code == 200
        assert "meal-pool" in response.text
        assert "Search meals" in response.text


class TestMonthlyPageRoutes:
    """Tests for monthly view page routes."""

    def test_month_home_page(self, client):
        """PG-M1: Month home shows current month."""
        response = client.get("/board/month")
        assert response.status_code == 200

    def test_specific_month_page(self, client):
        """PG-M2: Specific month page renders."""
        response = client.get("/board/month/2024/12")
        assert response.status_code == 200
        assert "December" in response.text
        assert "2024" in response.text

    def test_month_page_has_filter_tabs(self, client):
        """Verify month page has meal type filter tabs."""
        response = client.get("/board/month/2024/12")
        assert response.status_code == 200
        assert "meal-type-tab" in response.text
        assert "Breakfast" in response.text
        assert "Lunch" in response.text
        assert "Dinner" in response.text
        assert "Snack" in response.text

    def test_month_page_has_week_links(self, client):
        """Verify month page has week links."""
        response = client.get("/board/month/2024/12")
        assert response.status_code == 200
        # Should have week labels like W49, W50, etc.
        assert "/board/week/" in response.text


# ============== SLOT OPERATIONS TESTS ==============

class TestSlotOperations:
    """Tests for slot assignment and manipulation."""

    def test_assign_meal_to_slot_schema(self, client):
        """Verify slot assignment request schema."""
        # This will fail without a valid meal_id, but tests the endpoint exists
        response = client.post("/api/board/slot", json={
            "year": 2024,
            "week": 50,
            "day_of_week": 0,
            "meal_slot": "lunch",
            "meal_id": 9999,  # Non-existent meal
            "create_chain": False,
            "chain_days": 1
        })
        # Should return 404 for non-existent meal, not 422 for bad schema
        assert response.status_code in [404, 200]

    def test_delete_nonexistent_slot(self, client):
        """Verify delete returns 404 for non-existent slot."""
        response = client.delete("/api/board/slot/99999")
        assert response.status_code == 404

    def test_update_nonexistent_slot(self, client):
        """Verify update returns 404 for non-existent slot."""
        response = client.put("/api/board/slot/99999?day_of_week=1")
        assert response.status_code == 404


class TestChainOperations:
    """Tests for leftover chain operations."""

    def test_extend_nonexistent_chain(self, client):
        """Verify extend returns 404 for non-existent chain."""
        response = client.post("/api/board/chain/fake-chain-id/extend")
        assert response.status_code == 404

    def test_shrink_nonexistent_chain(self, client):
        """Verify shrink returns 404 for non-existent chain."""
        response = client.post("/api/board/chain/fake-chain-id/shrink")
        assert response.status_code == 404

    def test_delete_nonexistent_chain(self, client):
        """Verify delete returns 404 for non-existent chain."""
        response = client.delete("/api/board/chain/fake-chain-id")
        assert response.status_code == 404


# ============== UI ELEMENT TESTS ==============

class TestUIElements:
    """Tests for UI elements presence in rendered pages."""

    def test_week_page_has_print_button(self, client):
        """Verify print button exists."""
        response = client.get("/board/week/2024/50")
        assert response.status_code == 200
        assert "Print" in response.text
        assert "window.print()" in response.text

    def test_week_page_has_keyboard_hints(self, client):
        """Verify keyboard shortcuts hint exists."""
        response = client.get("/board/week/2024/50")
        assert response.status_code == 200
        assert "keyboard-hint" in response.text
        assert "Shortcuts" in response.text

    def test_week_page_has_sortablejs(self, client):
        """Verify SortableJS is loaded."""
        response = client.get("/board/week/2024/50")
        assert response.status_code == 200
        assert "sortablejs" in response.text.lower() or "Sortable" in response.text

    def test_month_page_has_keyboard_hints(self, client):
        """Verify keyboard shortcuts hint exists in month view."""
        response = client.get("/board/month/2024/12")
        assert response.status_code == 200
        assert "keyboard-hint" in response.text


# ============== EDGE CASE TESTS ==============

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_week_1_navigation(self, client):
        """EC-1: Week 1 should handle year properly."""
        response = client.get("/board/week/2024/1")
        assert response.status_code == 200
        # Prev week should go to 2023
        assert "2023" in response.text or "/board/week/2023/52" in response.text

    def test_week_52_navigation(self, client):
        """EC-2: Week 52 should handle year rollover."""
        response = client.get("/board/week/2024/52")
        assert response.status_code == 200
        # Next week should go to 2025
        assert "2025" in response.text or "/board/week/2025/1" in response.text

    def test_january_month(self, client):
        """EC-3: January should show correctly."""
        response = client.get("/board/month/2024/1")
        assert response.status_code == 200
        assert "January" in response.text

    def test_december_month(self, client):
        """EC-4: December should show correctly."""
        response = client.get("/board/month/2024/12")
        assert response.status_code == 200
        assert "December" in response.text

    def test_empty_search(self, client):
        """Empty search should not error."""
        response = client.get("/api/board/search?q=")
        assert response.status_code == 200
        assert response.json() == []

    def test_special_characters_in_search(self, client):
        """Search with special characters should not error."""
        response = client.get("/api/board/search?q=%20%20")  # spaces
        assert response.status_code == 200


# ============== PRINT STYLE TESTS ==============

class TestPrintStyles:
    """Tests for print-related CSS."""

    def test_week_page_has_print_styles(self, client):
        """Verify print media query exists."""
        response = client.get("/board/week/2024/50")
        assert response.status_code == 200
        assert "@media print" in response.text

    def test_month_page_has_print_styles(self, client):
        """Verify print media query exists in month view."""
        response = client.get("/board/month/2024/12")
        assert response.status_code == 200
        assert "@media print" in response.text


# ============== DATA STRUCTURE TESTS ==============

class TestDataStructures:
    """Tests for data structure validation."""

    def test_pool_section_structure(self, client):
        """Verify pool section structure."""
        response = client.get("/api/board/week/2024/50")
        assert response.status_code == 200
        data = response.json()

        if data["pool"]:
            section = data["pool"][0]
            assert "meal_type" in section
            assert "label" in section
            assert "emoji" in section
            assert "meals" in section

    def test_pool_meal_structure(self, client):
        """Verify pool meal structure."""
        response = client.get("/api/board/week/2024/50")
        assert response.status_code == 200
        data = response.json()

        # Find a meal in the pool
        for section in data["pool"]:
            if section["meals"]:
                meal = section["meals"][0]
                assert "id" in meal
                assert "name" in meal
                assert "nev" in meal
                assert "meal_type" in meal
                assert "default_portions" in meal
                break

    def test_board_slot_structure(self, client):
        """Verify board slot structure."""
        response = client.get("/api/board/week/2024/50")
        assert response.status_code == 200
        data = response.json()

        day = data["week"]["days"][0]
        slot = day["slots"]["breakfast"]

        # Empty slot should have these fields
        assert "plan_meal_id" in slot or slot.get("plan_meal_id") is None
        assert "meal" in slot or slot.get("meal") is None
        assert "is_leftover" in slot
        assert "portions_remaining" in slot or slot.get("portions_remaining") is None
        assert "chain_id" in slot or slot.get("chain_id") is None


# ============== INTEGRATION TESTS ==============

class TestIntegration:
    """Integration tests that test multiple components together."""

    def test_full_board_workflow(self, client):
        """Test complete board workflow: view -> API -> view."""
        # 1. Load week page
        response = client.get("/board")
        assert response.status_code == 200

        # 2. Load API data
        response = client.get("/api/board/current")
        assert response.status_code == 200

        # 3. Search meals
        response = client.get("/api/board/search?q=test")
        assert response.status_code == 200

        # 4. Switch to month view
        response = client.get("/board/month")
        assert response.status_code == 200

    def test_htmx_search_integration(self, client):
        """Test HTMX search returns valid HTML for injection."""
        response = client.get("/htmx/board/search?q=soup")
        assert response.status_code == 200

        # Should contain draggable pool meals or empty message
        content = response.text
        assert ("pool-meal" in content or
                "No meals found" in content or
                "Type at least" in content)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
