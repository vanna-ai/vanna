#!/usr/bin/env python3
"""
Urban Eats Restaurant Chain Database Generator

Generates a realistic SQLite database for a restaurant chain with:
- 25 restaurant locations
- 50 menu items across 8 categories
- 2,000 loyalty customers
- 300 employees
- 50,000+ orders (6 months of data)
- 150,000+ order items
- Inventory and supplier data
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Seed for reproducibility
random.seed(42)

# Database path
DB_PATH = Path(__file__).parent / "urban_eats.sqlite"

# ============================================================================
# DATA CONSTANTS
# ============================================================================

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
    ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
    ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
    ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("Fort Worth", "TX"), ("Columbus", "OH"), ("Charlotte", "NC"),
    ("Seattle", "WA"), ("Denver", "CO"), ("Boston", "MA"),
    ("Portland", "OR"), ("Atlanta", "GA"), ("Miami", "FL"),
    ("Nashville", "TN"), ("Detroit", "MI"), ("Minneapolis", "MN"),
    ("Las Vegas", "NV")
]

LOCATION_TYPES = ["Downtown", "Airport", "Mall", "Suburbs", "University", "Waterfront"]

CATEGORIES = [
    ("Appetizers", "Start your meal with our delicious starters"),
    ("Salads", "Fresh and healthy salad options"),
    ("Burgers", "Our signature handcrafted burgers"),
    ("Main Course", "Hearty entrees for every appetite"),
    ("Pasta", "Italian-inspired pasta dishes"),
    ("Seafood", "Fresh catches from the sea"),
    ("Desserts", "Sweet endings to your meal"),
    ("Beverages", "Refreshing drinks and cocktails")
]

MENU_ITEMS = [
    # Appetizers (category_id=1)
    ("Loaded Nachos", 1, 12.99, 4.50, "Tortilla chips with cheese, jalapeños, and salsa", False),
    ("Crispy Calamari", 1, 14.99, 5.20, "Lightly breaded calamari with marinara sauce", False),
    ("Buffalo Wings", 1, 13.99, 4.80, "Classic buffalo wings with ranch dip", False),
    ("Spinach Artichoke Dip", 1, 11.99, 3.90, "Creamy dip served with pita chips", True),
    ("Bruschetta", 1, 10.99, 3.20, "Toasted bread with tomato and basil", True),
    ("Mozzarella Sticks", 1, 9.99, 3.00, "Golden fried mozzarella with marinara", True),

    # Salads (category_id=2)
    ("Caesar Salad", 2, 11.99, 3.50, "Romaine lettuce with caesar dressing and croutons", True),
    ("Greek Salad", 2, 12.99, 4.00, "Mixed greens with feta, olives, and cucumber", True),
    ("Cobb Salad", 2, 15.99, 5.50, "Chicken, bacon, egg, avocado on mixed greens", False),
    ("House Salad", 2, 8.99, 2.50, "Fresh mixed greens with house vinaigrette", True),
    ("Asian Chicken Salad", 2, 14.99, 5.00, "Grilled chicken with sesame ginger dressing", False),

    # Burgers (category_id=3)
    ("Classic Burger", 3, 14.99, 5.00, "Angus beef patty with lettuce, tomato, onion", False),
    ("Bacon Cheeseburger", 3, 16.99, 6.00, "Classic burger with bacon and cheddar", False),
    ("Mushroom Swiss Burger", 3, 17.99, 6.50, "Topped with sautéed mushrooms and swiss", False),
    ("Veggie Burger", 3, 14.99, 4.50, "House-made black bean patty", True),
    ("BBQ Burger", 3, 17.99, 6.20, "With BBQ sauce, onion rings, and cheddar", False),
    ("Spicy Jalapeño Burger", 3, 16.99, 5.80, "With jalapeños, pepper jack, and chipotle mayo", False),

    # Main Course (category_id=4)
    ("Grilled Chicken", 4, 18.99, 6.50, "Herb-marinated chicken breast with vegetables", False),
    ("Baby Back Ribs", 4, 24.99, 9.00, "Fall-off-the-bone ribs with BBQ sauce", False),
    ("Steak Frites", 4, 28.99, 11.00, "8oz sirloin with french fries", False),
    ("Chicken Fried Steak", 4, 19.99, 7.00, "Breaded steak with country gravy", False),
    ("Roasted Turkey Dinner", 4, 17.99, 6.00, "With mashed potatoes and cranberry sauce", False),
    ("Vegetable Stir Fry", 4, 15.99, 4.50, "Mixed vegetables in savory sauce with rice", True),

    # Pasta (category_id=5)
    ("Spaghetti Bolognese", 5, 16.99, 5.00, "Classic meat sauce over spaghetti", False),
    ("Fettuccine Alfredo", 5, 15.99, 4.50, "Creamy parmesan sauce", True),
    ("Chicken Parmesan", 5, 19.99, 7.00, "Breaded chicken with marinara over pasta", False),
    ("Shrimp Scampi", 5, 21.99, 8.50, "Garlic butter shrimp over linguine", False),
    ("Vegetable Primavera", 5, 14.99, 4.00, "Seasonal vegetables in garlic olive oil", True),
    ("Lasagna", 5, 17.99, 6.00, "Layers of pasta, meat sauce, and cheese", False),

    # Seafood (category_id=6)
    ("Grilled Salmon", 6, 24.99, 10.00, "Atlantic salmon with lemon butter sauce", False),
    ("Fish and Chips", 6, 17.99, 6.00, "Beer-battered cod with fries and coleslaw", False),
    ("Shrimp Basket", 6, 16.99, 6.50, "Fried shrimp with cocktail sauce", False),
    ("Crab Cakes", 6, 22.99, 9.00, "Two jumbo lump crab cakes", False),
    ("Lobster Tail", 6, 34.99, 15.00, "Broiled Maine lobster tail with butter", False),
    ("Mahi Mahi Tacos", 6, 18.99, 7.00, "Grilled mahi with mango salsa", False),

    # Desserts (category_id=7)
    ("Chocolate Lava Cake", 7, 8.99, 2.50, "Warm chocolate cake with molten center", True),
    ("New York Cheesecake", 7, 7.99, 2.20, "Classic creamy cheesecake", True),
    ("Apple Pie à la Mode", 7, 7.99, 2.00, "Warm apple pie with vanilla ice cream", True),
    ("Tiramisu", 7, 8.99, 2.80, "Italian coffee-flavored dessert", True),
    ("Ice Cream Sundae", 7, 6.99, 1.80, "Three scoops with toppings", True),
    ("Brownie Sundae", 7, 8.99, 2.50, "Warm brownie with ice cream and fudge", True),

    # Beverages (category_id=8)
    ("Soft Drink", 8, 2.99, 0.50, "Coca-Cola, Sprite, or Fanta", True),
    ("Fresh Lemonade", 8, 3.99, 0.80, "House-made lemonade", True),
    ("Iced Tea", 8, 2.99, 0.40, "Unsweetened or sweet tea", True),
    ("Coffee", 8, 2.99, 0.60, "Regular or decaf", True),
    ("Craft Beer", 8, 6.99, 2.50, "Selection of local craft beers", True),
    ("House Wine", 8, 7.99, 3.00, "Red or white by the glass", True),
    ("Margarita", 8, 9.99, 3.50, "Classic lime margarita", True),
    ("Milkshake", 8, 5.99, 1.50, "Chocolate, vanilla, or strawberry", True),
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker"
]

SUPPLIERS = [
    ("Fresh Farms Co.", "John Smith", "Produce"),
    ("Premium Meats Inc.", "Sarah Johnson", "Meat"),
    ("Ocean Harvest", "Mike Chen", "Seafood"),
    ("Dairy Direct", "Lisa Brown", "Dairy"),
    ("Bread & Beyond", "Tom Wilson", "Bakery"),
    ("Global Spices", "Maria Garcia", "Spices"),
    ("Beverage Distributors", "James Davis", "Beverages"),
    ("Quality Oils", "Anna Martinez", "Cooking Oils"),
    ("Paper & Packaging Plus", "Robert Lee", "Supplies"),
    ("Cleaning Solutions Corp", "Jennifer Taylor", "Cleaning"),
    ("Kitchen Equipment Pro", "David Anderson", "Equipment"),
    ("Sysco Foods", "Michelle Thomas", "General"),
    ("US Foods", "Chris Jackson", "General"),
    ("Gordon Food Service", "Amanda White", "General"),
    ("Performance Food Group", "Brian Harris", "General"),
    ("Restaurant Depot", "Karen Martin", "General"),
    ("Coca-Cola Bottling", "Steve Clark", "Beverages"),
    ("Anheuser-Busch", "Nicole Lewis", "Beverages"),
    ("Tyson Foods", "Kevin Robinson", "Meat"),
    ("Dole Food Company", "Rachel Walker", "Produce"),
]

INVENTORY_ITEMS = [
    ("Ground Beef", 1, "kg", 8.50, 50),
    ("Chicken Breast", 1, "kg", 7.00, 40),
    ("Bacon", 1, "kg", 12.00, 30),
    ("Atlantic Salmon", 2, "kg", 22.00, 25),
    ("Shrimp", 2, "kg", 18.00, 20),
    ("Cod Fillets", 2, "kg", 15.00, 20),
    ("Romaine Lettuce", 0, "kg", 3.50, 30),
    ("Tomatoes", 0, "kg", 4.00, 40),
    ("Onions", 0, "kg", 2.00, 50),
    ("Potatoes", 0, "kg", 1.50, 100),
    ("Cheddar Cheese", 3, "kg", 10.00, 30),
    ("Mozzarella", 3, "kg", 11.00, 25),
    ("Parmesan", 3, "kg", 18.00, 15),
    ("Burger Buns", 4, "units", 0.30, 200),
    ("Bread Loaves", 4, "units", 2.50, 50),
    ("Olive Oil", 7, "liters", 12.00, 20),
    ("Vegetable Oil", 7, "liters", 5.00, 40),
    ("Pasta (Spaghetti)", 11, "kg", 2.00, 50),
    ("Pasta (Fettuccine)", 11, "kg", 2.20, 40),
    ("Rice", 11, "kg", 1.80, 60),
    ("Flour", 11, "kg", 1.00, 80),
    ("Sugar", 11, "kg", 1.20, 50),
    ("Salt", 5, "kg", 0.80, 30),
    ("Black Pepper", 5, "kg", 15.00, 5),
    ("Garlic", 5, "kg", 8.00, 10),
    ("Coca-Cola Syrup", 6, "liters", 4.00, 100),
    ("Coffee Beans", 6, "kg", 20.00, 20),
    ("Tea Bags", 6, "units", 0.05, 1000),
    ("Vanilla Ice Cream", 3, "liters", 8.00, 30),
    ("Chocolate Cake Mix", 11, "kg", 5.00, 20),
    ("Napkins", 8, "units", 0.02, 5000),
    ("To-Go Containers", 8, "units", 0.15, 2000),
    ("Cleaning Solution", 9, "liters", 8.00, 20),
    ("Hand Soap", 9, "liters", 6.00, 15),
]

PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "Mobile Pay", "Gift Card"]
ORDER_TYPES = ["Dine-in", "Takeout", "Delivery"]
EMPLOYEE_ROLES = ["Manager", "Assistant Manager", "Server", "Bartender", "Chef", "Line Cook", "Host", "Busser"]

# ============================================================================
# DATABASE CREATION
# ============================================================================

def create_database():
    """Create the SQLite database with all tables."""

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
        -- Restaurant locations
        CREATE TABLE restaurants (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT,
            country TEXT DEFAULT 'USA',
            address TEXT,
            phone TEXT,
            manager_id INTEGER,
            opened_date DATE,
            seating_capacity INTEGER
        );

        -- Menu categories
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        );

        -- Menu items
        CREATE TABLE menu_items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER,
            price DECIMAL(10,2) NOT NULL,
            cost DECIMAL(10,2),
            description TEXT,
            is_vegetarian BOOLEAN DEFAULT FALSE,
            is_available BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        -- Customers (loyalty program)
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            loyalty_points INTEGER DEFAULT 0,
            joined_date DATE,
            preferred_restaurant_id INTEGER,
            FOREIGN KEY (preferred_restaurant_id) REFERENCES restaurants(id)
        );

        -- Employees
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT,
            restaurant_id INTEGER,
            hire_date DATE,
            hourly_rate DECIMAL(10,2),
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        );

        -- Orders (sales transactions)
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            restaurant_id INTEGER NOT NULL,
            customer_id INTEGER,
            employee_id INTEGER,
            order_date DATETIME NOT NULL,
            subtotal DECIMAL(10,2),
            tax DECIMAL(10,2),
            tip DECIMAL(10,2),
            total DECIMAL(10,2),
            payment_method TEXT,
            order_type TEXT,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );

        -- Order line items
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price DECIMAL(10,2),
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        );

        -- Suppliers
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            contact_name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            category TEXT
        );

        -- Inventory items
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            supplier_id INTEGER,
            unit TEXT,
            unit_cost DECIMAL(10,2),
            reorder_level INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        -- Inventory by restaurant
        CREATE TABLE restaurant_inventory (
            id INTEGER PRIMARY KEY,
            restaurant_id INTEGER,
            inventory_id INTEGER,
            quantity DECIMAL(10,2),
            last_restocked DATE,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
            FOREIGN KEY (inventory_id) REFERENCES inventory(id)
        );

        -- Create indexes for performance
        CREATE INDEX idx_orders_restaurant ON orders(restaurant_id);
        CREATE INDEX idx_orders_date ON orders(order_date);
        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_order_items_order ON order_items(order_id);
        CREATE INDEX idx_order_items_menu ON order_items(menu_item_id);
        CREATE INDEX idx_employees_restaurant ON employees(restaurant_id);
    """)

    conn.commit()
    return conn

def generate_phone():
    """Generate a random US phone number."""
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

def generate_email(first_name, last_name, domain="email.com"):
    """Generate an email address."""
    return f"{first_name.lower()}.{last_name.lower()}@{domain}"

def populate_restaurants(cursor):
    """Create 25 restaurant locations."""
    print("Creating restaurants...")

    restaurants = []
    for i, (city, state) in enumerate(CITIES):
        location_type = random.choice(LOCATION_TYPES)
        name = f"Urban Eats {location_type}"
        address = f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Elm', 'Market', 'Commerce'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}"
        opened_date = datetime(2018, 1, 1) + timedelta(days=random.randint(0, 1800))
        seating_capacity = random.randint(50, 200)

        restaurants.append((
            i + 1, name, city, state, "USA", address,
            generate_phone(), None, opened_date.strftime("%Y-%m-%d"), seating_capacity
        ))

    cursor.executemany(
        "INSERT INTO restaurants VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        restaurants
    )
    return len(restaurants)

def populate_categories(cursor):
    """Create menu categories."""
    print("Creating categories...")

    categories = [(i + 1, name, desc) for i, (name, desc) in enumerate(CATEGORIES)]
    cursor.executemany("INSERT INTO categories VALUES (?, ?, ?)", categories)
    return len(categories)

def populate_menu_items(cursor):
    """Create menu items."""
    print("Creating menu items...")

    menu_items = []
    for i, (name, cat_id, price, cost, desc, is_veg) in enumerate(MENU_ITEMS):
        menu_items.append((i + 1, name, cat_id, price, cost, desc, is_veg, True))

    cursor.executemany(
        "INSERT INTO menu_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        menu_items
    )
    return len(menu_items)

def populate_suppliers(cursor):
    """Create suppliers."""
    print("Creating suppliers...")

    suppliers = []
    for i, (name, contact, category) in enumerate(SUPPLIERS):
        email = generate_email(contact.split()[0], contact.split()[1], "supplier.com")
        address = f"{random.randint(100, 9999)} Industrial Way, Warehouse District"
        suppliers.append((i + 1, name, contact, email, generate_phone(), address, category))

    cursor.executemany(
        "INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?, ?)",
        suppliers
    )
    return len(suppliers)

def populate_inventory(cursor):
    """Create inventory items."""
    print("Creating inventory items...")

    inventory = []
    for i, (name, supplier_id, unit, cost, reorder) in enumerate(INVENTORY_ITEMS):
        # Map supplier_id (0-based category index) to actual supplier
        actual_supplier = (supplier_id % 20) + 1 if supplier_id > 0 else random.randint(1, 20)
        inventory.append((i + 1, name, actual_supplier, unit, cost, reorder))

    cursor.executemany(
        "INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?)",
        inventory
    )
    return len(inventory)

def populate_employees(cursor, num_restaurants):
    """Create employees for all restaurants."""
    print("Creating employees...")

    employees = []
    employee_id = 1

    for restaurant_id in range(1, num_restaurants + 1):
        # Each restaurant has 10-15 employees
        num_employees = random.randint(10, 15)

        # First employee is always the manager
        for j in range(num_employees):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            if j == 0:
                role = "Manager"
                hourly_rate = random.uniform(25, 35)
            elif j == 1:
                role = "Assistant Manager"
                hourly_rate = random.uniform(18, 25)
            else:
                role = random.choice(EMPLOYEE_ROLES[2:])  # Non-manager roles
                if role == "Chef":
                    hourly_rate = random.uniform(18, 28)
                elif role in ["Server", "Bartender"]:
                    hourly_rate = random.uniform(12, 18)
                else:
                    hourly_rate = random.uniform(10, 15)

            hire_date = datetime(2018, 1, 1) + timedelta(days=random.randint(0, 2000))
            email = generate_email(first_name, last_name, "urbaneats.com")

            employees.append((
                employee_id, first_name, last_name, email, generate_phone(),
                role, restaurant_id, hire_date.strftime("%Y-%m-%d"), round(hourly_rate, 2)
            ))
            employee_id += 1

    cursor.executemany(
        "INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        employees
    )

    # Update restaurant managers
    for restaurant_id in range(1, num_restaurants + 1):
        cursor.execute(
            "UPDATE restaurants SET manager_id = (SELECT id FROM employees WHERE restaurant_id = ? AND role = 'Manager' LIMIT 1) WHERE id = ?",
            (restaurant_id, restaurant_id)
        )

    return len(employees)

def populate_customers(cursor, num_restaurants):
    """Create loyalty program customers."""
    print("Creating customers...")

    customers = []
    used_emails = set()

    for i in range(2000):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        # Ensure unique email
        base_email = generate_email(first_name, last_name)
        email = base_email
        counter = 1
        while email in used_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@email.com"
            counter += 1
        used_emails.add(email)

        joined_date = datetime(2019, 1, 1) + timedelta(days=random.randint(0, 1800))
        loyalty_points = random.randint(0, 5000)
        preferred_restaurant = random.randint(1, num_restaurants) if random.random() > 0.3 else None

        customers.append((
            i + 1, first_name, last_name, email, generate_phone(),
            loyalty_points, joined_date.strftime("%Y-%m-%d"), preferred_restaurant
        ))

    cursor.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        customers
    )
    return len(customers)

def populate_restaurant_inventory(cursor, num_restaurants, num_inventory):
    """Create inventory records for each restaurant."""
    print("Creating restaurant inventory...")

    records = []
    record_id = 1

    for restaurant_id in range(1, num_restaurants + 1):
        for inventory_id in range(1, num_inventory + 1):
            # Random quantity between 50% and 150% of reorder level
            cursor.execute("SELECT reorder_level FROM inventory WHERE id = ?", (inventory_id,))
            reorder_level = cursor.fetchone()[0]
            quantity = round(random.uniform(0.5, 2.0) * reorder_level, 1)

            last_restocked = datetime.now() - timedelta(days=random.randint(1, 30))

            records.append((
                record_id, restaurant_id, inventory_id, quantity,
                last_restocked.strftime("%Y-%m-%d")
            ))
            record_id += 1

    cursor.executemany(
        "INSERT INTO restaurant_inventory VALUES (?, ?, ?, ?, ?)",
        records
    )
    return len(records)

def populate_orders(cursor, num_restaurants, num_customers, num_menu_items):
    """Generate 6 months of order data with realistic patterns."""
    print("Creating orders and order items (this may take a moment)...")

    # Get employee IDs by restaurant for servers
    restaurant_servers = {}
    for restaurant_id in range(1, num_restaurants + 1):
        cursor.execute(
            "SELECT id FROM employees WHERE restaurant_id = ? AND role IN ('Server', 'Bartender')",
            (restaurant_id,)
        )
        restaurant_servers[restaurant_id] = [row[0] for row in cursor.fetchall()]

    # Generate orders for the last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    orders = []
    order_items = []
    order_id = 1
    order_item_id = 1

    current_date = start_date
    while current_date <= end_date:
        # More orders on weekends
        is_weekend = current_date.weekday() >= 5
        base_orders = random.randint(60, 100) if is_weekend else random.randint(40, 80)

        for restaurant_id in range(1, num_restaurants + 1):
            # Vary by restaurant size (based on seating capacity effect)
            num_orders_today = int(base_orders * random.uniform(0.7, 1.3))

            for _ in range(num_orders_today):
                # Order time - peaks at lunch (11-14) and dinner (17-21)
                hour_weights = [0.5, 0.3, 0.2, 0.1, 0.1, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0,
                               2.5, 3.0, 2.5, 1.5, 1.0, 1.5, 3.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0]
                hour = random.choices(range(24), weights=hour_weights)[0]
                minute = random.randint(0, 59)
                order_datetime = current_date.replace(hour=hour, minute=minute)

                # Customer (30% loyalty members)
                customer_id = random.randint(1, num_customers) if random.random() < 0.3 else None

                # Server
                employee_id = random.choice(restaurant_servers.get(restaurant_id, [1]))

                # Order type
                order_type = random.choices(
                    ORDER_TYPES,
                    weights=[0.6, 0.25, 0.15]  # More dine-in
                )[0]

                # Payment method
                payment_method = random.choices(
                    PAYMENT_METHODS,
                    weights=[0.1, 0.5, 0.2, 0.15, 0.05]  # Credit card most common
                )[0]

                # Generate order items (1-5 items per order)
                num_items = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.35, 0.30, 0.15, 0.05])[0]

                subtotal = 0
                items_for_this_order = []

                for _ in range(num_items):
                    menu_item_id = random.randint(1, num_menu_items)
                    cursor.execute("SELECT price FROM menu_items WHERE id = ?", (menu_item_id,))
                    price = cursor.fetchone()[0]

                    quantity = random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
                    item_total = price * quantity
                    subtotal += item_total

                    notes = None
                    if random.random() < 0.1:
                        notes = random.choice([
                            "No onions", "Extra sauce", "Well done", "Gluten-free bun",
                            "Dressing on side", "No ice", "Extra napkins", "Split plate"
                        ])

                    items_for_this_order.append((
                        order_item_id, order_id, menu_item_id, quantity, price, notes
                    ))
                    order_item_id += 1

                # Calculate totals
                tax = round(subtotal * 0.08, 2)  # 8% tax
                tip = round(subtotal * random.uniform(0.15, 0.25), 2) if order_type == "Dine-in" else 0
                total = round(subtotal + tax + tip, 2)

                orders.append((
                    order_id, restaurant_id, customer_id, employee_id,
                    order_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    round(subtotal, 2), tax, tip, total, payment_method, order_type
                ))
                order_items.extend(items_for_this_order)
                order_id += 1

        current_date += timedelta(days=1)

        # Batch insert every 10 days for performance
        if len(orders) >= 10000:
            cursor.executemany(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                orders
            )
            cursor.executemany(
                "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)",
                order_items
            )
            orders = []
            order_items = []

    # Insert remaining orders
    if orders:
        cursor.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            orders
        )
        cursor.executemany(
            "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)",
            order_items
        )

    return order_id - 1, order_item_id - 1

def main():
    """Main function to generate the complete database."""
    print("=" * 60)
    print("Urban Eats Restaurant Chain Database Generator")
    print("=" * 60)
    print()

    # Create database and tables
    conn = create_database()
    cursor = conn.cursor()

    # Populate tables
    num_restaurants = populate_restaurants(cursor)
    num_categories = populate_categories(cursor)
    num_menu_items = populate_menu_items(cursor)
    num_suppliers = populate_suppliers(cursor)
    num_inventory = populate_inventory(cursor)
    num_employees = populate_employees(cursor, num_restaurants)
    num_customers = populate_customers(cursor, num_restaurants)
    num_inventory_records = populate_restaurant_inventory(cursor, num_restaurants, num_inventory)
    num_orders, num_order_items = populate_orders(cursor, num_restaurants, num_customers, num_menu_items)

    # Commit and close
    conn.commit()

    # Print summary
    print()
    print("=" * 60)
    print("Database Generation Complete!")
    print("=" * 60)
    print(f"Database saved to: {DB_PATH}")
    print()
    print("Table Statistics:")
    print(f"  - Restaurants:          {num_restaurants:,}")
    print(f"  - Categories:           {num_categories:,}")
    print(f"  - Menu Items:           {num_menu_items:,}")
    print(f"  - Customers:            {num_customers:,}")
    print(f"  - Employees:            {num_employees:,}")
    print(f"  - Suppliers:            {num_suppliers:,}")
    print(f"  - Inventory Items:      {num_inventory:,}")
    print(f"  - Restaurant Inventory: {num_inventory_records:,}")
    print(f"  - Orders:               {num_orders:,}")
    print(f"  - Order Items:          {num_order_items:,}")
    print()

    # Verify with some sample queries
    print("Sample Query Results:")
    print("-" * 40)

    cursor.execute("SELECT SUM(total) FROM orders")
    total_revenue = cursor.fetchone()[0]
    print(f"Total Revenue (6 months): ${total_revenue:,.2f}")

    cursor.execute("""
        SELECT r.city, COUNT(o.id) as order_count, SUM(o.total) as revenue
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        GROUP BY r.city
        ORDER BY revenue DESC
        LIMIT 5
    """)
    print("\nTop 5 Cities by Revenue:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: ${row[2]:,.2f} ({row[1]:,} orders)")

    cursor.execute("""
        SELECT m.name, COUNT(oi.id) as times_ordered
        FROM order_items oi
        JOIN menu_items m ON oi.menu_item_id = m.id
        GROUP BY m.id
        ORDER BY times_ordered DESC
        LIMIT 5
    """)
    print("\nTop 5 Menu Items:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,} orders")

    conn.close()
    print()
    print("Database is ready for use!")

if __name__ == "__main__":
    main()
