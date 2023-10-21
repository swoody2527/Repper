import os
from flask import Flask, render_template, request, flash, redirect, session
from cs50 import SQL
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
import json


# SEE LATEST REP STATS FOR EACH WORKOUT
# TELL USER WHAT THEIR UPCOMING WORKOUT IS

# YOUR UPCOMING WORKOUT IS MONDAY, ULPPL.
# YOU ARE AIMING FOR X REPS ON X EXERCISE


app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///repper.db")

# username = db.execute("SELECT username FROM users WHERE id = (?)", session.get("user_id"))[0]["username"]

@app.route("/", methods=["GET", "POST"])
def index():
        # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username", "info")
            return redirect("/")
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password", "info")
            return redirect("/")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username and/or password", "info")
            return redirect("/")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Login successful", "success")
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("index.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Logged out")
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")
    if request.method == "POST":
        if not username:
            flash("ERROR: username not provided")
            return redirect("/register")
        elif not password or not confirmation:
            flash("ERROR: password or confirmation not provided")
            return redirect("/register")
        elif password != confirmation:
            flash("ERROR: passwords do not match")
            return redirect("/register")
        #all fields exist and passwords match
        else:
            try:
                db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))
                flash("Registration succesfull")
                return redirect("/")
            except ValueError:
                flash("that username is taken")
                return redirect("/register")
    else:
        return render_template("register.html", password=password, username=username, confirmation=confirmation)


@app.route("/workoutadd", methods=["GET", "POST"])
def workoutadd():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    names = db.execute("SELECT DISTINCT workout_name FROM workout_plans")

    if request.method == "POST":
        if request.form.get("workoutname") and request.form.get("workoutname2"):
            flash("Please select only one name input", "danger")
            return redirect("/workoutadd")
        if not request.form.get("workoutname"):
            workoutName = request.form.get("workoutname2")
        else:
            workoutName = request.form.get("workoutname")
        exerName = request.form.getlist("exerName")
        exerWeight = request.form.getlist("exerWeight")
        exerInc = request.form.getlist("exerInc")
        exerURange = request.form.getlist("exerURange")
        exerLRange = request.form.getlist("exerLRange")
        exerSets = request.form.getlist("exerSets")
        day = request.form.get("day")
        for i in range(len(exerName)):
            db.execute("INSERT INTO workout_plans (user_id, workout_name, day, dayID, exercise, weight, sets, increment, l_range, u_range) VALUES (?,?,?,?,?,?,?,?,?,?)", session.get("user_id"), workoutName, day, int(daysconv(day)) ,exerName[i], exerWeight[i], exerSets[i], exerInc[i], exerLRange[i], exerURange[i])
        flash("Successfully added", "success")
        return redirect("/workoutadd")
    else:
        return render_template("workoutadd.html", days=days, names=names)


@app.route("/workouts", methods=["GET", "POST"])
def workouts():
    names = db.execute("SELECT DISTINCT workout_name FROM workout_plans")

    if request.method == "POST":
        selectedName = request.form.get("wName")
        workoutInfo = db.execute("SELECT * FROM workout_plans WHERE workout_name = (?) ORDER BY dayID", selectedName)
        days = db.execute("SELECT DISTINCT day FROM workout_plans WHERE workout_name = (?) ORDER BY dayID", selectedName)
        return render_template("workouts.html", names=names, info=workoutInfo, days=days, selectedName=selectedName)
    else:
        return render_template("workouts.html", names=names)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "POST":
        editDay = request.form.get("editRequest")
        name = request.form.get("editName")
        ogExercises = db.execute("SELECT DISTINCT exercise FROM workout_plans WHERE day = (?) AND workout_name = (?) AND user_id = (?)", editDay, name, session.get("user_id"))
        info = db.execute("SELECT * FROM workout_plans WHERE day = (?) AND workout_name = (?) AND user_id = (?)", editDay, name, session.get("user_id"))
        return render_template("edit.html", info=info, day=editDay, name=name, ogExercises=ogExercises)

@app.route("/editconfirm", methods=["GET", "POST"])
def confirmEdit():
    if request.method == "POST":
        day = request.form.get("day")
        name = request.form.get("name")
        exercise = request.form.getlist("exercise")
        ogExercise = request.form.getlist("ogExercise")
        weight = request.form.getlist("weight")
        sets = request.form.getlist("sets")
        increment = request.form.getlist("increment")
        lrange = request.form.getlist("lrange")
        urange = request.form.getlist("urange")

        for i in range(len(ogExercise)):
            db.execute("UPDATE workout_plans SET exercise = (?), weight = (?), sets = (?), increment = (?), l_range = (?), u_range = (?) WHERE exercise =(?) AND day = (?) AND workout_name = (?) AND user_id = (?)", exercise[i], weight[i], sets[i], increment[i], lrange[i], urange[i], ogExercise[i] ,day, name, session.get("user_id"))
        flash("Workout Updated", "success")
        return redirect("/workouts")




@app.route("/delete", methods=["POST"])
def delete():
    delDay = request.form.get("deleterequest")
    name = request.form.get("delName")
    db.execute("DELETE FROM workout_plans WHERE day=(?) AND workout_name = (?) AND user_id =(?)", delDay, name, session.get("user_id"))
    flash("Deleted " + delDay +"'s workout from " + name, "danger")
    return redirect("/workouts")



@app.route("/home", methods=["GET", "POST"])
def home():

    username = db.execute("SELECT username FROM users WHERE id = (?)", session.get("user_id"))[0]["username"]
    workoutNames = db.execute("SELECT DISTINCT workout_name FROM workout_plans WHERE user_id = (?)", session.get("user_id"))
    if request.method == "POST":
        wName = request.form.get("wName")
        rawreps = db.execute("SELECT DISTINCT exercise, reps_achieved, day, weight FROM workouts WHERE user_id = (?) AND workout_name = (?) ORDER BY date DESC", session.get("user_id"), wName)
        moveUps = []
        for row in rawreps:
            maxRepSet = db.execute("SELECT u_range, sets, increment FROM workout_plans WHERE workout_name = (?) AND exercise = (?) AND day = (?) AND user_id = (?)", wName, row["exercise"], row["day"], session.get("user_id"))
            checkWeight = db.execute("SELECT weight FROM workout_plans WHERE workout_name = (?) AND exercise = (?) AND day = (?) AND user_id =(?)", wName, row["exercise"], row["day"], session.get("user_id"))
            print(row["exercise"])
            print(checkWeight)
            print(row["weight"])
            if maxRepSet == []:
                continue
            if checkWeight == []:
                continue
            if row["weight"] != checkWeight[0]["weight"]:
                continue
            else:
                maxRepSet = maxRepSet[0]
                totalGoal = maxRepSet["u_range"] * maxRepSet["sets"]
                increment = maxRepSet["increment"]
                replreps = row["reps_achieved"].replace("'", '"')
                totalReps = json.loads(replreps)
                totalReps = sum([int(value) for value in totalReps])
                if totalReps >= totalGoal:
                    name = row["exercise"]
                    day = row["day"]
                    weight = row["weight"]
                    newweight = (weight + increment)
                    moveUps.append({"exercise": name,"weight": weight ,"day": day, "newweight": newweight, "increment": increment})
        # previous workout stuff
        try:
            preDate = db.execute("SELECT date, dayID FROM workouts WHERE user_id = (?) AND workout_name = (?) ORDER BY date DESC LIMIT 1", session.get("user_id"), wName)[0]
            preDateId = preDate['dayID']
            preWorkout = db.execute("SELECT * FROM workouts WHERE date = (?) AND user_id = (?) AND workout_name = (?)", preDate['date'], session.get("user_id"), wName)
            preDay = db.execute("SELECT workout_name, day FROM workouts WHERE date=(?) AND user_id =(?) AND workout_name = (?) LIMIT 1", preDate['date'], session.get("user_id"), wName)[0]
            # next workout stuff
            nextDateId = preDateId + 1
            nextWorkout = db.execute("SELECT * FROM workout_plans WHERE dayID = (?) AND user_id =(?) AND workout_name = (?)", nextDateId, session.get("user_id"), wName)

            # if not following workout is found initially, cycle until one is
            if nextWorkout == []:
                while nextWorkout == []:
                    if nextDateId == 7:
                        nextDateId = 1
                        nextWorkout = db.execute("SELECT * FROM workout_plans WHERE dayID = (?) AND user_id =(?) AND workout_name = (?)", nextDateId, session.get("user_id"), wName)
                    else:
                        nextDateId = nextDateId + 1
                        nextWorkout = db.execute("SELECT * FROM workout_plans WHERE dayID = (?) AND user_id =(?) AND workout_name = (?)", nextDateId, session.get("user_id"), wName)
                if nextWorkout != []:
                    nextDay = nextWorkout[0]["day"]
                    nextWorkoutName = nextWorkout[0]["workout_name"]
                    return render_template("home.html", name=username, preWorkout=preWorkout, preDate=preDate, preDay=preDay, nextWorkout=nextWorkout, nextName=nextWorkoutName, nextDay=nextDay, workoutNames=workoutNames, moveUps=moveUps)
            else:
                nextDay = nextWorkout[0]["day"]
                nextWorkoutName = nextWorkout[0]["workout_name"]
                return render_template("home.html", name=username, preWorkout=preWorkout, preDate=preDate, preDay=preDay, nextWorkout=nextWorkout, nextName=nextWorkoutName, nextDay=nextDay, workoutNames=workoutNames, moveUps=moveUps)
        except IndexError:
            flash("error", "danger")
            return redirect("/home")

    else:
        return render_template("home.html", name=username, workoutNames=workoutNames)

@app.route("/updateweight", methods=["POST"])
def updateweight():
    exercise = request.form.get("update")
    day = request.form.get("updateDay")
    workout = request.form.get("updateWorkout")
    newWeight = request.form.get("updateWeight")
    db.execute("UPDATE workout_plans SET weight = (?) WHERE exercise =(?) AND day =(?) AND workout_name = (?) AND user_id =(?)", newWeight, exercise, day, workout, session.get("user_id"))
    flash("updated", "success")
    return redirect("/home")

@app.route("/stats", methods=["GET", "POST"])
def stats():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    names = db.execute("SELECT DISTINCT workout_name FROM workout_plans")
    if request.method == "POST":
        selectedName = request.form.get("wName")
        if not selectedName:
            flash("Must select workout name", "danger")
            return redirect("/stats")
        selectedDay = request.form.get("wDay")
        if not selectedDay:
            flash("Must select day", "danger")
            return redirect("/stats")
        workoutInfo = db.execute("SELECT * FROM workouts WHERE workout_name = (?) AND day = (?)", selectedName, selectedDay)
        if workoutInfo == []:
            flash("No workouts found on " + selectedDay + " for " + selectedName, "danger")
            return redirect("/stats")
        dates = db.execute("SELECT DISTINCT date FROM workouts WHERE workout_name = (?) AND day =(?)", selectedName, selectedDay)
        return render_template("stats.html", names=names, info=workoutInfo, selectedName=selectedName, selectedDay=selectedDay, days=days, dates=dates)
    else:
        return render_template("stats.html", names=names, days=days)



@app.route("/workoutlog", methods=["GET", "POST"])
def workoutlog():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    names = db.execute("SELECT DISTINCT workout_name FROM workout_plans")
    user = session.get("user_id")

    if request.method == "POST":
        day = request.form.get("day")
        redirName = request.form.get("workoutname")
        qty = db.execute("SELECT DISTINCT exercise FROM workout_plans WHERE workout_name = (?) AND day = (?)", redirName, day)
        info = db.execute("SELECT * FROM workout_plans WHERE workout_name = (?) AND day = (?)", redirName, day)
        submitCheck = db.execute("SELECT * FROM workouts WHERE workout_name = (?) AND day =(?) AND date = (?)", redirName, day, date.today())
        if info == []:
            flash("A workout for " + day + " was not found in " + redirName, "danger")
            return render_template("workoutlog.html", names=names, days=days)
        elif submitCheck != []:
            flash("You have already recorded that workout today", "danger")
            return render_template("workoutlog.html", names=names, days=days)
        else:
            recentReps = db.execute("SELECT reps_achieved, exercise, weight FROM workouts WHERE workout_name = (?) AND day = (?) ORDER BY date DESC LIMIT (?)", redirName, day, len(qty))
            for row in recentReps:
                currentWeight = db.execute("SELECT weight FROM workout_plans WHERE exercise = (?) AND day = (?) AND workout_name = (?) AND user_id = (?)", row["exercise"], day, redirName, user)[0]["weight"]
                newWeightTarget = db.execute("SELECT l_range FROM workout_plans WHERE exercise = (?) AND day = (?) AND workout_name = (?) AND user_id = (?)", row["exercise"], day, redirName, user)[0]["l_range"]
                if row["weight"] != currentWeight:
                    row["reps_achieved"] = newWeightTarget


            return render_template("/logging.html", name=redirName, day=day, info=info, recentReps=recentReps)
    return render_template("workoutlog.html", names=names, days=days)


    # BLOCKS SUBMISSIONS TO A DAY WHICH DOES NOT EXIST FOR THAT WORKOUT.
    # CURRENTLY BLOCKS MULTIPLE SUBMISSIONS FOR THE SAME DAY. CHANGE TO JUST UPDATE DB INSTEAD???

@app.route("/logging", methods=["GET", "POST"])
def logging():
    user = session.get("user_id")

    if request.method == "POST":
        workoutName = request.form.get("name")
        exercises = request.form.getlist("exercise")
        day = request.form.get("day")
        for exercise in exercises:
            reps = request.form.getlist(exercise+"Reps")
            sets = db.execute("SELECT sets FROM workout_plans WHERE workout_name = (?) AND exercise =(?) AND day =(?)", workoutName, exercise, day)[0]['sets']
            if "''" in str(reps):
                flash("Input Error: Missing input on log submission", "danger")
                return redirect("/workoutlog")
            weight = request.form.get(exercise+"weight")
            print(weight)
            db.execute("INSERT INTO workouts (user_id, workout_name, day, dayID, exercise, weight, set_, reps_achieved, date) VALUES (?,?,?,?,?,?,?,?, date('now'))", user, workoutName, day, daysconv(day), exercise, weight, sets, str(reps))
        flash("Workout Logged", "info")
        return redirect("/workoutlog")
    else:
        return render_template("logging.html")



def daysconv(day):
    if day == "Monday":
        day = 1
        return day
    elif day == "Tuesday":
        day = 2
        return day
    elif day == "Wednesday":
        day = 3
        return day
    elif day == "Thursday":
        day = 4
        return day
    elif day == "Friday":
        day = 5
        return day
    elif day == "Saturday":
        day = 6
        return day
    elif day == "Sunday":
        day = 7
        return day
