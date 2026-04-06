from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file, flash
from .models import SkillCategory, Skill, UserSkill, Goal, Progress, User
from .extensions import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import io

main = Blueprint('main', __name__)

@main.route("/")
def home():
    return render_template("login.html")




@main.route("/admin/dashboard")
@login_required
def admin_dashboard():

    categories = SkillCategory.query.all()
    skills = Skill.query.all()
    users = User.query.all()

    total_users = len(users)
    total_categories = len(categories)
    total_skills = len(skills)

    recent_users = User.query.order_by(User.id.desc()).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        user=current_user,
        total_users=total_users,
        total_categories=total_categories,
        total_skills=total_skills,
        recent_users=recent_users,
        categories=categories,
        skills=skills
    )

#manage category
@main.route("/admin/manage-category", methods=["GET","POST"])
@login_required
def manage_category():

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]

        category = SkillCategory(
            name=name,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        return redirect(url_for("main.manage_category"))

    categories = SkillCategory.query.all()

    return render_template(
        "manage_categories.html",
        categories=categories,
        user=current_user
    )

@main.route("/admin/delete-category/<int:id>")
@login_required
def delete_category(id):

    category = SkillCategory.query.get(id)

    db.session.delete(category)
    db.session.commit()

    return redirect(url_for("main.manage_category"))

@main.route("/admin/edit-category/<int:id>", methods=["GET","POST"])
@login_required
def edit_category(id):

    category = SkillCategory.query.get(id)

    if request.method == "POST":

        category.name = request.form["name"]
        category.description = request.form["description"]

        db.session.commit()

        return redirect(url_for("main.manage_category"))

    return render_template(
        "edit_category.html",
        category=category
    )

@main.route("/admin/manage-skill", methods=["GET","POST"])
@login_required
def manage_skill():

    if request.method == "POST":

        skill_name = request.form["skill_name"]
        category_id = request.form["category_id"]
        weight = request.form["weight"]

        skill = Skill(
            skill_name=skill_name,
            category_id=category_id,
            weight=weight
        )

        db.session.add(skill)
        db.session.commit()

        return redirect(url_for("main.manage_skill"))

    skills = Skill.query.all()
    categories = SkillCategory.query.all()

    return render_template(
        "manage_admin_skills.html",
        skills=skills,
        categories=categories,
        user=current_user
    )

@main.route("/admin/delete-skill/<int:id>")
@login_required
def delete_skill(id):

    skill = Skill.query.get(id)

    db.session.delete(skill)
    db.session.commit()

    return redirect(url_for("main.manage_skill"))

@main.route("/admin/edit-skill/<int:id>", methods=["GET","POST"])
@login_required
def edit_skill(id):

    skill = Skill.query.get(id)
    categories = SkillCategory.query.all()

    if request.method == "POST":

        skill.skill_name = request.form["skill_name"]
        skill.category_id = request.form["category_id"]
        skill.weight = request.form["weight"]

        db.session.commit()

        return redirect(url_for("main.manage_skill"))

    return render_template(
        "edit_skill.html",
        skill=skill,
        categories=categories
    )

@main.route("/admin/users")
@login_required
def admin_users():

    users = User.query.all()

    return render_template(
        "admin_users.html",
        users=users,
        user=current_user
    )

@main.route("/admin/user/<int:id>")
@login_required
def admin_user_detail(id):

    user = User.query.get(id)

    user_skills = UserSkill.query.filter_by(
        user_id=id
    ).all()

    progress = Progress.query.filter_by(
        user_id=id
    ).order_by(Progress.id.desc()).limit(10).all()

    total_hours = db.session.query(
        db.func.sum(Progress.hours_spent)
    ).filter_by(user_id=id).scalar() or 0

    return render_template(
        "admin_user_detail.html",
        user=user,
        user_skills=user_skills,
        progress=progress,
        total_hours=round(total_hours,2)
    )

@main.route("/admin/profile", methods=["GET","POST"])
@login_required
def admin_profile():

    user = current_user

    if request.method == "POST":

        user.name = request.form.get("name")
        user.email = request.form.get("email")

        db.session.commit()

        flash("Profile Updated Successfully")

    return render_template(
        "admin_profile.html",
        user=user
    )


#user side backend
@main.route("/user-dashboard")
@login_required
def user_dashboard():
    

    # Skills selected by user
    user_skills = UserSkill.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()

    # Active goals
    goals = Goal.query.filter(
        Goal.user_id == current_user.id,
        Goal.status == "active",
        Goal.skill_id.in_(
            db.session.query(UserSkill.skill_id).filter(
                UserSkill.user_id == current_user.id,
                UserSkill.is_active == True
            )
        )
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

    # Daily Streak Calculation

    progress_dates = db.session.query(
        Progress.date
    ).filter(
        Progress.user_id == current_user.id
    ).order_by(Progress.date.desc()).all()

    unique_days = []

    for p in progress_dates:
        day = p.date.date()
        if day not in unique_days:
            unique_days.append(day)

    streak = 0
    longest_streak = 0
    temp_streak = 0

    today = date.today()

    for i, day in enumerate(unique_days):

        if i == 0:
            if day == today or day == today - timedelta(days=1):
                streak = 1
                temp_streak = 1
            else:
                break

        else:
            if unique_days[i-1] - day == timedelta(days=1):
                temp_streak += 1
            else:
                break

        longest_streak = max(longest_streak, temp_streak)

    last_active = unique_days[0] if unique_days else None

    # Productivity Score

    # Goal Score (40%)
    goal_score = overall_performance * 0.4


    # Consistency Score (30%)
    consistency_score = min(streak * 10, 100) * 0.3


    # Priority Score (30%)
    priority_total = 0
    priority_count = 0

    for skill in high_priority:

        if skill in goal_progress:
            priority_total += goal_progress[skill]
            priority_count += 1

    priority_score = (priority_total / priority_count) if priority_count else 0
    priority_score = priority_score * 0.3


    productivity_score = round(
        goal_score + consistency_score + priority_score, 2
    )

    # Recent Activity

    recent_activity = Progress.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Progress.date.desc()
    ).limit(5).all()

    # Smart Recommendations

    smart_recommendations = []

    today = datetime.utcnow().date()

    for us in user_skills:

        last_progress = Progress.query.filter(
            Progress.user_id == current_user.id,
            Progress.skill_id == us.skill_id
        ).order_by(
            Progress.date.desc()
        ).first()

        if last_progress:

            last_date = last_progress.date.date()
            gap = (today - last_date).days

            if gap >= 2:
                smart_recommendations.append(
                    f"You haven't practiced {us.skill.skill_name} for {gap} days"
                )

        else:
            smart_recommendations.append(
                f"Start working on {us.skill.skill_name}"
            )

    # Goal Based Smart Recommendations

    for skill, progress in goal_progress.items():

        if progress >= 80 and progress < 100:
            smart_recommendations.append(
                f"You're close to completing {skill} goal"
            )

        elif progress == 0:
            smart_recommendations.append(
                f"Start your weekly goal for {skill}"
            )

    if len(high_priority) > 0:
        smart_recommendations.append(
            "Focus on High Priority Skills first"
        )    

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
        streak=streak,
        longest_streak=longest_streak,
        last_active=last_active,
        productivity_score=productivity_score,
        recent_activity=recent_activity,
        smart_recommendations=smart_recommendations,
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

#skills management
@main.route("/skills")
@login_required
def manage_skills():

    user_skills = current_user.user_skills

    return render_template(
        "manage_skills.html",
        user_skills=user_skills
    )

@main.route("/toggle-skill/<int:id>")
@login_required
def toggle_skill(id):

    skill = UserSkill.query.get(id)

    skill.is_active = not skill.is_active

    goal = Goal.query.filter_by(
        user_id=current_user.id,
        skill_id=skill.skill_id
    ).first()

    if goal:
        goal.status = "active" if skill.is_active else "inactive"

    db.session.commit()

    return redirect(url_for("main.manage_skills"))


@main.route("/download-report")
@login_required
def download_report():

    buffer = io.BytesIO()

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(
        "<b>Student Skill Progress Report</b>",
        styles["Heading1"]
    ))

    story.append(Spacer(1, 12))

    # User Info
    story.append(Paragraph(
        f"User : {current_user.name}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"Date : {datetime.utcnow().strftime('%d %B %Y')}",
        styles["Normal"]
    ))

    story.append(Spacer(1, 12))

    # Performance Section
    story.append(Paragraph(
        "<b>Performance Summary</b>",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 6))

    story.append(Paragraph(
        f"Overall Performance : {request.args.get('overall', '0')}%",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"Productivity Score : {request.args.get('productivity', '0')}%",
        styles["Normal"]
    ))

    story.append(Spacer(1, 12))


    # Skills Progress
    story.append(Paragraph(
        "<b>Skill Progress</b>",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 6))

    user_skills = current_user.user_skills

    for us in user_skills:

        story.append(Paragraph(
            f"{us.skill.skill_name}",
            styles["Normal"]
        ))

    story.append(Spacer(1, 12))


    # Recent Activity
    story.append(Paragraph(
        "<b>Recent Activity</b>",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 6))

    recent = Progress.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Progress.date.desc()
    ).limit(5).all()

    for r in recent:

        story.append(Paragraph(
            f"{r.skill.skill_name} — {round(r.hours_spent*60)} mins",
            styles["Normal"]
        ))

    story.append(Spacer(1, 12))


    # Footer
    story.append(Paragraph(
        "Generated by Student Skill Progress Analytics System",
        styles["Italic"]
    ))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Skill_Report.pdf",
        mimetype="application/pdf"
    )

@main.route("/pomodoro")
@login_required
def pomodoro():

    user_skills = UserSkill.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()

    return render_template(
        "pomodoro.html",
        user_skills=user_skills
    )

@main.route("/save-pomodoro", methods=["POST"])
@login_required
def save_pomodoro():

    data = request.get_json()

    skill_id = data.get("skill_id")
    minutes = data.get("minutes")

    hours = minutes / 60

    progress = Progress(
        user_id=current_user.id,
        skill_id=skill_id,
        hours_spent=hours
    )

    db.session.add(progress)
    db.session.commit()

    return jsonify({"status":"success"})