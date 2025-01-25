from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from flask_mail import Mail, Message
from io import BytesIO
from mysql.connector import Error
import mysql.connector

app = Flask(__name__, template_folder='templates')
app.config['MAIL_SERVER'] = 'smtp.yourmailserver.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'felixlouiegregorio@gmail.com'
app.config['MAIL_PASSWORD'] = 'nighthawk5432'

db = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'northwave_db'
}
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db)
        if connection.is_connected():
            print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

mail = Mail(app)


@app.route('/send-message', methods=['POST'])
def send_message():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    # Insert into tbl_client
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO tbl_client (client_name, email, message) VALUES (%s, %s, %s)",
        (name, email, message)
    )
    connection.commit()
    cursor.close()
    connection.close()

    # Send email
    msg = Message(
        recipients=['felixlouiegregorio@gmail.com']
    )
    msg.body = f"""
    You have received a new message from your website contact form.
    
    Here are the details:
    Name: {name}
    Email: {email}
    Message: {message}
    """
    try:
        mail.send(msg)
        flash('Message sent successfully!', 'success')
    except Exception as e:
        flash(f'Failed to send message: {e}', 'danger')

    return redirect('property_single')



@app.route("/")
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/display_image/<int:agent_id>')
def display_image(agent_id):
    try:
        conn = mysql.connector.connect(**db)
        cursor = conn.cursor()

        # Modify the query to match your table and image column name
        cursor.execute(f"SELECT a_image FROM tbl_agent WHERE agent_id = {agent_id}")
        image_data = cursor.fetchone()

        image = image_data[0]  # Assuming image data is the first element

        cursor.close()
        conn.close()

        if image:
            return send_file(BytesIO(image), mimetype='image/jpeg')  # Adjust mimetype if needed
        else:
            print(f"No image data retrieved for agent ID: {agent_id}")
            return redirect(url_for('index'))  # Redirect if no image data retrieved
    except mysql.connector.Error as err:
        print(f"Error retrieving image: {err}")
        return redirect(url_for('index'))  # Redirect on database error

@app.route('/displayimage/<int:property_id>')
def displayimage(property_id):
    try:
        conn = mysql.connector.connect(**db)
        cursor = conn.cursor()
        # Use parameterized query to prevent SQL injection vulnerabilities
        query = "SELECT p_image FROM tbl_property WHERE property_id = %s"
        cursor.execute(query, (property_id,))  # Pass property_id as parameter
        image_data = cursor.fetchone()
        if image_data is None:  # Check if any data is retrieved
            print(f"No image data retrieved for property ID: {property_id}")
            return redirect(url_for('index'))  # Redirect if no image found
        image = image_data[0]  # Extract image data from the fetched row
        cursor.close()
        conn.close()
        if image:
            return send_file(BytesIO(image), mimetype='image/jpeg')  # Adjust mimetype if needed
        else:
            print(f"Image data retrieved but appears empty for property ID: {property_id}")
            return redirect(url_for('index'))  # Redirect if data is empty

    except mysql.connector.Error as err:
        print(f"Error retrieving image: {err}")
        return redirect(url_for('index'))  # Redirect on database error


@app.route('/propertygrid', methods=['GET', 'POST'])
def property_grid():
    filter_option = request.args.get('filter', 'all')
    keyword = request.args.get('keyword', '')
    property_type = request.args.get('type', 'All Type')
    bedrooms = request.args.get('bedrooms', 'Any')
    bathrooms = request.args.get('bathrooms', 'Any')
    min_price = request.args.get('min_price', 'Unlimited')

    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database", 500

    cursor = connection.cursor(dictionary=True)

    # Start with the base query
    query = "SELECT * FROM tbl_property WHERE 1=1"

    # Apply filters based on the selected option
    if filter_option == 'new_to_old':
        query += " ORDER BY property_id DESC"
    elif filter_option == 'for_rent':
        query += " AND property_type = 'Rent'"
    elif filter_option == 'for_sale':
        query += " AND property_type = 'Sale'"

    # Apply additional filters
    if keyword:
        query += f" AND (property_name LIKE '%{keyword}%' OR location LIKE '%{keyword}%' OR property_discription LIKE '%{keyword}%')"

    if property_type != 'All Type':
        query += f" AND property_type = '{property_type}'"

    if bedrooms != 'Any':
        query += f" AND beds = '{bedrooms}'"

    if bathrooms != 'Any':
        query += f" AND baths = '{bathrooms}'"

    if min_price != 'Unlimited':
        query += f" AND property_prize >= '{min_price}'"

    cursor.execute(query)
    properties = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('property-grid.html', properties=properties)



@app.route('/propertysingle/<int:property_id>')
def property_single(property_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch property details
    cursor.execute("SELECT * FROM tbl_property WHERE property_id = %s", (property_id,))
    property = cursor.fetchone()
    
    # Fetch agent details based on the agent's first name
    if property:
        cursor.execute("SELECT * FROM tbl_agent WHERE agent_firstname = %s", (property['agent'],))
        agent = cursor.fetchone()
    else:
        agent = None
    
    cursor.close()
    connection.close()
    
    return render_template('property-single.html', property=property, agent=agent)


@app.route("/bloggrid")
def bloggrid():
    return render_template('blog-grid.html')



@app.route('/agentgrid')
def agent_grid():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tbl_agent")
    agent = cursor.fetchall()
    connection.close()
    return render_template('agents-grid.html', agents=agent)

@app.route('/agentsingle/<int:agent_id>')
def agent_single(agent_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch agent details
    cursor.execute("SELECT * FROM tbl_agent WHERE agent_id = %s", (agent_id,))
    agent = cursor.fetchone()
    
    # Fetch properties associated with the agent
    if agent:
        cursor.execute("""
            SELECT * FROM tbl_property WHERE agent = %s
        """, (agent['agent_firstname'],))
        properties = cursor.fetchall()
    else:
        properties = []
    
    cursor.close()
    connection.close()
    
    return render_template('agent-single.html', agent=agent, properties=properties)





@app.route("/contact")
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)