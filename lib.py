import sqlite3
from sqlite3 import Error

# 建立資料庫連線
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        print(f'Successfully connected to the database')
        return conn
    except Error as e:
        print(f'Error connecting to the database: {e}')
    return conn

# 建立會員資料表
def create_users_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                phone TEXT
            )
        ''')
        print('Users table created successfully')
    except Error as e:
        print(f'Error creating users table: {e}')

# 建立訂單資料表
def create_orders_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                table_id INTEGER,
                timestamp TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (table_id) REFERENCES carts (table_id)
            )
        ''')
        print('Orders table created successfully')
    except Error as e:
        print(f'Error creating orders table: {e}')

# 建立購物車資料表
def create_carts_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY,
                table_id INTEGER,
                item_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY (item_id) REFERENCES menu_items (id),
                FOREIGN KEY (table_id) REFERENCES carts (table_id)
            )
        ''')
        print('Carts table created successfully')
    except Error as e:
        print(f'Error creating carts table: {e}')


# 建立餐點資料表
def create_menu_items_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY,
                categories TEXT,
                name TEXT,
                image TEXT,
                price REAL,
                description TEXT,
                FOREIGN KEY (categories) REFERENCES categories (name)
            )
        ''')
        print('Menu_items table created successfully')
    except Error as e:
        print(f'Error creating menu_items table: {e}')

# 建立餐點種類資料表
def create_menu_categories_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        # 插入餐點種類資料
        categories = ['主餐', '副餐', '飲料', '甜點']
        conn = create_connection()
        for category in categories:
            conn.execute('INSERT INTO categories (name) VALUES (?)', (category,))
            conn.commit()
        print('Categories table created successfully')
    except Error as e:
        print(f'Error creating categories table: {e}')

# 建立資料庫和資料表
def create_database():
    conn = create_connection()
    if conn is not None:
        create_users_table(conn)
        create_orders_table(conn)
        create_carts_table(conn)
        create_menu_items_table(conn)
        create_menu_categories_table(conn)
        conn.close()

    else:
        print('Error creating database')

# 呼叫建立資料庫函式
if __name__ == '__main__':
    create_database()