from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
import app_solar_calculation
import sqlite3
from flask import g
# import init_db
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


DATABASE = 'database.db'


def get_db():
    """Connect to the db"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def insert_db(query, args=()):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    con.close()

    return


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/', methods=["GET", "POST"])
def homepage():

    if request.method == "GET":
        return render_template("index.html")

    # If "Calculate" button is clicked
    if request.method == "POST":

        # Get raw values (strings) from form
        lat_in = request.form.get('coord_y')
        long_in = request.form.get('coord_x')
        rotate_in = request.form.get('rotation')
        surface_type = request.form.get('surface')
        year = request.form.get('year')

        location_name, today, version, loc, surface_type, rotation, rounded_tilts, historical_year = \
            app_solar_calculation.run(lat_in, long_in, rotate_in, surface_type, year)

        lat = str(lat_in)
        long = str(long_in)


        return render_template("results.html", location_name=location_name, today=today, version=version, lat_in=lat,
                               loc=loc, long_in=long, surface_type=surface_type, rotation=rotation, rounded_tilts=rounded_tilts,
                               historical_year=historical_year)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            show_username = "block"
            show_password = "none"
            show_pw_match = "none"
            show_exists = "none"
            # print("error_username")
            return render_template("signup.html", show_username=show_username, show_password=show_password,
                                   show_pw_match=show_pw_match, show_exists=show_exists)

        # Ensure password was submitted
        elif not request.form.get("password"):
            show_username = "none"
            show_password = "block"
            show_pw_match = "none"
            show_exists = "none"
            # print("error_password")
            return render_template("signup.html", show_username=show_username, show_password=show_password,
                                   show_pw_match=show_pw_match, show_exists=show_exists)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            show_username = "none"
            show_password = "none"
            show_pw_match = "block"
            show_exists = "none"
            # print("error_match")
            return render_template("signup.html", show_username=show_username, show_password=show_password,
                                   show_pw_match=show_pw_match, show_exists=show_exists)

        username = request.form.get("username")

        # Query database for username
        rows = query_db("SELECT * FROM users WHERE username = ?", (username,))
        # print(len(rows))

        if len(rows) != 0:
            show_username = "none"
            show_password = "none"
            show_pw_match = "none"
            show_exists = "block"
            # print("error_exists")
            return render_template("signup.html", show_username=show_username, show_password=show_password,
                                   show_pw_match=show_pw_match, show_exists=show_exists)

        # hash password to store in db rather than actual password
        hash = generate_password_hash(request.form.get("password"))

        insert_db("INSERT INTO users (username, hash) VALUES(?, ?);", (username, hash))

        # Redirect user to home page
        return render_template("index.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        show_username = "none"
        show_password = "none"
        show_pw_match = "none"
        show_exists = "none"
        return render_template("signup.html", show_username=show_username, show_password=show_password,
                               show_pw_match=show_pw_match, show_exists=show_exists)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            show_username = "block"
            show_password = "none"
            show_match = "none"
            # print("error_username")
            return render_template("login.html", show_username=show_username, show_password=show_password,
                                   show_match=show_match)

        # Ensure password was submitted
        elif not request.form.get("password"):
            show_username = "none"
            show_password = "block"
            show_match = "none"
            # print("error_password")
            return render_template("login.html", show_username=show_username, show_password=show_password,
                                   show_match=show_match)

        username = request.form.get("username")
        password = request.form.get("password")

        rows = query_db("SELECT * FROM users WHERE username = ?", (username,))
        # print(len(rows))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            show_username = "none"
            show_password = "none"
            show_match = "block"
            # print("error_match")
            return render_template("login.html", show_username=show_username, show_password=show_password,
                                   show_match=show_match)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # print(session["user_id"])

        # Redirect user to home page
        return render_template("index.html")

    # User reached route via GET (as by clicking a link or via redirect)
    # else:
    if request.method == "GET":
        show_username = "none"
        show_password = "none"
        show_match = "none"
        return render_template("login.html", show_username=show_username, show_password=show_password,
                               show_match=show_match)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/userfeedback", methods=["GET", "POST"])
def feedback():
    """Get user feedback"""
    if request.method == "GET":
        show = "none"
        return render_template("user_feedback.html", show=show)

    if request.method == "POST":

        fb = []
        # get all values from form in string format
        for i in range(1,6):
            # print(i)
            val = "rating" + str(i)
            if request.form.get(val) is not None:
                fb.append(int(request.form.get(val)))
            # If not all 5 mandatory elements are filled in, re-render template with warning
            else:
                show = "block"
                return render_template("user_feedback.html", show=show)

        if request.form.get('further') is not None:
            comment = request.form.get('further')
        else:
            comment = "-"

        # print(fb)
        # print(comment)

        # Add feedback to database
        insert_db("INSERT INTO feedback (q1, q2, q3, q4, q5, comment) VALUES (?, ?, ?, ?, ?, ?);",
                  (fb[0], fb[1], fb[2], fb[3], fb[4], comment))

        # Query overall satisfaction and count
        result = query_db("SELECT AVG(q1) FROM feedback;", one=True)
        overall_sat = int(result[0])

        result2 = query_db("SELECT count(*) FROM feedback;", one=True)
        count = int(result2[0])

        return render_template("thanks.html", overall_rating=overall_sat, count_submissions=count)


@app.route("/about", methods=["GET"])
def about():
    """load page with information about the project"""

    if request.method == "GET":
        return render_template("about.html")


@app.route("/savedsearches", methods=["GET", "POST"])
def saved():
    """load page with information about the project"""

    if request.method == "POST":
        search_id = request.form.get('redo')
        # print(search_id)

        search_params = query_db("SELECT * FROM savedSearches WHERE id = ?;", (search_id,), one=True)

        # Get individual values
        lat_in = search_params['lat_in']
        long_in = search_params['long_in']
        rotate_in = search_params['rotate_in']
        surface_type = search_params['surface_type']
        year = search_params['year']

        location_name, today, version, loc, surface_type, rotation, rounded_tilts, historical_year = \
            app_solar_calculation.run(lat_in, long_in, rotate_in, surface_type, year)

        lat = str(lat_in)
        long = str(long_in)

        return render_template("results.html", location_name=location_name, today=today, version=version, lat_in=lat,
                               loc=loc, long_in=long, surface_type=surface_type, rotation=rotation,
                               rounded_tilts=rounded_tilts,
                               historical_year=historical_year)

    if request.method == "GET":

        user_id = int(session["user_id"])
        user_searches = query_db("SELECT * FROM savedSearches WHERE user_id = ?;", (user_id,))

        return render_template("savedsearches.html", user_searches=user_searches)


@app.route("/results", methods=["POST"])
def save():
    """ save current search to db"""

    if request.method == "POST":

        # get time and date as string
        now = datetime.now()
        now_string = now.strftime("%d/%m/%Y %H:%M:%S")
        # print(f"now = {str(now_string)}")

        # user ID from session
        user_id = int(session["user_id"])
        # print(f"session id = {str(user_id)}")

        loc_name = request.form.get('loc_name')
        lat_in = request.form.get('lat_in')
        long_in = request.form.get('long_in')
        rotate_in = request.form.get('rotate_in')
        surface_type = request.form.get('surface_type')
        year = request.form.get('year')

        # print(f"loc_name = {str(loc_name)}")

        insert_db("INSERT INTO savedSearches (user_id, date, loc_name, lat_in, long_in, rotate_in, surface_type, "
                   "year) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", (user_id, now_string, loc_name, lat_in, long_in, rotate_in,
                                                              surface_type, year))

        user_searches = query_db("SELECT * FROM savedSearches WHERE user_id = ?;", (user_id,))

        return render_template("savedsearches.html", user_searches=user_searches)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
