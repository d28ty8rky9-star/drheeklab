"""Saved production specifications and one-time completion recognition."""
STATEMENTS = (
    "CREATE TABLE production_recipes (variant_id INTEGER PRIMARY KEY REFERENCES variants(id), revision INTEGER NOT NULL, data TEXT NOT NULL, updated_at TEXT NOT NULL)",
    "CREATE TABLE recipe_orders (op_id INTEGER PRIMARY KEY REFERENCES production_orders(id), recipe TEXT NOT NULL)",
    "CREATE TABLE production_completions (op_id INTEGER PRIMARY KEY REFERENCES production_orders(id), completed_at TEXT NOT NULL, cost_cents INTEGER NOT NULL CHECK(cost_cents>=0))",
)
