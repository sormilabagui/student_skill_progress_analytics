from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file, flash, session
from .models import SkillCategory, Skill, UserSkill, Goal, Progress, User, StudyResource
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

    skills = Skill.query.filter_by(category_id=id).all()

    for skill in skills:
        UserSkill.query.filter_by(skill_id=skill.id).delete()
        Goal.query.filter_by(skill_id=skill.id).delete()
        Progress.query.filter_by(skill_id=skill.id).delete()

    Skill.query.filter_by(category_id=id).delete()

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

    UserSkill.query.filter_by(skill_id=id).delete()
    Goal.query.filter_by(skill_id=id).delete()
    Progress.query.filter_by(skill_id=id).delete()

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

@main.route("/admin/resources", methods=["GET","POST"])
@login_required
def admin_resources():

    if current_user.role != "admin":
        return redirect(url_for("main.user_dashboard"))

    skills = Skill.query.all()

    if request.method == "POST":

        skill_id = request.form.get("skill_id")
        title = request.form.get("title")
        url = request.form.get("url")
        platform = request.form.get("platform")

        resource = StudyResource(
            skill_id=skill_id,
            title=title,
            url=url,
            platform=platform
        )

        db.session.add(resource)
        db.session.commit()

        return redirect(url_for("main.admin_resources"))

    resources = StudyResource.query.all()

    return render_template(
        "admin_resources.html",
        skills=skills,
        resources=resources
    )


#user side backend
@main.route("/user-dashboard")
@login_required
def user_dashboard():
    

    # Skills selected by user
    user_skills = UserSkill.query.join(Skill).filter(
    UserSkill.user_id == current_user.id,
    UserSkill.is_active == True
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

        if not us.skill:
            continue

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


@main.route('/analytics')
@login_required
def analytics():

    user_id = current_user.id

    user_skills = UserSkill.query.filter_by(user_id=user_id).all()
    goals = Goal.query.filter_by(user_id=user_id).all()
    progress = Progress.query.filter_by(user_id=user_id).all()


    # Weekly Target Chart

    skill_names = []
    target_hours = []

    for g in goals:
        if g.skill:   # ← Fix added
            skill_names.append(g.skill.skill_name)
            target_hours.append(g.target_hours_per_week)


    # Skill Progress

    skill_labels = []
    skill_progress = []

    for g in goals:
        if g.skill:   # ← Fix added
            skill_labels.append(g.skill.skill_name)
            skill_progress.append(50)


    # Category Performance

    category_dict = {}

    for p in progress:
        if p.skill and p.skill.category:   # ← Fix added

            category = p.skill.category.name

            if category not in category_dict:
                category_dict[category] = 0

            category_dict[category] += p.hours_spent


    category_labels = list(category_dict.keys())
    category_values = list(category_dict.values())


    return render_template(
        'analytics.html',
        skill_names=skill_names,
        target_hours=target_hours,
        skill_labels=skill_labels,
        skill_progress=skill_progress,
        category_labels=category_labels,
        category_values=category_values
    )

@main.route('/goals_progress')
@login_required
def goals_progress():

    user_id = current_user.id

    goals = Goal.query.filter_by(user_id=user_id).all()
    progress = Progress.query.filter_by(user_id=user_id).all()


    # Calculate hours spent per skill

    skill_hours = {}

    for p in progress:
        if p.skill:
            name = p.skill.skill_name

            if name not in skill_hours:
                skill_hours[name] = 0

            skill_hours[name] += p.hours_spent


    # Goal Progress

    goal_progress = {}

    weak_skills = []
    strong_skills = []

    recommendations = []

    high_priority = []
    medium_priority = []
    low_priority = []


    for g in goals:

        if not g.skill:
            continue

        skill_name = g.skill.skill_name

        target = g.target_hours_per_week

        actual = skill_hours.get(skill_name, 0)

        progress_percent = 0

        if target > 0:
            progress_percent = (actual / target) * 100

        goal_progress[skill_name] = round(progress_percent,2)


        # Weak / Strong Logic

        if progress_percent < 40:
            weak_skills.append(skill_name)
            recommendations.append(
                f"Increase time for {skill_name}"
            )

        elif progress_percent > 75:
            strong_skills.append(skill_name)


        # Priority from Database

        if g.priority == "High":
            high_priority.append(skill_name)

        elif g.priority == "Medium":
            medium_priority.append(skill_name)

        else:
            low_priority.append(skill_name)



    return render_template(
        'goals_progress.html',
        goals=goals,
        goal_progress=goal_progress,
        weak_skills=weak_skills,
        strong_skills=strong_skills,
        recommendations=recommendations,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority
    )

from datetime import datetime, timedelta


@main.route('/productivity')
@login_required
def productivity():

    user_id = current_user.id

    user_skills = UserSkill.query.join(Skill).filter(
        UserSkill.user_id == user_id,
        UserSkill.is_active == True
    ).all()

    goal_progress = {}
    high_priority = []

    total_progress = 0
    skill_count = 0

    # Calculate Goal Progress

    for us in user_skills:

        if not us.skill:
            continue

        skill_name = us.skill.skill_name
        weight = us.skill.weight

        if weight >= 7:
            high_priority.append(skill_name)

        goal = Goal.query.filter_by(
            user_id=user_id,
            skill_id=us.skill_id,
            status="active"
        ).first()

        if goal:

            target = goal.target_hours_per_week

            week_ago = datetime.utcnow() - timedelta(days=7)

            progress_entries = Progress.query.filter(
                Progress.user_id == user_id,
                Progress.skill_id == us.skill_id,
                Progress.date >= week_ago
            ).all()

            actual = sum(p.hours_spent for p in progress_entries)

            progress = (actual / target) * 100 if target else 0

            goal_progress[skill_name] = round(progress,2)

            total_progress += progress
            skill_count += 1


    overall_performance = round(total_progress / skill_count, 2) if skill_count else 0


    # Streak Calculation

    progress_dates = db.session.query(
        Progress.date
    ).filter(
        Progress.user_id == user_id
    ).order_by(
        Progress.date.desc()
    ).all()

    unique_days = []

    for p in progress_dates:
        day = p.date.date()
        if day not in unique_days:
            unique_days.append(day)

    streak = 0
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


    # Productivity Score

    goal_score = overall_performance * 0.4

    consistency_score = min(streak * 10, 100) * 0.3


    priority_total = 0
    priority_count = 0

    for skill in high_priority:

        if skill in goal_progress:
            priority_total += goal_progress[skill]
            priority_count += 1


    priority_score = (priority_total / priority_count) if priority_count else 0
    priority_score = priority_score * 0.3


    productivity_score = round(
        goal_score + consistency_score + priority_score,
        2
    )


    # Total Hours

    total_hours = db.session.query(
        db.func.sum(Progress.hours_spent)
    ).filter(
        Progress.user_id == user_id
    ).scalar() or 0


    # Weekly Hours

    week_ago = datetime.utcnow() - timedelta(days=7)

    weekly_hours = db.session.query(
        db.func.sum(Progress.hours_spent)
    ).filter(
        Progress.user_id == user_id,
        Progress.date >= week_ago
    ).scalar() or 0


    # Top Skill

    skill_hours = {}

    progress = Progress.query.filter_by(
        user_id=user_id
    ).all()

    for p in progress:
        if p.skill:
            skill_name = p.skill.skill_name

            if skill_name not in skill_hours:
                skill_hours[skill_name] = 0

            skill_hours[skill_name] += p.hours_spent


    top_skill = max(skill_hours, key=skill_hours.get) if skill_hours else "None"


    suggestions = []

    if productivity_score < 30:
        suggestions.append("Low productivity — focus on consistency")

    elif productivity_score < 60:
        suggestions.append("Moderate productivity — improve goal completion")

    else:
        suggestions.append("Excellent productivity — maintain momentum")


    return render_template(
        'productivity.html',
        total_hours=round(total_hours,2),
        weekly_hours=round(weekly_hours,2),
        top_skill=top_skill,
        productivity_score=productivity_score,
        suggestions=suggestions
    )

@main.route('/reports')
@login_required
def reports():

    user_id = current_user.id

    user_skills = UserSkill.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()

    weak_skills = []
    strong_skills = []
    recommendations = []

    goal_progress = {}

    total_progress = 0
    skill_count = 0

    for us in user_skills:

        if not us.skill:
            continue

        skill_name = us.skill.skill_name

        goal = Goal.query.filter_by(
            user_id=user_id,
            skill_id=us.skill_id,
            status="active"
        ).first()

        if goal:

            week_ago = datetime.utcnow() - timedelta(days=7)

            progress_entries = Progress.query.filter(
                Progress.user_id == user_id,
                Progress.skill_id == us.skill_id,
                Progress.date >= week_ago
            ).all()

            actual = sum(p.hours_spent for p in progress_entries)

            target = goal.target_hours_per_week

            progress = (actual / target) * 100 if target else 0

            skill_name = us.skill.skill_name

            goal_progress[skill_name] = round(progress,2)

            total_progress += progress
            skill_count += 1

            if progress < 40:
                weak_skills.append(skill_name)
                recommendations.append(
                    f"Increase focus on {skill_name}"
                )
            else:
                strong_skills.append(skill_name)


    overall_performance = round(
        total_progress / skill_count,2
    ) if skill_count else 0


    # Streak

    progress_dates = Progress.query.filter(
        Progress.user_id == user_id
    ).order_by(
        Progress.date.desc()
    ).all()

    unique_days = []

    for p in progress_dates:
        day = p.date.date()
        if day not in unique_days:
            unique_days.append(day)

    streak = len(unique_days[:5])  # simplified

    # Productivity Score (Same as productivity page)

    goal_score = overall_performance * 0.4

    consistency_score = min(streak * 10, 100) * 0.3

    # Priority Score

    high_priority = []

    for us in user_skills:
        if us.skill and us.skill.weight >= 7:
            high_priority.append(us.skill.skill_name)

    priority_total = 0
    priority_count = 0

    for skill in high_priority:

        if skill in goal_progress:
            priority_total += goal_progress[skill]
            priority_count += 1

    priority_score = (priority_total / priority_count) if priority_count else 0
    priority_score = priority_score * 0.3


    productivity_score = round(
        goal_score + consistency_score + priority_score,
        2
    )

    return render_template(
        "reports.html",
        overall_performance=overall_performance,
        productivity_score=round(productivity_score,2),
        streak=streak,
        strong_skills=strong_skills,
        weak_skills=weak_skills,
        recommendations=recommendations
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
            priority = request.form.get(f"priority_{skill_id}","Medium")

            new_skill = UserSkill(
                user_id=current_user.id,
                skill_id=skill_id
            )

            db.session.add(new_skill)

            goal = Goal(
                user_id=current_user.id,
                skill_id=skill_id,
                target_hours_per_week=hours,
                priority=priority
            )

            db.session.add(goal)

        db.session.commit()

        return redirect(url_for("main.user_dashboard"))

    return render_template(
        "setup_skills.html",
        categories=categories
    )

@main.route("/add-progress", methods=["GET", "POST"])
@login_required
def add_progress():

    user_skills = current_user.user_skills

    if request.method == "POST":

        skill_id = request.form.get("skill_id")
        hours = float(request.form.get("hours"))

        topic = request.form.get("topic")
        study_type = request.form.get("study_type")
        focus_rating = request.form.get("focus_rating")

        date = request.form.get("date")

        if date:
            date = datetime.fromisoformat(date)


        progress = Progress(
            user_id=current_user.id,
            skill_id=skill_id,
            hours_spent=hours,
            topic=topic,
            study_type=study_type,
            focus_rating=focus_rating,
            date=date
        )

        db.session.add(progress)
        db.session.commit()

        return redirect(url_for("main.user_dashboard"))

    return render_template(
        "add_progress.html",
        user_skills=user_skills
    )

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

@main.route("/update-goal/<int:id>", methods=["POST"])
@login_required
def update_goal(id):

    user_skill = UserSkill.query.get(id)

    hours = request.form.get("hours")
    priority = request.form.get("priority")

    goal = Goal.query.filter_by(
        user_id=current_user.id,
        skill_id=user_skill.skill_id
    ).first()

    if goal:
        goal.target_hours_per_week = hours
        goal.priority = priority

    db.session.commit()

    return redirect(
        url_for("main.manage_skills")
    )

@main.route("/download-report")
@login_required
def download_report():

    buffer = io.BytesIO()

    styles = getSampleStyleSheet()
    story = []

    # =============================
    # Calculate Analytics First
    # =============================

    user_id = current_user.id

    user_skills = UserSkill.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()

    weak_skills = []
    strong_skills = []

    goal_progress = {}

    total_progress = 0
    skill_count = 0

    for us in user_skills:

        if not us.skill:
            continue

        goal = Goal.query.filter_by(
            user_id=user_id,
            skill_id=us.skill_id,
            status="active"
        ).first()

        if goal:

            week_ago = datetime.utcnow() - timedelta(days=7)

            progress_entries = Progress.query.filter(
                Progress.user_id == user_id,
                Progress.skill_id == us.skill_id,
                Progress.date >= week_ago
            ).all()

            actual = sum(p.hours_spent for p in progress_entries)
            target = goal.target_hours_per_week

            progress = (actual / target) * 100 if target else 0

            skill_name = us.skill.skill_name

            goal_progress[skill_name] = round(progress, 2)

            total_progress += progress
            skill_count += 1

            if progress < 40:
                weak_skills.append(skill_name)
            else:
                strong_skills.append(skill_name)

    overall_performance = round(
        total_progress / skill_count, 2
    ) if skill_count else 0


    # =============================
    # Streak Calculation
    # =============================

    progress_dates = Progress.query.filter(
        Progress.user_id == user_id
    ).order_by(
        Progress.date.desc()
    ).all()

    unique_days = []

    for p in progress_dates:
        day = p.date.date()
        if day not in unique_days:
            unique_days.append(day)

    streak = len(unique_days[:5])


    # =============================
    # Productivity Score
    # =============================

    goal_score = overall_performance * 0.4
    consistency_score = min(streak * 10, 100) * 0.3

    high_priority = []

    for us in user_skills:
        if us.skill and us.skill.weight >= 7:
            high_priority.append(us.skill.skill_name)

    priority_total = 0
    priority_count = 0

    for skill in high_priority:

        if skill in goal_progress:
            priority_total += goal_progress[skill]
            priority_count += 1

    priority_score = (priority_total / priority_count) if priority_count else 0
    priority_score = priority_score * 0.3

    productivity_score = round(
        goal_score + consistency_score + priority_score,
        2
    )



    # =============================
    # PDF Content Starts
    # =============================

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


    # Performance Summary
    story.append(Paragraph(
        "<b>Performance Summary</b>",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 6))

    story.append(Paragraph(
        f"Overall Performance : {overall_performance}%",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"Productivity Score : {productivity_score}%",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"Study Streak : {streak} Days",
        styles["Normal"]
    ))

    story.append(Spacer(1, 12))


    # Strong Skills
    story.append(Paragraph(
        "<b>Strong Skills</b>",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 6))

    for s in strong_skills:
        story.append(Paragraph(
            f"✓ {s}",
            styles["Normal"]
        ))

    story.append(Spacer(1, 12))


    # Weak Skills
    story.append(Paragraph(
        "<b>Weak Skills</b>",
        styles["Heading2"]
    ))

    story.append(Spacer(1, 6))

    for w in weak_skills:
        story.append(Paragraph(
            f"⚠ {w}",
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

        if r.skill:
            story.append(Paragraph(
                f"{r.skill.skill_name} — {round(r.hours_spent,2)} hrs",
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

@main.route("/study-resources")
@login_required
def study_resources():

    user_skills = current_user.user_skills

    return render_template(
        "study_resources.html",
        user_skills=user_skills
    )

# Start Auto Study
@main.route("/start-auto-study/<int:skill_id>")
@login_required
def start_auto_study(skill_id):

    session["auto_skill"] = skill_id
    session["start_time"] = datetime.now().isoformat()

    return "", 204


# Stop Auto Study
@main.route("/stop-auto-study")
@login_required
def stop_auto_study():

    skill_id = session.get("auto_skill")
    start_time = session.get("start_time")

    if not skill_id or not start_time:
        return "", 204

    start_time = datetime.fromisoformat(start_time)
    end_time = datetime.now()

    time_spent = (end_time - start_time).seconds / 3600

    progress = Progress(
        user_id=current_user.id,
        skill_id=skill_id,
        hours_spent=time_spent
    )

    db.session.add(progress)
    db.session.commit()

    session.pop("auto_skill", None)
    session.pop("start_time", None)

    return "", 204
