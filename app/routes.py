from flask import Blueprint, render_template, request, redirect, url_for
from .models import SkillCategory, Skill, UserSkill, Goal
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


@main.route("/user-dashboard")
@login_required
def user_dashboard():

    # Skills selected by user
    user_skills = current_user.user_skills

    # Active goals
    goals = Goal.query.filter_by(user_id=current_user.id, status="active").all()

    # Data for charts
    skill_names = []
    target_hours = []
    skill_labels = [us.skill.skill_name for us in user_skills]
    skill_progress = [0 for _ in user_skills]

    for g in goals:
        skill_names.append(g.skill.skill_name)
        target_hours.append(g.target_hours_per_week)

    return render_template(
        "user_dashboard.html",
        user=current_user,
        user_skills=user_skills,
        goals=goals,
        skill_names=skill_names,
        target_hours=target_hours,
        skill_labels=skill_labels,
        skill_progress=skill_progress
    )

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

            hours = request.form.get(f"hours_{skill_id}")

            new_skill = UserSkill(
                user_id=current_user.id,
                skill_id=skill_id
            )

            db.session.add(new_skill)

            goal = Goal(
                user_id=current_user.id,
                skill_id=skill_id,
                target_hours_per_week=hours
            )

            db.session.add(goal)

        db.session.commit()

        return redirect(url_for("main.user_dashboard"))

    return render_template("setup_skills.html", categories=categories)