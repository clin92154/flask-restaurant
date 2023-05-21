from flask import *
import sqlite3
from lib import *
import datetime ,os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__) #目前使用模組
conn = sqlite3.connect('database.db')



"""
環境設定
"""
app.templates_auto_reload = True 
app.config['UPLOAD_FOLDER'] = '/static/images' #路徑建置


"""
Format設定
"""
@app.template_filter('custom_datetimeformat')
def custom_datetimeformat(value):
    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
    formatted_datetime = dt.strftime('%Y-%m-%d %H時%M分%S秒')
    return formatted_datetime

"""
首頁
"""
@app.route('/', methods=['GET', 'POST'])
@app.route('/<category>/', methods=['GET', 'POST'])
def home(category='all'):
    conn = create_connection()


    if conn is not None:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories')
        categories = cursor.fetchall()
        
        selected_category = category  #餐點選項
        if selected_category == 'all': #所有餐點選項
            cursor.execute('SELECT * FROM menu_items')
        else: #指定選項
            cursor.execute('SELECT * FROM menu_items WHERE categories = ?', (selected_category,))
        menu_items = cursor.fetchall()
     
        cart_items= show_cart()


        ''' 檢查 Cookie '''
        response = make_response(render_template('index.html', categories=categories, menu_items=menu_items,selected_category=selected_category,cart_items=cart_items))
        if 'islogin' not in request.cookies:
            response.set_cookie('islogin',value='false')
       
        conn.close()

        return response
    else:
        return 'Error connecting to the database'
    

"""
歷史訂單
"""
@app.route('/Order_history', methods=['GET'])
def order_history():
    conn = create_connection()
    cursor = conn.cursor()
    phone = request.cookies.get('user_phone')
    user_id = cursor.execute('SELECT users.id FROM users WHERE users.phone = ?', (phone,)).fetchone()
    print(phone,user_id[0])

    try:
        # 歷史訂單
        cursor.execute('SELECT orders.id, SUM(carts.quantity * menu_items.price), orders.timestamp , carts.quantity , menu_items.name , menu_items.price  FROM orders INNER JOIN carts ON orders.table_id = carts.table_id INNER JOIN menu_items ON carts.item_id = menu_items.id WHERE orders.user_id = ? GROUP BY orders.id', (user_id[0],))
        orders = cursor.fetchall()
        conn.close()
        return render_template('/restaurant/order_history.html', orders=orders)
    except Error as e:
        print(f'Error retrieving order history: {e}')
        conn.close()

    return 'Error retrieving order history'




"""
加入購物車
"""
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = request.form['item_id']
    quantity = int(request.form['quantity'])

    conn = create_connection()
    cursor = conn.cursor()

    try:
        # 查找 orders 表中 table_id 的最大值
        cursor.execute('SELECT MAX(table_id) FROM orders')
        max_table_id = cursor.fetchone()[0]

        if max_table_id is not None:
            table_id = max_table_id + 1
        else:
            table_id = 1

        # 檢查購物車中是否已經存在該餐點，若存在則更新數量，否則新增一筆資料
        cursor.execute('SELECT * FROM carts WHERE item_id = ? AND table_id = ? LIMIT 1', (item_id, table_id))
        existing_item = cursor.fetchone()

        if existing_item:
            new_quantity = existing_item[3] + quantity
            cursor.execute('UPDATE carts SET quantity = ? WHERE item_id = ? AND table_id = ?', (new_quantity, item_id,table_id))
        else:
            cursor.execute('INSERT INTO carts (table_id, item_id, quantity) VALUES (?, ?, ?)', (table_id, item_id, quantity))
        
        conn.commit()
    except Error as e:
        conn.rollback()
        flash(f'Error adding item to cart: {e}')
    finally:
        conn.close()

    return redirect(url_for('home'))

"""
購物車
"""
# 顯示購物車
def show_cart():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT MAX(table_id) FROM orders')
    max_table_id = cursor.fetchone()[0]

    if max_table_id is not None:
        table_id = max_table_id + 1
    else:
        table_id = 1
    cursor.execute('''
        SELECT menu_items.name, carts.quantity, menu_items.price,carts.id
        FROM carts
        INNER JOIN menu_items ON carts.item_id = menu_items.id
        WHERE carts.table_id = ?
    ''', (table_id,))

    cart_items = cursor.fetchall()

    conn.close()
    return cart_items


"""
購物車轉訂單
"""
@app.route('/cart_to_order/<phone>')
def cart_to_order(phone):
    user_id = create_order_cart(phone)
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(id) FROM orders WHERE user_id=?',(user_id,))
    order_id = cursor.fetchone()[0]
    return redirect(url_for('created_order',order_id=order_id))


"""
刪除餐點
"""
@app.route('/delete_cart_item/<cart_id>', methods=['POST'])
def delete_cart_item(cart_id,page='home'):
    
    # 刪除餐點
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM carts WHERE id = ?",(cart_id,))

    # 提交變更到資料庫
    conn.commit()
    conn.close()
    if request.form["page"] =='for_order':
        return redirect(url_for('cart_detail'))
    elif request.form["page"] =='home':
        return redirect(url_for('home'))
    return redirect(url_for('edit_order' , order_id = request.form['page']))


"""
更新餐點數量
"""

@app.route('/update_cart_item/<cart_id>', methods=['POST'])
def update_cart_item(cart_id):
    conn = create_connection()
    cursor = conn.cursor()
    quantity = int(request.form['quantity'])

    cursor.execute("UPDATE carts SET quantity = ? WHERE id = ?",(quantity,cart_id))

    conn.commit()

    conn.close() 
    if request.form['page'] == "for_order":
        return redirect(url_for('cart_detail'))
    return redirect(url_for('edit_order' , order_id = request.form['page']))





"""
購物車頁面並成立訂單
"""
@app.route('/cart', methods=['GET'])
def cart_detail():
    
    cart_items = show_cart()

    #顯示總額
    total_amount = 0
    for item in cart_items:
        quantity = item[1]
        price = item[2]
        total_amount += quantity * price
    return render_template('cart/cart.html', carts=cart_items , total=total_amount)


"""
登入後成立訂單資料
"""
# 創建訂單
def create_order_cart(phone):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # 根據手機號碼找到對應的會員編號
            cursor.execute('SELECT id FROM users WHERE phone=?', (phone,))
            user_id = cursor.fetchone()[0]
            
            # 根據table_id 獲取購物車資料
            carts = get_cart_items()

            # 創建訂單並刪除購物車資料
            for cart in carts:
                print("顯示訂單資料")

            timestamp = datetime.datetime.now()
            # 創建訂單
            cursor.execute('INSERT INTO orders (table_id,user_id, timestamp) VALUES (?, ?, ?)', (cart[4],user_id, timestamp))
                # 執行其他相應的操作，如更新庫存等
                
            conn.commit()

            # 關閉資料庫連接
            conn.close()
            print('Order created and cart data cleared successfully')
        except Error as e:
            print(f'Error creating order and clearing cart data: {e}')
        conn.close()
        return user_id
    else:
        print('Error connecting to the database')


# 獲取購物車資料
def get_cart_items():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(table_id) FROM orders')
            max_table_id = cursor.fetchone()[0]

            if max_table_id is not None:
                table_id = max_table_id + 1
            else:
                table_id = 1
            cursor.execute('''
                SELECT carts.id, menu_items.name, menu_items.price, carts.quantity , carts.table_id 
                FROM carts
                INNER JOIN menu_items ON carts.item_id = menu_items.id
                WHERE carts.table_id = ?
            ''', (table_id,))
            cart_items = cursor.fetchall()
            conn.close()
            return cart_items
        except Error as e:
            print(f'Error retrieving cart items: {e}')
    return []


"""
訂單成立資料顯示
- 顯示:訂單編號、會員名稱、手機號碼、餐點名稱、數量訂單成立時間、總額
"""
@app.route('/order/<order_id>', methods=['GET', 'POST'])
def created_order(order_id):
    conn = create_connection()
    cursor = conn.cursor()

    # 訂單資料
    cursor.execute('SELECT id, user_id, table_id, timestamp FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone()

    # 會員資料
    cursor.execute('SELECT username, phone FROM users WHERE id = ?', (order[1],))
    user = cursor.fetchone()

    # 餐點資訊
    cursor.execute('''
        SELECT menu_items.name, menu_items.price ,carts.quantity
        FROM carts
        INNER JOIN menu_items ON carts.item_id = menu_items.id
        WHERE carts.table_id = ?
    ''', (order[2],))
    cart_items = cursor.fetchall()

    # 總額
    total_price = 0
    for item in cart_items:
        item_price = item[1]
        total_price += item_price * item[2]

    conn.close()

    # 渲染模板并传递数据
    return render_template('order.html', order_number=order_id, username=user[0], phone=user[1], items=cart_items, total_price=total_price)



"""
後臺管理
"""

"""
新增餐點
"""
@app.route('/admin/add_menu_item', methods=['GET', 'POST'])
def add_menu_item():
    conn =  create_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            print(filename)
            file_path = f".{app.config['UPLOAD_FOLDER']}/{filename}"
            file.save(file_path)
        category = request.form['category']
        name = request.form['name']
        image = file_path
        price = request.form['price']
        description = request.form['description']
        cursor.execute('INSERT INTO menu_items (categories, name, image, price, description) VALUES (?, ?, ?, ?, ?)',
                    (category, name, image, price, description))
        conn.commit()
        return redirect(url_for('admin'))
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    conn.close()
    return render_template('admin/add_item.html', categories=categories)


"""
刪除餐點
"""
@app.route('/delete_menu_item/<item_id>', methods=['POST'])
def delete_menu_item(item_id):
    conn = create_connection()
    cursor = conn.cursor()
    # 執行刪除操作
    cursor.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    # 提交變更並關閉連接
    conn.commit()
    conn.close()

    # 跳轉回顯示餐點的頁面
    return redirect(url_for('admin'))

"""
編輯餐點
"""
@app.route('/edit_menu_item/<item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    if request.method == 'POST':
        # 從表單中獲取修改後的餐點資料
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        description = request.form['description']

        # 連接到 SQLite 資料庫
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # 更新資料庫中對應的餐點資料
        cursor.execute("UPDATE menu_items SET name=?, categories=?, price=?, description=? WHERE id=?", (name, category, price, description, item_id))
        conn.commit()

        # 關閉資料庫連接
        conn.close()

        # 跳轉回顯示餐點的頁面
        return redirect(url_for('admin'))
    # 連接到 SQLite 資料庫
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 根據 item_id 從資料庫中獲取餐點資料
    cursor.execute("SELECT * FROM menu_items WHERE id=?", (item_id,))
    item = cursor.fetchone()
    #品項種類
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()

    # 關閉資料庫連接
    conn.close()

    # 將餐點資料傳遞給編輯頁面進行顯示
    return render_template('admin/edit_item.html', item_id=item_id, item=item,categories=categories)




"""
列出所有成立的訂單:
訂單編號、會員名稱、會員手機號碼、成立時間、編輯按鈕
"""
@app.route('/manage_orders', methods=['GET'])
def manage_orders():
    conn = create_connection()
    cursor = conn.cursor()

    # 取得訂單資料
    cursor.execute('''
        SELECT orders.id, users.username, users.phone, orders.timestamp
        FROM orders
        INNER JOIN users ON orders.user_id = users.id
    ''')
    orders = cursor.fetchall()

    conn.close()

    return render_template('admin/manage_orders.html', orders=orders)


@app.route('/delete_order/<order_id>', methods=['GET','POST'])
def delete_order(order_id):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        # 删除订单及关联的购物车项
        cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        cursor.execute('DELETE FROM carts WHERE table_id = ?', (order_id,))
        conn.commit()
        print('Order deleted successfully')
    except Error as e:
        conn.rollback()
        print(f'Error deleting order: {e}')
    finally:
        conn.close()

    return redirect(url_for('manage_orders'))



"""
編輯特定訂單資料:
訂單編號、會員名稱、會員手機號碼、成立時間

購物車資料編輯:
數量變更、刪除按鈕、儲存。
"""
@app.route('/edit_order/<order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    conn = create_connection()
    cursor = conn.cursor()

    # 取得訂單資料
    cursor.execute('SELECT id, user_id, timestamp FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone()

    # 取得會員資料
    cursor.execute('SELECT username, phone FROM users WHERE id = ?', (order[1],))
    user = cursor.fetchone()

    # 取得購物車資料
    cursor.execute('''
        SELECT carts.id, menu_items.name, carts.quantity, menu_items.price
        FROM carts
        INNER JOIN menu_items ON carts.item_id = menu_items.id
        WHERE carts.table_id = ?
    ''', (order_id,))
    cart_items = cursor.fetchall()

    conn.close()
    #總額
    total_price = 0
    for item in cart_items:
        total_price += item[3] * item[2]


    return render_template('admin/edit_orders.html', order_id=order[0], username=user[0], phone=user[1], timestamp=order[2], cart_items=cart_items,total= total_price)


@app.route('/admin')
def admin():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items')
    items = cursor.fetchall()
    return render_template('admin.html',items=items)

# 註冊會員頁面
@app.route('/Register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # 儲存會員資料到資料庫
        save_user_to_db(username, phone, password)
        
        return redirect(url_for('login'))
    
    return render_template('register.html')



# """
# 已經登入，直接進行訂單處理
# """
# def user_to_order(phone):
#     order_id = cart_to_order(phone)
#     return redirect(url_for('created_order',order_id=order_id))


# 登入頁面
@app.route('/Login', methods=['GET', 'POST'])
@app.route('/Login/<status>', methods=['GET', 'POST'])
def login(status= 'to_history'):

      
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        status = request.form.get('status')
        # 檢查會員資料庫是否有該手機號碼和密碼
        if check_user_credentials(phone, password):
            # 登入成功，執行成立訂單
            if status == "to_order":
                ''' 設定 Cookie '''
                # order_id = cart_to_order(phone)
                response = make_response(cart_to_order(phone))
                response.set_cookie('islogin',value='true')
                response.set_cookie('user_id', phone)
                response.set_cookie('user_phone', phone)
                return response 
            elif status == "to_history":
                response = make_response(redirect('/'))
                response.set_cookie('islogin',value='true')
                response.set_cookie('user_id', phone)
                response.set_cookie('user_phone', phone)
                return response


        # 登入失敗，顯示錯誤訊息
        error_message = '手機號碼或密碼不正確'
        return render_template('login.html', error_message=error_message,status=status)        

    return render_template('login.html',status=status)

@app.route('/Logout', methods=['GET', 'POST'])
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('islogin',value='false')
    response.set_cookie('user_id', '', expires=0)
    response.set_cookie('user_phone', '', expires=0)
    return response
# 儲存會員資料到資料庫
def save_user_to_db(username, phone, password):
    conn =  sqlite3.connect('database.db')
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, phone, password) VALUES (?, ?, ?)', (username, phone, password))
            conn.commit()
            print('User data saved successfully')
        except Error as e:
            print(f'Error saving user data: {e}')
        conn.close()
    else:
        print('Error connecting to the database')


# 檢查會員資料庫是否有該手機號碼和密碼
def check_user_credentials(phone, password):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE phone=? AND password=?
            ''', (phone, password))
            user = cursor.fetchone()
            conn.close()
            if user is not None:
                return True
        except Error as e:
            print(f'Error checking user credentials: {e}')
    return False




if __name__ == '__main__':
    app.run(debug=True)