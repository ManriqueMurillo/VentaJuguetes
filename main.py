import sqlalchemy.exc
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, exc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import abort
from wtforms.validators import DataRequired
from sqlalchemy.future import select
from sqlalchemy.sql import func
import requests
import os
import datetime
import gunicorn

class Base(DeclarativeBase):
    pass

db_monsters=SQLAlchemy(model_class=Base)

class MonsterTrucks(db_monsters.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True)
    rating: Mapped[str] = mapped_column(String(250), nullable=True)
    price: Mapped[float] = mapped_column(String(250), nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)
    status: Mapped[str] = mapped_column(String(250), nullable=True)

class User(UserMixin, db_monsters.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))

class TruckAddForm(FlaskForm):
    name = StringField(label='Nombre')
    rating = StringField(label='Rating')
    review = StringField(label='Descripcion')
    price = StringField(label='Precio')
    status = StringField(label='Estado')
    img_url = StringField(label='Imagen')
    submit_button = SubmitField(label="Agregar")

class UserForm(FlaskForm):
    username = StringField(label='User')
    email = StringField(label='Email')
    password = PasswordField(label='Password')
    submit_button = SubmitField(label="Register")

class TruckUpdateForm(FlaskForm):
    name = StringField(label='Nombre')
    rating = StringField(label='Rating')
    review = StringField(label='Descripcion')
    price = StringField(label='Precio')
    status = StringField(label='Estado')
    img_url = StringField(label='Imagen')
    submit_button = SubmitField(label="Actualizar")

class LoginForm(FlaskForm):
    email = StringField(label='Email')
    password = PasswordField(label='Password')
    submit_button = SubmitField(label="Login")


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
Bootstrap5(app)
loggedin = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///monstertrucks_db.db")
db_monsters.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
with app.app_context():
    db_monsters.create_all()

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return db_monsters.get_or_404(User, user_id)


@app.route('/register', methods=["GET", "POST"])
def register():
    global loggedin, glbl_user
    form = UserForm()
    error = None
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_secure = generate_password_hash(password=password,method="pbkdf2", salt_length=8)
        confirm = db_monsters.session.execute(db_monsters.select(User).where(User.email == email))
        if len(list(confirm)) == 0:
            new_user = User(
                name=name,
                email=email,
                password=password_secure,
            )
            db_monsters.session.add(new_user)
            try:
                db_monsters.session.commit()
            except exc.IntegrityError:
                flash("Email is already used.")
            login_user(new_user)
            loggedin = True
            print(current_user.name)
            return redirect(url_for('home'))
        else:
            flash("Email is already used.")
    return render_template("register.html", form=form, loggedin=loggedin, user=current_user)

@app.route('/login', methods=["GET", "POST"])
def login():
    global loggedin, glbl_user
    form = LoginForm()
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        # Find user by email entered.
        result = db_monsters.session.execute(db_monsters.select(User).where(User.email == email))
        user = result.scalar()
        # Check stored password hash against entered password hashed.
        if user is not None:
            if check_password_hash(user.password, password):
                 login_user(user)
                 flash('Logged in successfully.')
                 loggedin = True
                 glbl_user = user.name
                 #time.sleep(3000)
                 return redirect(url_for('home'))
            else:
                 flash('Password is wrong.')
                 loggedin = False
        else:
             flash(f'There is no user {email}, need to register.')
    return render_template("login.html", form=form, loggedin=loggedin, user=current_user)


@app.route("/")
def home():
    with app.app_context():
        result = db_monsters.session.execute(db_monsters.select(MonsterTrucks).order_by(MonsterTrucks.name))
        all_trucks = result.scalars().all()
    return render_template("index.html", trucks=all_trucks, user=current_user, dia=datetime.datetime.now().strftime("%B, %Y"))


@app.route("/add", methods=["GET", "POST"])
@admin_only
def add():

    form = TruckAddForm()
    if request.method == "POST":
        new_truck = MonsterTrucks(
            name=form.name.data,
            img_url=form.img_url.data,
            status=form.status.data,
            rating=form.rating.data,
            price=form.price.data,
            review=form.review.data,
        )

        db_monsters.session.add(new_truck)
        try:
            db_monsters.session.commit()
        except sqlalchemy.exc.IntegrityError:
            print("Record ya existe con ese name")
        return redirect(url_for('home'))

    return render_template("add.html", form=form)

@app.route("/edit", methods=["GET", "POST"])
@admin_only
def edit():
    form = TruckUpdateForm()
    truck_id = request.args.get('truck_id')
    data_to_update = db_monsters.get_or_404(MonsterTrucks, truck_id)
    form["name"].data = data_to_update.name
    form["rating"].data = data_to_update.rating
    form["review"].data = data_to_update.review
    form["price"].data = data_to_update.price
    form["img_url"].data = data_to_update.img_url
    form["status"].data = data_to_update.status


    if request.method == "POST":
        truck_to_update = db_monsters.get_or_404(MonsterTrucks, truck_id)
        truck_to_update.name = request.form["name"]
        truck_to_update.rating = request.form["rating"]
        truck_to_update.review = request.form["review"]
        truck_to_update.price = request.form["price"]
        truck_to_update.img_url = request.form["img_url"]
        truck_to_update.status = request.form["status"]
        db_monsters.session.commit()
        return redirect(url_for('home'))

    truck_selected = db_monsters.get_or_404(MonsterTrucks, truck_id)
    return render_template("edit.html", form=form, truck=truck_selected)

# @app.route("/delete", methods=["GET", "POST"])
# def delete():
#     truck_id = request.args.get('truck_id')
#     truck_to_delete = db_monsters.get_or_404(MonsterTrucks, truck_id)
#     db_monsters.session.delete(truck_to_delete)
#     db_monsters.session.commit()
#     return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)