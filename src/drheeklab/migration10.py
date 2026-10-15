"""Accessories share unit stock and existing sale/return/cost accounting."""
STATEMENTS=("CREATE TABLE accessory_products(product_id INTEGER PRIMARY KEY REFERENCES products(id))",)
