from flask import Flask, render_template, redirect, url_for, request, flash
from forms import LoginForm, RegistrationForm, ComplaintForm, MunicipalForm, DeleteUserForm, DeleteMunicipalCouncilForm
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from smtplib import SMTP
import haversine as hs
# import folium
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import os

lat = 0
long = 0


def create_data(MunicipalData):
    all_names = [data.place for data in MunicipalData.query.all()]
    all_latitude = [data.latitude for data in MunicipalData.query.all()]
    all_longitude = [data.longitude for data in MunicipalData.query.all()]
    return {"Name": all_names, "Latitude": all_latitude, "Longitude": all_longitude}


def send_email(image, lat, long):
    council_id = get_min_distance_council_id(point_latitude=lat, point_longitude=long)
    SentEmailData(image=image.read(), latitude=lat, longitude=long, user_id=current_user.id, municipal_id=council_id)
    council_email = MunicipalData.query.get(council_id)
    html = f"<html><body><h1>This is an image of garbage <h1><img src='cid:image1'><br><p>we found this garbage at this location</p><a href='https://www.google.com/maps/search/?api=1&query={lat},{long}'></a></body></html>"
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Garbage Alert (From garbage management program)"
    msg['From'] = EMAIL
    msg['To'] = "tharanga123anuradha@gmail.com"
    mime_image = MIMEImage(_imagedata=image.read(), _subtype="jpg")
    mime_image.add_header("Content-ID", "<image1>")
    msg.attach(mime_image)
    msg.attach(MIMEText(html, "html"))
    smtp = SMTP("smtp.gmail.com")
    smtp.starttls()
    smtp.login(user=EMAIL, password=PASSWORD)
    smtp.sendmail(from_addr=EMAIL, to_addrs=council_email, msg=msg.as_string())


def get_min_distance_council_id(point_latitude, point_longitude):
    print(point_latitude, point_longitude)
    all_distances = []
    for data in MunicipalData.query.all():
        all_distances.append(calculate_distance(data.latitude, data.longitude, point_latitude, point_longitude))

    return all_distances.index(min(all_distances))


def calculate_distance(m_lat, m_long, lat, long):
    return hs.haversine((m_lat, m_long), (lat, long), unit=hs.Unit.MILES)


API_KEY = os.environ.get('api_key')
EMAIL = "miniprojectdp2022@gmail.com"
PASSWORD = os.environ.get("PASSWORD")
app = Flask(__name__)
Bootstrap(app=app)
app.secret_key = "tharanga"
# app.config['DATABASE_URL'] = 'postgres://lhnbqzquvpiwpa:4d9b4f85a1e0f26612341ead5e67f856b1c9c2ecf52777d7091e7b940ea679c7@ec2-54-173-77-184.compute-1.amazonaws.com:5432/d919gv8uldb2bvb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app=app)


@login_manager.user_loader
def load_user(user_id):
    return UserData.query.get(user_id)


class UserData(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class MunicipalData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    place = db.Column(db.String(80), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)


class SentEmailData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_data.id"))
    user = db.relationship("UserData", backref=db.backref('sent_email_data', lazy=True))
    municipal_id = db.Column(db.Integer, db.ForeignKey("municipal_data.id"))
    municipal = db.relationship("MunicipalData", backref=db.backref('sent_email_data', lazy=True))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)


db.create_all()


@app.route("/")
def home():
    return render_template("index.html", current_user=current_user,
                           map_state=os.path.exists("./templates/map_themed.html"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        try:
            not_logged_user = UserData.query.filter_by(username=username)[0]
            if check_password_hash(pwhash=not_logged_user.password, password=password):
                login_user(not_logged_user)
                return redirect(url_for("home"))
            else:
                flash("Wrong username or password")
        except IndexError:
            flash("Wrong username or password")

    return render_template("login.html", form=login_form, current_user=current_user)


@app.route('/logout', methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/register", methods=['GET', 'POST'])
def register():
    registration_form = RegistrationForm()
    if registration_form.validate_on_submit():
        if request.method == "POST":
            username = registration_form.username.data
            email = registration_form.email.data
            password = registration_form.password.data
            password_hash = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)
            try:
                if UserData.query.filter_by(username=username)[0].username != username:
                    registered_user = UserData(username=username, email=email, password=password_hash)
                    db.session.add(registered_user)
                    db.session.commit()
                    login_user(registered_user)
                    return redirect(url_for("home"))
                if UserData.query.filter_by(username=username)[0].username == username:
                    flash("Username already exist")
                    return redirect(url_for("register"))

            except IndexError:
                registered_user = UserData(username=username, email=email, password=password_hash)
                db.session.add(registered_user)
                db.session.commit()
                login_user(registered_user)
                return redirect(url_for("home"))

    return render_template("Register.html", form=registration_form, current_user=current_user)


@app.route("/complaint", methods=['GET', 'POST'])
def complaint():
    complaint_form = ComplaintForm()
    if request.method == "POST":
        location = request.form.get("location")

        try:
            global lat
            global long
            try:
                location = location.split(",")
            except AttributeError:
                pass

            lat = float(location[0])
            long = float(location[1])

        except TypeError:
            pass

    if complaint_form.validate_on_submit():
        image = complaint_form.image.data
        latitude = complaint_form.latitude.data
        longitude = complaint_form.longitude.data
        if latitude != 0 and longitude != 0:
            send_email(image=image, lat=latitude, long=longitude)
        else:
            send_email(image=image, lat=lat, long=long)
        redirect(url_for("home"))
    return render_template("complaint.html", form=complaint_form, current_user=current_user)


@app.route("/municipal_data", methods=["GET", "POST"])
def municipal_data():
    # dataset = create_data(MunicipalData)
    # try:
    #     location_map = folium.Map(width=600, height=500, location=[sum(dataset["Latitude"]) / len(dataset["Latitude"]), sum(dataset["Longitude"]) / len(dataset["Longitude"])], zoom_start=14, control_scale=True)
    #
    #     for i in range(len(dataset["Latitude"])):
    #         folium.Marker((dataset["Latitude"][i], dataset["Longitude"][i]), popup=dataset["Name"][i]).add_to(location_map)
    #         location_map.save("./templates/map.html", close_file=True)
    #         with open("./templates/map.html", "r+") as html:
    #             html_text = html.read().replace('"https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css"', "")
    #             html_text = html_text.replace('"https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css"', "")
    #             html_text = html_text.replace('"https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css"', "")
    #         with open("./templates/map_themed.html", "w") as html:
    #             html.write(html_text)
    # except ZeroDivisionError:
    #     pass

    if current_user.is_authenticated and current_user.id in [1, 2, 3, 4]:
        municipal_form = MunicipalForm()

        if request.method == "POST" and municipal_form.validate_on_submit():

            if not (MunicipalData.query.filter_by(
                    place=municipal_form.municipal_council.data) or MunicipalData.query.filter_by(
                    email=municipal_form.email.data) or MunicipalData.query.filter_by(
                    place=municipal_form.latitude.data) or MunicipalData.query.filter_by(
                    place=municipal_form.municipal_council.longitude)) or len(MunicipalData.query.all()) == 0:
                municipal_ = MunicipalData(place=municipal_form.municipal_council.data, email=municipal_form.email.data,
                                           latitude=municipal_form.latitude.data,
                                           longitude=municipal_form.longitude.data)

                db.session.add(municipal_)
                db.session.commit()
            else:
                flash("This information is already entered or this information is incorrect")
        return render_template("Municipal.html", form=municipal_form, current_user=current_user,
                               map_state=os.path.exists("./templates/map_themed.html"))
    else:
        return "<h1>You don't have access for this page</h1>", 403


@app.route("/Delete_user", methods=["GET", "POST"])
def delete_user():
    if current_user.is_authenticated and current_user.id in [1, 2, 3, 4]:
        delete_user_form = DeleteUserForm()
        all_users = UserData.query.all()
        if delete_user_form.validate_on_submit():
            removing_user = UserData.query.filter_by(username=delete_user_form.username.data).first()
            if not removing_user == None:
                db.session.delete(removing_user)
                db.session.commit()
            else:
                flash("User doesn't exist")
                return redirect(url_for("delete_user"))
            return redirect(url_for("home"))
        return render_template("delete_user.html", form=delete_user_form, all_users=all_users)
    else:
        return "<h1>You don't have access for this page</h1>", 403


@app.route("/Delete_municipal_council", methods=["GET", "POST"])
def delete_municipal_council():
    if current_user.is_authenticated and current_user.id in [1, 2, 3, 4]:
        delete_municipal_council_form = DeleteMunicipalCouncilForm()
        all_municipal_councils = MunicipalData.query.all()
        if delete_municipal_council_form.validate_on_submit():
            removing_municipal_council = MunicipalData.query.filter_by(
                place=delete_municipal_council_form.username.data).first()
            if not removing_municipal_council == None:
                db.session.delete(removing_municipal_council)
                db.session.commit()
            else:
                flash("Municipal council doesn't exist")
                return redirect(url_for("delete_user"))
            return redirect(url_for("home"))
        return render_template("delete_municipal_council.html", form=delete_municipal_council_form,
                               all_municipal_councils=all_municipal_councils)
    else:
        return "<h1>You don't have access for this page</h1>", 403


if __name__ == "__main__":
    app.run(debug=True)
