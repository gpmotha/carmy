# Carmy 🍳

**Every second counts.** A smart weekly meal planner for families.

Carmy learns from your historical meal plans to generate future weeks, enforces taste diversity rules, and supports Hungarian + international cuisines. Named after Carmen "Carmy" Berzatto from *The Bear*.

---

## What It Does

- **Learns from history**: Analyzes past weekly plans to understand preferences
- **Enforces rules**: No flavor conflicts (e.g., broccoli soup + broccoli pasta), meat limits, cuisine rotation
- **Generates plans**: Auto-suggests weekly menus (2 soups, 4 main courses)
- **Bilingual**: Hungarian (nev) + English (name) for all meals
- **Seasonal awareness**: Prefers seasonal ingredients

---

## Quick Start for Development

### Prerequisites
- Python 3.11+
- VS Code with Claude Code extension

### Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Initialize database
carmy db init

# Import historical data
carmy import history data/Meal_planner.xlsx
```

### Basic Commands
```bash
carmy meal list                    # List all meals
carmy meal list --type soup        # Filter by type
carmy plan show --week 10          # Show week's plan
carmy plan generate --week 15      # Auto-generate plan
carmy plan validate --week 15      # Check rules
carmy --lang hu meal list          # Hungarian output
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Feature Roadmap](docs/01_feature_roadmap.md) | Phased build plan (MVP → full features) |
| [Technical Spec](docs/02_technical_spec.md) | Architecture, tech stack, CLI commands |
| [Data Dictionary](docs/03_data_dictionary.md) | Data models, enums, import formats |
| [Project Description](docs/04_project_description.md) | Full project context and business rules |

---

## Project Structure

```
carmy/
├── src/
│   └── carmy/
│       ├── main.py              # CLI entry point
│       ├── models/              # SQLAlchemy models
│       ├── schemas/             # Pydantic schemas
│       ├── services/            # Business logic
│       │   ├── rules_engine.py  # Validation rules
│       │   ├── generator.py     # Plan generation
│       │   └── analyzer.py      # Historical analysis
│       ├── cli/                 # Typer CLI commands
│       └── i18n/                # EN/HU translations
├── data/
│   ├── Meal_planner.xlsx        # Historical data (683 entries)
│   └── images/meals/            # Meal photos
├── docs/                        # Documentation
├── tests/
├── pyproject.toml
└── README.md
```

---

## Historical Data Summary

Your `Meal_planner.xlsx` contains:

| Sheet | Contents | Count |
|-------|----------|-------|
| **Plan** | Weekly meal history (2023-2024) | 683 entries |
| **Sheet2** | Unique meal catalog | 84 meals |
| **Guide** | Weekly planning philosophy | Rules reference |

### Columns in Plan sheet:
`Week`, `Start`, `Név`, `Name`, `Type`, `Cuisine`, `Category`, `Calories`, `Prep time`, `Cook time`, `Difficulty`, `Seasonality`, `Ingredients`, `Note`

---

## Core Planning Rules

1. **Weekly quotas**: 2 soups, 4 main courses
2. **Taste diversity**: No same flavor base twice (broccoli, mushroom, etc.)
3. **Meat reduction**: Max 3 meat dishes per week
4. **Cuisine rotation**: Vary Hungarian, Italian, Indian, etc.
5. **Leftover tracking**: Reuse meals intentionally (marked in notes)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| CLI | Typer + Rich |
| Database | SQLite (local) |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| XLSX Import | openpyxl |

---

## Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Data models, CRUD, import | 🔲 TODO |
| 2 | Rules engine, validation | 🔲 TODO |
| 3 | Plan generation | 🔲 TODO |
| 4 | Seasonality | 🔲 TODO |
| 5 | Analytics | 🔲 TODO |
| 6 | Web UI (optional) | 🔲 TODO |

---

## For Claude Code

Start here:

1. **Read docs**: `docs/01_feature_roadmap.md` → `02_technical_spec.md` → `03_data_dictionary.md`
2. **Understand data**: Analyze `data/Meal_planner.xlsx` structure
3. **Build Phase 1**: Project setup, models, XLSX importer

### First Task
```
Set up the project structure per technical spec.
Create SQLAlchemy models for Meal, Recipe, WeeklyPlan, PlanMeal.
Build the XLSX importer for historical data.
```

---

## License

Private project.

---

*"Let's go, let's go, let's go!"* — Carmy
