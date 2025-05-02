from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import pymysql
from datetime import datetime, timedelta
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure cookies to include the 'Secure' directive
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Ensures cookies are only sent over HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevents JavaScript access to cookies
    SESSION_COOKIE_SAMESITE='Lax'  # Mitigates CSRF attacks
)

# Database connection
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'MYsqlpass@123'),
        db=os.getenv('DB_NAME', 'auction_db'),
        cursorclass=pymysql.cursors.DictCursor
    )

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to fetch auction details and bids
def get_auction_and_bids(auction_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM auctions WHERE id = %s", (auction_id,))
        auction = cursor.fetchone()

        cursor.execute("""
            SELECT b.bid_amount, b.bid_time, u.username
            FROM bids b
            JOIN users u ON b.user_id = u.id
            WHERE b.item_id = %s
            ORDER BY b.bid_amount DESC
        """, (auction_id,))
        bids = cursor.fetchall()

        return auction, bids
    except Exception as e:
        print(f"Error fetching auction and bids: {e}")
        return None, []
    finally:
        cursor.close()
        connection.close()

# Landing page
@app.route('/')
def index():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Fetch only active auctions (end_time > NOW())
        cursor.execute("SELECT * FROM auctions WHERE end_time > NOW()")
        auctions = cursor.fetchall()
        # Process each auction to ensure image paths are correct
        for auction in auctions:
            if auction['image_path']:
                auction['image_path'] = url_for('static', filename=auction['image_path'].lstrip("static/").replace("\\", "/"))
    finally:
        cursor.close()
        connection.close()

    username = session.get('username', None)
    return render_template('index.html', auctions=auctions, username=username)

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        try:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except Exception as e:
            flash('Error hashing password. Please try again.')
            return redirect(url_for('register'))
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
                           (username, email, hashed_password, user_type))
            connection.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error during registration: {e}")
            return redirect(url_for('register'))
        finally:
            cursor.close()
            connection.close()
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                flash('Login successful.')
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials. Please check your email and password.')
        except Exception as e:
            flash('An error occurred during login. Please try again.')
            print(f"Login error: {e}")
        finally:
            cursor.close()
            connection.close()
    return render_template('login.html')

# User logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

# Add auction
@app.route('/add_auction', methods=['GET', 'POST'])
def add_auction():
    if 'user_id' not in session or session['user_type'] != 'seller':
        flash('Access denied.')
        return redirect(url_for('login'))

    title = request.args.get('title', '')
    description = request.args.get('description', '')
    request_id = request.args.get('request_id', None)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        starting_price = request.form['starting_price']
        end_time = request.form['end_time']  # Provided in ISO 8601 format (e.g., '2025-05-01T11:27')

        try:
            # Convert ISO 8601 format to '%Y-%m-%d %H:%M:%S'
            end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
            if datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') <= datetime.now():
                flash('End time must be in the future.', 'danger')
                return redirect(url_for('add_auction', title=title, description=description, request_id=request_id))
        except ValueError:
            flash('Invalid date format. Please use the correct format.', 'danger')
            return redirect(url_for('add_auction', title=title, description=description, request_id=request_id))

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            relative_image_path = os.path.join('uploads', filename)
            absolute_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                image.save(absolute_image_path)
            except Exception as e:
                flash('Error saving the image. Please try again.', 'danger')
                print(f"Error saving image: {e}")
                return redirect(url_for('add_auction', title=title, description=description, request_id=request_id))
        else:
            flash('Invalid file type. Please upload a valid image.', 'danger')
            return redirect(url_for('add_auction', title=title, description=description, request_id=request_id))

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            # Add auction to the database
            cursor.execute("""
                INSERT INTO auctions (title, description, starting_price, end_time, seller_id, image_path)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, starting_price, end_time, session['user_id'], relative_image_path))
            connection.commit()

            # Delete the request after adding the auction
            if request_id:
                cursor.execute("DELETE FROM item_requests WHERE id = %s", (request_id,))
                connection.commit()

            flash('Auction added successfully.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash('An error occurred while adding the auction.', 'danger')
            print(f"Error adding auction: {e}")
        finally:
            cursor.close()
            connection.close()
    return render_template('add_auction.html', title=title, description=description)

# View requests
@app.route('/view_requests', methods=['GET', 'POST'])
def view_requests():
    if 'user_id' not in session or session['user_type'] != 'seller':
        flash('Unauthorized access.')
        return redirect(url_for('index'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT ir.id, ir.item_name, ir.description, ir.budget, ir.status, u.username AS buyer_name
            FROM item_requests ir
            JOIN users u ON ir.buyer_id = u.id
            WHERE ir.status = 'Pending'
        """)
        requests = cursor.fetchall()
        if request.method == 'POST':
            request_id = request.form.get('request_id')
            if request_id:
                cursor.execute("UPDATE item_requests SET status = 'Matched', seller_id = %s WHERE id = %s",
                               (session['user_id'], request_id))
                connection.commit()
                flash('Request approved successfully.', 'success')
            else:
                flash('Invalid request ID.', 'danger')
    except Exception as e:
        flash('An error occurred while processing the request.', 'danger')
        print(f"Error in view_requests route: {e}")
    finally:
        cursor.close()
        connection.close()
    return render_template('view_requests.html', requests=requests)

# Respond to request
@app.route('/respond_to_request', methods=['GET', 'POST'])
def respond_to_request():
    if 'user_id' not in session or session['user_type'] != 'seller':
        flash('Unauthorized access.')
        return redirect(url_for('index'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT ir.id, ir.item_name, ir.description, ir.budget, ir.status
            FROM item_requests ir
            WHERE ir.seller_id = %s AND ir.status = 'Matched'
        """, (session['user_id'],))
        available_requests = cursor.fetchall()
        if request.method == 'POST':
            request_id = request.form['request_id']
            cursor.execute("SELECT * FROM item_requests WHERE id = %s", (request_id,))
            request_data = cursor.fetchone()
            if request_data:
                # Redirect to add auction with pre-filled data and pass request_id
                return redirect(url_for('add_auction', title=request_data['item_name'], description=request_data['description'], request_id=request_id))
            else:
                flash('Request not found.', 'danger')
    except Exception as e:
        flash('An error occurred while processing the request.', 'danger')
        print(f"Error in respond_to_request route: {e}")
    finally:
        cursor.close()
        connection.close()
    return render_template('respond_to_request.html', available_requests=available_requests)

# Buyer request
@app.route('/buyer_request', methods=['GET', 'POST'])
def buyer_request():
    if 'user_id' not in session or session['user_type'] != 'buyer':
        flash('Unauthorized access.')
        return redirect(url_for('index'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Handle form submission to place a request
        if request.method == 'POST':
            item_name = request.form['item_name']
            description = request.form['description']
            budget = request.form['budget']  # New field for budget
            if not item_name or not description or not budget:
                flash('All fields are required.', 'danger')
                return redirect(url_for('buyer_request'))

            cursor.execute("""
                INSERT INTO item_requests (buyer_id, item_name, description, budget, status)
                VALUES (%s, %s, %s, %s, 'Pending')
            """, (session['user_id'], item_name, description, budget))
            connection.commit()
            flash('Request submitted successfully.', 'success')

        # Fetch existing requests for the logged-in buyer
        cursor.execute("SELECT * FROM item_requests WHERE buyer_id = %s", (session['user_id'],))
        requests = cursor.fetchall()
    except Exception as e:
        flash('An error occurred while processing your request.', 'danger')
        print(f"Error in buyer_request route: {e}")
    finally:
        cursor.close()
        connection.close()

    return render_template('buyer_request.html', requests=requests)

# Auction detail and bid placement
@app.route('/auction/<int:auction_id>', methods=['GET', 'POST'])
def auction_detail(auction_id):
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to place a bid.')
            return redirect(url_for('login'))

        bid_amount = request.form['bid_amount']
        user_id = session['user_id']

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            # Check if the bid is higher than the current highest bid or starting price
            cursor.execute("""
                SELECT COALESCE(MAX(b.bid_amount), (SELECT starting_price FROM auctions WHERE id = %s)) AS highest_bid
                FROM bids b
                WHERE b.item_id = %s
            """, (auction_id, auction_id))
            highest_bid = cursor.fetchone()['highest_bid']
            if float(bid_amount) <= float(highest_bid):
                flash(f"Your bid must be higher than the current highest bid of ₹{highest_bid}.", 'danger')
                return redirect(url_for('auction_detail', auction_id=auction_id))
            # Insert the bid into the database
            cursor.execute("""
                INSERT INTO bids (user_id, item_id, bid_amount, bid_time)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, auction_id, bid_amount))
            connection.commit()
            flash('Bid placed successfully.', 'success')
        except Exception as e:
            flash('An error occurred while placing the bid.', 'danger')
            print(f"Error placing bid: {e}")
        finally:
            cursor.close()
            connection.close()

    # Fetch auction details and bids
    auction, bids = get_auction_and_bids(auction_id)
    if not auction:
        flash('Auction not found.', 'danger')
        return redirect(url_for('index'))

    # Check if the auction has ended
    auction_ended = datetime.now() > auction['end_time']

    # Determine if the logged-in user is the winner
    is_winner = False
    if auction_ended and 'user_id' in session:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT b.user_id AS winner_id
                FROM bids b
                WHERE b.item_id = %s
                ORDER BY b.bid_amount DESC
                LIMIT 1
            """, (auction_id,))
            result = cursor.fetchone()
            if result and result['winner_id'] == session['user_id']:
                is_winner = True
        except Exception as e:
            print(f"Error checking winner: {e}")
        finally:
            cursor.close()
            connection.close()

    # Ensure the image path is passed correctly
    auction['image_path'] = url_for('static', filename=auction['image_path'].removeprefix('static/').replace("\\", "/"))
    print(f"Image path being passed to template: {auction['image_path']}")

    return render_template('auction-detail.html', auction=auction, bids=bids, is_winner=is_winner, auction_ended=auction_ended)

# Match requests
@app.route('/match_requests')
def match_requests():
    if 'user_id' not in session or session['user_type'] != 'buyer':
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Fetch matched requests for the logged-in buyer
        cursor.execute("""
            SELECT ir.id, ir.item_name, ir.description, ir.budget, ir.status, u.username AS seller_name
            FROM item_requests ir
            JOIN users u ON ir.seller_id = u.id
            WHERE ir.buyer_id = %s AND ir.status = 'Matched'
        """, (session['user_id'],))
        matched_requests = cursor.fetchall()
    except Exception as e:
        flash('An error occurred while fetching matched requests.', 'danger')
        print(f"Error in match_requests route: {e}")
        matched_requests = []
    finally:
        cursor.close()
        connection.close()

    return render_template('match_requests.html', matched_requests=matched_requests)

# Auction history
@app.route('/auction_history')
def auction_history():
    if 'user_id' not in session:
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Calculate the date one week ago
        one_week_ago = datetime.now() - timedelta(days=7)

        # Fetch auctions that ended in the last week
        cursor.execute("""
            SELECT a.title, a.end_time, 
                   COALESCE(MAX(b.bid_amount), a.starting_price) AS final_bid,
                   (SELECT u.username 
                    FROM bids b1 
                    JOIN users u ON b1.user_id = u.id 
                    WHERE b1.item_id = a.id 
                    ORDER BY b1.bid_amount DESC 
                    LIMIT 1) AS winner,
                   a.image_path
            FROM auctions a 
            LEFT JOIN bids b ON a.id = b.item_id
            WHERE a.end_time <= NOW() AND a.end_time >= %s
            GROUP BY a.id, a.title, a.end_time, a.starting_price, a.image_path
        """, (one_week_ago,))
        auctions = cursor.fetchall()
        # Ensure image paths are processed correctly
        for auction in auctions:
            if auction['image_path']:
                auction['image_path'] = url_for('static', filename=auction['image_path'].lstrip("static/").replace("\\", "/"))
    except Exception as e:
        flash('An error occurred while fetching auction history.', 'danger')
        print(f"Error in auction_history route: {e}")
        auctions = []
    finally:
        cursor.close()
        connection.close()
    return render_template('auction_history.html', auctions=auctions)

# Seller dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session['user_type'] != 'seller':
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Fetch all auctions created by the logged-in seller
        cursor.execute("""
            SELECT * FROM auctions
            WHERE seller_id = %s
        """, (session['user_id'],))
        auctions = cursor.fetchall()
        # Ensure image paths are processed correctly
        for auction in auctions:
            if auction['image_path']:
                auction['image_path'] = url_for('static', filename=auction['image_path'].lstrip("static/").replace("\\", "/"))
    except Exception as e:
        flash('An error occurred while fetching your auctions.', 'danger')
        print(f"Error in dashboard route: {e}")
        auctions = []
    finally:
        cursor.close()
        connection.close()
    # Pass the current time to the template
    return render_template('dashboard.html', auctions=auctions, now=datetime.now())

@app.route('/feedback_payment/<int:auction_id>', methods=['GET', 'POST'])
def feedback_payment(auction_id):
    if 'user_id' not in session or session['user_type'] != 'buyer':
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Fetch auction details and check if the logged-in user is the winner
        cursor.execute("""
            SELECT a.title, a.description, a.starting_price, 
                   COALESCE(MAX(b.bid_amount), a.starting_price) AS final_bid,
                   (SELECT b.user_id 
                    FROM bids b 
                    WHERE b.item_id = a.id 
                    ORDER BY b.bid_amount DESC 
                    LIMIT 1) AS winner_id,
                   a.seller_id,
                   a.image_path
            FROM auctions a
            LEFT JOIN bids b ON a.id = b.item_id
            WHERE a.id = %s
            GROUP BY a.id
        """, (auction_id,))
        auction = cursor.fetchone()

        if not auction:
            flash('Auction not found.', 'danger')
            return redirect(url_for('index'))

        if auction['winner_id'] != session['user_id']:
            flash('You are not the winner of this auction.', 'danger')
            return redirect(url_for('index'))

        # Handle feedback submission
        if request.method == 'POST' and 'feedback' in request.form:
            rating = request.form['rating']
            comments = request.form['comments']
            try:
                cursor.execute("""
                    INSERT INTO feedback (reviewer_id, reviewed_user_id, rating, review)
                    VALUES (%s, %s, %s, %s)
                """, (session['user_id'], auction['seller_id'], rating, comments))
                connection.commit()
                flash('Feedback submitted successfully.', 'success')
            except Exception as e:
                flash('An error occurred while submitting feedback.', 'danger')
                print(f"Error in feedback_payment route: {e}")

        # Handle payment submission
        if request.method == 'POST' and 'payment' in request.form:
            # Redirect to the payment confirmation page using a GET request
            return redirect(url_for('payment_confirmation', auction_id=auction_id))

    except Exception as e:
        flash('An error occurred while fetching auction details.', 'danger')
        print(f"Error in feedback_payment route: {e}")
    finally:
        cursor.close()
        connection.close()

    # Ensure the image path is passed correctly
    auction['image_path'] = url_for('static', filename=auction['image_path'])

    return render_template('feedback_payment.html', auction=auction)

@app.route('/payment_confirmation/<int:auction_id>', methods=['GET', 'POST'])
def payment_confirmation(auction_id):
    if 'user_id' not in session:
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Fetch auction details
        cursor.execute("""
            SELECT a.title, COALESCE(MAX(b.bid_amount), a.starting_price) AS final_bid
            FROM auctions a
            LEFT JOIN bids b ON a.id = b.item_id
            WHERE a.id = %s
            GROUP BY a.id
        """, (auction_id,))
        auction = cursor.fetchone()

        if not auction:
            flash('Auction not found.', 'danger')
            return redirect(url_for('index'))

        # Display payment success message
        if request.method == 'POST':
            flash(f"🎉 Payment of ₹{auction['final_bid']} for '{auction['title']}' completed successfully!", 'success')
            flash("Congratulations! You are the winner of this auction.", 'success')

    except Exception as e:
        flash('An error occurred while fetching auction details.', 'danger')
        print(f"Error in payment_confirmation route: {e}")
    finally:
        cursor.close()
        connection.close()

    return render_template('payment_confirmation.html', auction=auction)

@app.route('/transaction_history')
def transaction_history():
    if 'user_id' not in session:
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Fetch transaction history for the logged-in user
        cursor.execute("""
            SELECT a.title AS item_name, t.bid_amount AS final_bid, u.username AS winner
            FROM transactions t
            JOIN auctions a ON t.item_id = a.id
            JOIN users u ON t.buyer_id = u.id
            WHERE t.seller_id = %s OR t.buyer_id = %s
        """, (session['user_id'], session['user_id']))
        transactions = cursor.fetchall()
    except Exception as e:
        flash('An error occurred while fetching transaction history.', 'danger')
        print(f"Error in transaction_history route: {e}")
        transactions = []
    finally:
        cursor.close()
        connection.close()

    return render_template('transaction_history.html', transactions=transactions)

if __name__ == '__main__':
    app.run(debug=True)