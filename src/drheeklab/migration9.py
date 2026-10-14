"""Independent purchased stock catalog; no production specification required."""
STATEMENTS = (
    "CREATE TABLE purchased_products (product_id INTEGER PRIMARY KEY REFERENCES products(id))",
)
