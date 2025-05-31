# -*- coding: utf-8 -*-
"""Database handling module for the Phone Store Manager."""

import sqlite3
import os

DATABASE_NAME = "store_data.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return conn

def _add_column_if_not_exists(cursor, table_name, column_name, column_type):
    """Helper function to add a column if it doesn't exist."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    # Corrected: Access column name using the correct key 'name' without extra spaces
    columns = [info['name'] for info in cursor.fetchall()]
    if column_name not in columns:
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            print(f"Added column '{column_name}' to table '{table_name}'.")
        except sqlite3.Error as e:
            print(f"Error adding column '{column_name}' to '{table_name}': {e}")

def init_db():
    """Initializes the database and creates/updates tables if they don't exist."""
    print(f"Initializing database at: {DB_PATH}")
    conn = None # Initialize conn to None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                original_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                quantity INTEGER NOT NULL
            )
        """)
        
        # Create sales table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL
            )
        """)
        
        # Create sale_items table with original_price_at_sale
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity_sold INTEGER NOT NULL,
                price_at_sale REAL NOT NULL,
                original_price_at_sale REAL NOT NULL, -- Added for profit calculation
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        
        # Add the column if the table already existed without it
        _add_column_if_not_exists(cursor, 'sale_items', 'original_price_at_sale', 'REAL NOT NULL DEFAULT 0.0') # Add with default for safety, though record_sale should handle it
        
        conn.commit()
        print("Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

def add_product(name, original_price, selling_price, quantity):
    """Adds a new product to the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, original_price, selling_price, quantity)
            VALUES (?, ?, ?, ?)
        """, (name, original_price, selling_price, quantity))
        conn.commit()
        print(f"Product '{name}' added successfully.")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Product name '{name}' already exists.")
        return False
    except sqlite3.Error as e:
        print(f"Error adding product: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_products():
    """Retrieves all products from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, original_price, selling_price, quantity FROM products ORDER BY name")
        products = cursor.fetchall()
        return [dict(row) for row in products] # Convert rows to dictionaries
    except sqlite3.Error as e:
        print(f"Error fetching products: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_product(product_id, name, original_price, selling_price, quantity):
    """Updates an existing product in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products 
            SET name = ?, original_price = ?, selling_price = ?, quantity = ?
            WHERE id = ?
        """, (name, original_price, selling_price, quantity, product_id))
        conn.commit()
        print(f"Product ID {product_id} updated successfully.")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Product name '{name}' might already exist for another ID.")
        return False
    except sqlite3.Error as e:
        print(f"Error updating product ID {product_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_product(product_id):
    """Deletes a product from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if product is part of any sale first? (Optional: prevent deletion if sold)
        # cursor.execute("SELECT 1 FROM sale_items WHERE product_id = ? LIMIT 1", (product_id,))
        # if cursor.fetchone():
        #     print(f"Error: Cannot delete product ID {product_id} as it exists in sales records.")
        #     return False
            
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        print(f"Product ID {product_id} deleted successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error deleting product ID {product_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def record_sale(items, total_price):
    # items should be a list of dicts: {'id': product_id, 'quantity': quantity_sold, 'selling_price': price_at_sale}
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Insert into sales table
        cursor.execute("INSERT INTO sales (total_amount) VALUES (?)", (total_price,))
        sale_id = cursor.lastrowid
        
        # Insert into sale_items and update product quantities
        for item in items:
            product_id = item['id']
            quantity_sold = item['quantity']
            price_at_sale = item['selling_price']
            
            # Fetch the current original_price for profit calculation
            cursor.execute("SELECT original_price FROM products WHERE id = ?", (product_id,))
            product_info = cursor.fetchone()
            if not product_info:
                raise sqlite3.Error(f"Product ID {product_id} not found during sale recording.")
            original_price_at_sale = product_info['original_price']

            cursor.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity_sold, price_at_sale, original_price_at_sale)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, product_id, quantity_sold, price_at_sale, original_price_at_sale))
            
            # Update product quantity
            cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity_sold, product_id))
            # Check if update was successful / quantity didn't go negative (optional)
            # cursor.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
            # current_qty = cursor.fetchone()[0]
            # if current_qty < 0:
            #     raise sqlite3.Error(f"Product ID {product_id} quantity would become negative.")

        # Commit transaction
        conn.commit()
        print(f"Sale recorded successfully with ID: {sale_id}")
        return sale_id
    except sqlite3.Error as e:
        conn.rollback() # Rollback on error
        print(f"Error recording sale: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_sale_details(sale_id):
    """Retrieves details for a specific sale, including items."""
    conn = get_db_connection()
    details = {"sale_info": None, "items": []}
    try:
        cursor = conn.cursor()
        # Get sale info
        cursor.execute("SELECT id, sale_date, total_amount FROM sales WHERE id = ?", (sale_id,))
        sale_info = cursor.fetchone()
        if sale_info:
            details["sale_info"] = dict(sale_info)
        
        # Get sale items including original price at sale
        cursor.execute("""
            SELECT si.quantity_sold, si.price_at_sale, si.original_price_at_sale, p.name 
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        items = cursor.fetchall()
        details["items"] = [dict(item) for item in items]
        
        return details
    except sqlite3.Error as e:
        print(f"Error fetching sale details for ID {sale_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_product_by_id(product_id):
    """Retrieves a single product by its ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, original_price, selling_price, quantity FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        return dict(product) if product else None # Convert row to dictionary or return None
    except sqlite3.Error as e:
        print(f"Error fetching product ID {product_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- Reporting Functions --- 

def get_sales_and_profit_for_period(start_date, end_date):
    """Calculates total sales and profit for a given date range."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Query to sum sales and calculate profit within the date range
        # Note: SQLite date functions are used here. Ensure dates are in 'YYYY-MM-DD HH:MM:SS' format.
        cursor.execute("""
            SELECT 
                SUM(si.price_at_sale * si.quantity_sold) as total_sales,
                SUM((si.price_at_sale - si.original_price_at_sale) * si.quantity_sold) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.sale_date BETWEEN ? AND ?
        """, (start_date, end_date))
        
        result = cursor.fetchone()
        # Corrected: Access results using correct keys without extra spaces
        total_sales = result['total_sales'] if result['total_sales'] is not None else 0.0
        total_profit = result['total_profit'] if result['total_profit'] is not None else 0.0
        
        return {'total_sales': total_sales, 'total_profit': total_profit}
    except sqlite3.Error as e:
        print(f"Error calculating sales/profit for period {start_date} to {end_date}: {e}")
        return {'total_sales': 0.0, 'total_profit': 0.0}
    finally:
        if conn:
            conn.close()


