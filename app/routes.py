from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .models import SkillCategory, Skill, UserSkill, Goal, Progress
from .extensions import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date

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
    goals = Goal.query.filter_by(
        user_id=current_user.id,
        status="active"
    ).all()

    # Chart Data
    skill_labels = []
    skill_progress = []
    skill_names = []
    target_hours = []

    # Analytics Data
    weak_skills = []
    strong_skills = []
    recommendations = []
    goal_progress = {}

    #priority analysis
    high_priority = []
    medium_priority = []
    low_priority = []

    total_progress = 0
    skill_count = 0

    category_data = {}

    for us in user_skills:

        skill_name = us.skill.skill_name
        weight = us.skill.weight
        category = us.skill.category.name

        if weight >= 7:
            high_priority.append(skill_name)

        elif weight >= 5:
            medium_priority.append(skill_name)

        else:
            low_priority.append(skill_name)

        goal = Goal.query.filter_by(
            user_id=current_user.id,
            skill_id=us.skill_id,
            status="active"
        ).first()

        if goal:

            target = goal.target_hours_per_week

            # Get last 7 days progress
            week_ago = datetime.utcnow() - timedelta(days=7)

            progress_entries = Progress.query.filter(
                Progress.user_id == current_user.id,
                Progress.skill_id == us.skill_id,
                Progress.date >= week_ago
            ).all()

            actual = sum(p.hours_spent for p in progress_entries)

            progress = (actual / target) * 100 if target else 0
            goal_progress[skill_name] = round(progress, 2)

            total_progress += progress
            skill_count += 1

            if category in category_data:
                category_data[category] += progress
            else:
                category_data[category] = progress

            skill_names.append(skill_name)
            target_hours.append(target)

            # Weakness detection
            if progress == 0:
                weak_skills.append(skill_name)
                recommendations.append(f"Start working on {skill_name}")

            elif progress < 50:
                weak_skills.append(skill_name)
                recommendations.append(f"Increase time for {skill_name}")

            else:
                strong_skills.append(skill_name)

        else:
            progress = 0

        skill_labels.append(skill_name)
        skill_progress.append(progress)
    
    overall_performance = round(total_progress / skill_count, 2) if skill_count else 0
    category_labels = list(category_data.keys())
    category_values = list(category_data.values())


    return render_template(
        "user_dashboard.html",
        user=current_user,
        user_skills=user_skills,
        goals=goals,
        goal_progress=goal_progress,
        skill_names=skill_names,
        target_hours=target_hours,
        skill_labels=skill_labels,
        skill_progress=skill_progress,
        weak_skills=weak_skills,
        strong_skills=strong_skills,
        recommendations=recommendations,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority,
        overall_performance=overall_performance,
        category_labels=category_labels,
        category_values=category_values,
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

@main.route("/add-progress", methods=["GET", "POST"])
@login_required
def add_progress():

    user_skills = current_user.user_skills

    if request.method == "POST":

        skill_id = request.form.get("skill_id")
        hours = float(request.form.get("hours"))

        progress = Progress(
            user_id=current_user.id,
            skill_id=skill_id,
            hours_spent=hours
        )

        db.session.add(progress)
        db.session.commit()

        return redirect(url_for("main.user_dashboard"))

    return render_template("add_progress.html", user_skills=user_skills)


@main.route("/timer-progress", methods=["POST"])
@login_required
def timer_progress():

    data = request.get_json()

    skill_id = data.get("skill_id")
    hours = data.get("hours")

    progress = Progress(
        user_id=current_user.id,
        skill_id=skill_id,
        hours_spent=hours
    )

    db.session.add(progress)
    db.session.commit()

    return {"status": "success"}