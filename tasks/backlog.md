# Carmy Task Backlog

## Data Quality Issues

- [ ] **Meal type normalization** - Some meals are categorized as "vegan" or "meat" type instead of "main_course". These should be main_course with `is_vegan=True` or `has_meat=True` flags. Affects main course count in validation.
- [ ] **Missing Hungarian names** - Many meals have English name duplicated in `nev` field instead of actual Hungarian translation.
- [ ] **Missing cuisine data** - Some meals have no cuisine assigned.

## Enhancements

- [ ] **Add flavor base detection** - Automatically detect flavor bases from meal names (e.g., "Broccoli soup" -> broccoli flavor base).
- [ ] **Improve vegetarian/meat detection** - Parse meal names/types to better detect meat content.
- [ ] **Add meal editing CLI** - `carmy meal edit <id>` to update meal attributes.
- [ ] **Add plan creation CLI** - `carmy plan create --week N` to create new plans interactively.

## Future Ideas

- [ ] **Ingredient parsing** - Parse ingredients from XLSX "Ingredients" column if populated.
- [ ] **Recipe import** - Support importing recipes from URLs.
- [ ] **Image support** - Link meal images from data/images folder.

## Phase 7: Web UI (Planned)

See [docs/04_web_ui_spec.md](../docs/04_web_ui_spec.md) for full specification.

- [x] **7.1 API Foundation** - FastAPI setup, meals/plans CRUD endpoints, Pydantic schemas (2024-12-26)
- [x] **7.2 Basic Templates** - Jinja2 base layout, meals list/detail, plans list (2024-12-26)
- [x] **7.3 Plan Views** - Weekly plan view, generation page, validation display (2024-12-26)
- [x] **7.4 Analytics Dashboard** - Charts (frequency, cuisine, trends), stats (2024-12-26)
- [x] **7.5 Interactivity** - HTMX for inline editing, live search, notifications (2024-12-26)
- [x] **7.6 Polish** - Responsive design, dark mode, language toggle (2024-12-26)

---

## Completed

- [x] **Phase 1: Foundation** - Project structure, models, XLSX importer (2024-12-26)
- [x] **Phase 2: Rules Engine** - Validation rules, CLI commands (2024-12-26)
- [x] **Phase 3: Smart Generation** - Historical analyzer, plan generator, stats commands (2024-12-26)
- [x] **Phase 4: Seasonality** - Seasonal ingredients, meal scoring, season-aware generation (2024-12-26)
- [x] **Phase 5: Analytics** - Frequency reports, cuisine distribution, patterns, trends, leftovers (2024-12-26)
- [x] **Phase 6: Export & Integrations** - Shopping lists, JSON/CSV/Markdown/ICS export, calendar integration (2024-12-26)
- [x] **Phase 7: Web UI** - FastAPI + HTMX web interface with all features (2024-12-26)
