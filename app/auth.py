from flask import Blueprint, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db
from flask import request, redirect, url_for
from flask_login import login_user, logout_user

auth = Blueprint('auth', __name__)


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already exists"
        
        hashed_pwd = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_pwd
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            return "No user found"
        
        if not check_password_hash(user.password_hash, password):
            return "Wrong password"
        
        login_user(user)
        return redirect(url_for("main.dashboard"))
    

    return render_template("login.html")

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))