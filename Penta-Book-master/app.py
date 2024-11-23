from flask import Flask, render_template, request, redirect, url_for, g, flash, session
import sqlite3
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from forms import LoginForm, RegisterForm, ShopRegisterForm

app = Flask(__name__)
app.config.from_object(Config)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def format_currency(value):
    return f'Rp{value:,.0f}'.replace(',', '.')


@app.route('/')
def index():
    template = 'index.html'
    if session.get('role') == 'buyer':
        template = 'buyer_index.html'
    elif session.get('role') == 'shop':
        template = 'shop_index.html'
    return render_template(template, books=[], format_currency=format_currency)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        dob = form.dob.data
        email = form.email.data
        phone_number = form.phone_number.data
        password = form.password.data
        buyer_address = form.buyer_address.data

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            db = get_db()
            db.execute('''INSERT INTO buyer (username, dob, email, phone_number, password, buyer_address) 
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (username, dob, email, phone_number, hashed_password, buyer_address))
            db.commit()
            flash('You have successfully registered! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        db = get_db()
        cur = db.execute('SELECT * FROM buyer WHERE username = ?', (username,))
        user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['buyer_id']
            session['username'] = user['username']
            session['role'] = 'buyer'
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/shop/register', methods=['GET', 'POST'])
def shop_register():
    form = ShopRegisterForm()
    if form.validate_on_submit():
        shop_name = form.shop_name.data
        owner_name = form.owner_name.data
        shop_phone = form.shop_phone.data
        password = form.password.data
        shop_address = form.shop_address.data
        shop_email = form.shop_email.data
        shop_description = form.shop_description.data

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            db = get_db()
            db.execute('''INSERT INTO shop (shop_name, owner_name, shop_phone, shop_address, shop_email, shop_description, password)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (shop_name, owner_name, shop_phone, shop_address, shop_email, shop_description, hashed_password))
            db.commit()
            flash('Your shop has been successfully registered! Please log in.', 'success')
            return redirect(url_for('shop_login'))
        except sqlite3.IntegrityError:
            flash('Shop name, email or phone number already exists.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')

    return render_template('shop_register.html', form=form)


@app.route('/shop/login', methods=['GET', 'POST'])
def shop_login():
    form = LoginForm()
    if form.validate_on_submit():
        shop_name = form.username.data
        password = form.password.data

        db = get_db()
        cur = db.execute('SELECT * FROM shop WHERE shop_name = ?', (shop_name,))
        shop = cur.fetchone()

        if shop and check_password_hash(shop['password'], password):
            session['shop_id'] = shop['shop_id']
            session['shop_name'] = shop['shop_name']
            session['role'] = 'shop'
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid shop name or password.', 'danger')

    return render_template('shop_login', form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/book/<int:book_id>')
def book(book_id):
    try:
        db = get_db()
        cur = db.execute('SELECT * FROM books WHERE book_id = ?', (book_id,))
        book = cur.fetchone()
        return render_template('book.html', book=book, format_currency=format_currency)
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('index'))


@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
def add_to_cart(book_id):
    if 'user_id' not in session:
        flash('You need to be logged in to add items to the cart.', 'warning')
        return redirect(url_for('login'))

    try:
        db = get_db()
        cur = db.execute('SELECT * FROM books WHERE book_id = ?', (book_id,))
        book = cur.fetchone()
        if book:
            cur = db.execute(
                'SELECT * FROM cartitems WHERE cart_id = (SELECT cart_id FROM cart WHERE buyer_id = ?) AND book_id = ?',
                (session['user_id'], book_id))
            item = cur.fetchone()
            if item:
                db.execute('UPDATE cartitems SET quantity = quantity + 1 WHERE cart_item_id = ?',
                           (item['cart_item_id'],))
            else:
                cart_cur = db.execute('SELECT cart_id FROM cart WHERE buyer_id = ?', (session['user_id'],))
                cart_id = cart_cur.fetchone()
                if not cart_id:
                    db.execute('INSERT INTO cart (buyer_id, status) VALUES (?, ?)', (session['user_id'], 'open'))
                    cart_id = db.execute('SELECT cart_id FROM cart WHERE buyer_id = ?',
                                         (session['user_id'],)).fetchone()
                db.execute('INSERT INTO cartitems (cart_id, book_id, quantity) VALUES (?, ?, ?)',
                           (cart_id['cart_id'], book_id, 1))
            db.commit()
            flash('Book added to cart!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('index'))


@app.route('/shop_books', methods=['GET'])
def shop_books():
    query = request.args.get('query', '')
    genre = request.args.get('genre', '')
    price_min = request.args.get('price_min', 0)
    price_max = request.args.get('price_max', float('inf'))
    sort = request.args.get('sort', 'book_name')

    db = get_db()
    cursor = db.cursor()

    sql_query = "SELECT * FROM books WHERE 1=1"
    parameters = []

    if query:
        sql_query += " AND (book_name LIKE ? OR author LIKE ?)"
        parameters.extend(['%' + query + '%', '%' + query + '%'])

    if genre:
        sql_query += " AND genre = ?"
        parameters.append(genre)

    sql_query += " AND price BETWEEN ? AND ?"
    parameters.extend([price_min, price_max])

    if sort == 'price_asc':
        sql_query += " ORDER BY price ASC"
    elif sort == 'price_desc':
        sql_query += " ORDER BY price DESC"
    else:
        sql_query += f" ORDER BY {sort}"

    cursor.execute(sql_query, parameters)
    books = cursor.fetchall()

    return render_template('shop_books.html', books=books, format_currency=format_currency)


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('You need to be logged in to view your cart.', 'warning')
        return redirect(url_for('login'))

    try:
        db = get_db()
        cur = db.execute('''
            SELECT b.book_id, b.book_name, b.author, IFNULL(b.price, 0) as price, ci.quantity
            FROM cartitems ci
            JOIN books b ON ci.book_id = b.book_id
            JOIN cart c ON ci.cart_id = c.cart_id
            WHERE c.buyer_id = ? AND c.status = "open"
        ''', (session['user_id'],))
        cart_items = cur.fetchall()
        return render_template('cart.html', cart_items=cart_items, format_currency=format_currency)
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('index'))



@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('You need to be logged in to checkout.', 'warning')
        return redirect(url_for('login'))

    try:
        db = get_db()
        user_id = session['user_id']

        # Get the cart items
        cur = db.execute('''
            SELECT b.book_name, b.desc, b.price, c.quantity, b.book_id, sh.shop_id, sh.price as individual_price, 
                            (c.quantity * b.price) as total_price, sh.shop_email, sh.shop_name, sh.owner_name
            FROM cartitems c
            JOIN books b ON c.book_id = b.book_id
            JOIN shop sh ON sh.shop_id = b.shop_id
            WHERE c.cart_id = (SELECT cart_id FROM cart WHERE buyer_id = ?)
        ''', (user_id,))
        cart_items = cur.fetchall()

        if request.method == 'POST':
            # Create a new order
            total_price = sum(item['price'] * item['quantity'] for item in cart_items)
            address = request.form.get('address')  # Collect delivery address
            db.execute(
                'INSERT INTO orders (cart_id, buyer_id, subtotal, total, status, delivery_address, order_date) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
                (cart_items[0][0] if cart_items else 0, user_id, total_price, total_price, 'initiated', address))
            order_id = db.lastrowid

            for item in cart_items:
                db.execute(
                    'INSERT INTO orderitems (order_id, book_id, shop_id, quantity, price, total_price) VALUES (?, ?, ?, ?, ?, ?)',
                    (order_id, item['book_id'], item['shop_id'], item['quantity'], item['individual_price'],
                     item['total_price']))

            db.execute('UPDATE cart SET status = ? WHERE buyer_id = ?', ('complete', user_id))
            db.commit()
            flash('Your order has been placed.', 'success')
            return redirect(url_for('index'))

        total = sum(item['price'] * item['quantity'] for item in cart_items)
        return render_template('checkout.html', cart=cart_items, total=total, format_currency=format_currency)
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('index'))


@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
def payment(order_id):
    if 'user_id' not in session:
        flash('You need to be logged in to make a payment.', 'warning')
        return redirect(url_for('login'))

    db = get_db()
    if request.method == 'POST':
        method_id = request.form.get('method')
        transaction_id = request.form.get('transaction_id')

        # Fetch order details
        order = db.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchone()

        # Call mock payment gateway
        payment_url = 'http://localhost:5001/process_payment'
        data = {
            "amount": order['total'],
            "method_id": method_id,
            "order_id": order_id
        }

        try:
            response = requests.post(payment_url, json=data)
            response_data = response.json()
            if response.status_code == 200 and response_data['status'] == 'success':
                transaction_id = response_data['data']['transaction_id']
                payment_status = response_data['data']['payment_status']

                # Insert payment details
                db.execute(
                    'INSERT INTO payments (method_id, order_id, transaction_id, payment_date, payment_status) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)',
                    (method_id, order_id, transaction_id, payment_status))
                db.execute('UPDATE orders SET status = ? WHERE order_id = ?', ('paid', order_id))
                db.commit()
                flash('Payment successful!', 'success')
            else:
                flash('Payment declined by the gateway.', 'danger')
        except requests.ConnectionError:
            flash('Failed to connect to the payment gateway.', 'danger')

        return redirect(url_for('index'))

    # Fetch available payment methods
    methods = db.execute('SELECT * FROM paymentmethods').fetchall()
    return render_template('payment.html', methods=methods)


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
