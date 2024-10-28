from flask import render_template, request, redirect, url_for, flash
from flemo import app, db, bcrypt
from flemo.forms import RegistrationForm, LoginForm, TaskForm
from flemo.models import User, Task, Note
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html')


@app.route("/home")
def home():
    return render_template('home.html', title='Home')


@app.route("/tasks")
@login_required
def tasks():
    form = TaskForm()
    # Query to get all tasks for the current user
    task_list = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', task_list=task_list, form=form)


@app.route("/gallery")
@login_required
def gallery():
    return render_template('gallery.html')


@app.route("/add-task", methods=['POST'])
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        new_task = Task(title=form.task.data, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
    else:
        flash("Failed to add task. Please try again.", "danger")

    return redirect(url_for('tasks'))


@app.route('/update-tasks', methods=['POST'])
def update_tasks():
    if 'remove_task' in request.form:
        # Task removal request
        task_id = int(request.form['remove_task'])
        task = Task.query.get_or_404(task_id)

        # Ensure the task belongs to the current user
        if task.user_id == current_user.id:
            db.session.delete(task)
            db.session.commit()
        else:
            flash("You don't have permission to delete this task.", "danger")
    else:
        # Update task completion statuses
        tasks_db = Task.query.filter_by(user_id=current_user.id).all()
        updated = False  # Track if any update was made
        for task in tasks_db:
            checkbox_name = f'task_done_{task.id}'
            # Check if this task's checkbox is checked in the form data
            new_status = checkbox_name in request.form
            if task.done != new_status:  # Update only if there's a change
                task.done = new_status
                updated = True

        # Commit only if there was an actual change
        if updated:
            db.session.commit()
        else:
            flash("No changes detected in task statuses.", 'info')

    return redirect(url_for('tasks'))


@app.route("/notes")
@login_required
def notes():
    return render_template('notes.html')


@app.route("/files")
@login_required
def files():
    return render_template('files.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful!', 'danger')

    return render_template('login.html', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))
