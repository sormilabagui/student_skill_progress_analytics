from flask import Blueprint, render_template, request, redirect, url_for
from .models import SkillCategory, Skill, UserSkill
from .extensions import db
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

@main.route("/")
def home():
    return render_template("login.html")




@main.route("/admin_dashboard")
@login_required
def admin_dashboard():
    return render_template("admin_dashboard.html", user=current_user)


@main.route("/user_dashboard")
@login_required
def user_dashboard():
    return render_template("user_dashboard.html", user=current_user)


@main.route("/admin/add-category", methods=["GET", "POST"])
def add_category():

    if request.method == "POST":

        name = request.form.get("name")
        description = request.form.get("description")

        new_category = SkillCategory(
            name=name,
            description=description
        )

        db.session.add(new_category)
        db.session.commit()

        return redirect(url_for("main.admin_dashboard"))

    return render_template("add_category.html")


@main.route("/admin/add-skill", methods=["GET", "POST"])
def add_skill():

    categories = SkillCategory.query.all()

    if request.method == "POST":

        skill_name = request.form.get("skill_name")
        category_id = request.form.get("category_id")
        weight = request.form.get("weight")

        new_skill = Skill(
            skill_name=skill_name,
            category_id=category_id,
            weight=weight
        )

        db.session.add(new_skill)
        db.session.commit()

        return redirect(url_for("main.admin_dashboard"))

    return render_template("add_skill.html", categories=categories)

@main.route("/setup-skills", methods=["GET", "POST"])
@login_required
def skill_setup():

    categories = SkillCategory.query.all()

    if request.method == "POST":

        selected_skills = request.form.getlist("skills")

        for skill_id in selected_skills:
            new_skill = UserSkill(
                user_id=current_user.id,
                skill_id=skill_id
            )

            db.session.add(new_skill)

        db.session.commit()

        return redirect(url_for("main.user_dashboard"))

    return render_template("setup_skills.html", categories=categories)