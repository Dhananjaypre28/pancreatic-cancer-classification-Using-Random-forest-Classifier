import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3 as sql



app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


# Load the dataset from CSV file
df = pd.read_csv('data/Debernardi et al 2020 data.csv')  # Update with your actual dataset file path

# Mapping for diagnosis labels
diagnosis_mapping = {
    1: "Control (No pancreatic disease)",
    2: "Benign hepatobiliary disease (including chronic pancreatitis)",
    3: "Pancreatic ductal adenocarcinoma (Pancreatic cancer)"
}

# Selecting the features from the dataset
X = df[['plasma_CA19_9', 'creatinine', 'LYVE1', 'REG1B', 'TFF1', 'REG1A']]
y = df['diagnosis']

# Create a Random Forest classifier
clf = RandomForestClassifier()
clf.fit(X, y)


@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact')
def contact():
    return render_template('Contact.html')

@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    msg = None
    if request.method == "POST":
        email = request.form['email']
        password = request.form['pwd']

        with sql.connect("data.db") as con:
            c = con.cursor()
            c.execute("SELECT email, password FROM users WHERE email = ? AND password = ?", (email, password))
            r = c.fetchall()
            if r:
                return render_template("UserHome.html")
            else:
                msg = "Invalid email or password. Please try again."

    return render_template("UserLogin.html", msg=msg)


@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    msg = None
    if request.method == "POST":
        email = request.form['email']
        password = request.form['pwd']

        with sql.connect("data.db") as con:
            c = con.cursor()
            c.execute("SELECT email, password FROM admin WHERE email = ? AND password = ?", (email, password))
            r = c.fetchall()
            if r:
                return render_template("AdminHome.html")
            else:
                msg = "Invalid email or password. Please try again."

    return render_template("AdminLogin.html", msg=msg)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    msg = None
    if request.method == "POST":
        username = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        upassword = request.form['pwd']
        
        try:
            with sql.connect("data.db") as con:
                c = con.cursor()
                c.execute("INSERT INTO users (username, email, mobile, password) VALUES (?, ?, ?, ?)", 
                          (username, email, mobile, upassword))
                con.commit()
                msg = "Signup Successful. Please login."
        except sql.Error as e:
            con.rollback()
            msg = f"Error occurred: {e}"
        
        return render_template("UserLogin.html", success_msg=msg)
    
    return render_template("Registration.html", msg=msg)



@app.route('/userhome')
def userhome():
    return render_template('UserHome.html')

@app.route('/userlogout')
def user_logout():
    # Clear the session data to log the user out
    session.clear()
    return redirect(url_for('userlogin'))

@app.route('/userfaqlist')
def user_faq_list():
    conn = sql.connect('data.db')
    faqs = conn.execute('SELECT * FROM faq').fetchall()
    conn.close()
    return render_template('UserFaqList.html', faqs=faqs)

@app.route('/adminhome')
def adminhome():
    return render_template('AdminHome.html')

# Function to fetch users from the database
def get_users():
    conn = sql.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, mobile FROM users")
    users = c.fetchall()
    conn.close()
    return users

# Route to display the list of users
@app.route('/adminuserslist')
def admin_users_list():
    users = get_users()
    return render_template('AdminUsersList.html', users=users)

# Route to delete a user
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = sql.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_users_list'))

@app.route('/adminfaqlist')
def faq_list():
    conn = sql.connect('data.db')
    faqs = conn.execute('SELECT * FROM faq').fetchall()
    conn.close()
    return render_template('AdminFaqList.html', faqs=faqs)

@app.route('/delete_faq/<int:faq_id>', methods=['POST'])
def delete_faq(faq_id):
    conn = sql.connect('data.db')
    conn.execute('DELETE FROM faq WHERE id = ?', (faq_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('faq_list'))

@app.route('/add_faq', methods=['GET', 'POST'])
def add_faq():
    if request.method == 'POST':
        subject = request.form['subject']
        answer = request.form['answer']
        conn = sql.connect('data.db')
        conn.execute('INSERT INTO faq (subject, answer) VALUES (?, ?)', (subject, answer))
        conn.commit()
        conn.close()
        return redirect(url_for('faq_list'))
    return render_template('AdminAddFAQ.html')

@app.route('/adminlogout')
def admin_logout():
    # Clear the session data to log the user out
    session.clear()
    return redirect(url_for('adminlogin'))


# Route for the detection form
@app.route('/detection', methods=['GET', 'POST'])
def detection():
    if request.method == 'POST':
        # Get user input from the form
        plasma_CA19_9 = float(request.form['plasma_CA19_9'])
        creatinine = float(request.form['creatinine'])
        LYVE1 = float(request.form['LYVE1'])
        REG1B = float(request.form['REG1B'])
        TFF1 = float(request.form['TFF1'])
        REG1A = float(request.form['REG1A'])

        # Make prediction based on user input
        user_input = [[plasma_CA19_9, creatinine, LYVE1, REG1B, TFF1, REG1A]]
        prediction = clf.predict(user_input)

        # Map prediction to diagnosis label
        diagnosis_result = diagnosis_mapping.get(prediction[0], "Unknown")

        return render_template('Result.html', diagnosis=diagnosis_result)

    return render_template('Detection.html')


if __name__ == '__main__':
    app.run(debug=True)
