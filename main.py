import sqlalchemy.exc
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy.future import select
from sqlalchemy.sql import func
import requests
import os
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


class TruckAddForm(FlaskForm):
    name = StringField(label='Nombre')
    rating = StringField(label='Rating')
    review = StringField(label='Descripcion')
    price = StringField(label='Precio')
    status = StringField(label='Estado')
    img_url = StringField(label='Imagen')
    submit_button = SubmitField(label="Agregar")

class TruckUpdateForm(FlaskForm):
    name = StringField(label='Nombre')
    rating = StringField(label='Rating')
    review = StringField(label='Descripcion')
    price = StringField(label='Precio')
    status = StringField(label='Estado')
    img_url = StringField(label='Imagen')
    submit_button = SubmitField(label="Actualizar")
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///monstertrucks_db.db")
db_monsters.init_app(app)
with app.app_context():
    db_monsters.create_all()

@app.route("/")
def home():
    with app.app_context():
        result = db_monsters.session.execute(db_monsters.select(MonsterTrucks).order_by(MonsterTrucks.name))
        all_trucks = result.scalars().all()
    return render_template("index.html", trucks=all_trucks)


@app.route("/add", methods=["GET", "POST"])
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