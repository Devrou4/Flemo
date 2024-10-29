from flask import render_template, request, redirect, url_for, flash
from flemo import app, db, bcrypt
from flemo.forms import RegistrationForm, LoginForm, TaskForm, UpdateAccount, NoteField
from flemo.models import User, Task, Note
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html')


@app.route("/home")
@login_required
def home():
    return render_template('home.html', title='Home')


@app.route("/tasks")
@login_required
def tasks():
    form = TaskForm()
    # Query to get all tasks for the current user
    task_list = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', task_list=task_list, form=form, title='Tasks')


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
    form = NoteField()
    notes_list = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('notes.html', notes=notes_list, form=form, title='Tasks')


@app.route("/note/<int:note_id>", methods=["GET", "POST"])
@login_required
def note(note_id):
    form = NoteField()
    note_obj = Note.query.get_or_404(note_id)
    notes_list = Note.query.filter_by(user_id=current_user.id).all()
    if request.method == "POST":
        if form.validate_on_submit():
            note_obj.title = form.title.data
            note_obj.content = form.content.data
            db.session.commit()
            return redirect(url_for("note", note_id=note_obj.id, title=note_obj.title))
        else:
            flash("Failed to update note. Please try again.", "danger")
    elif request.method == "GET":
        form.title.data = note_obj.title
        form.content.data = note_obj.content
    return render_template('note.html', form=form, notes=notes_list, note_id=note_id, title=note_obj.title)


@app.route("/add-note", methods=['POST'])
def add_note():
    form = NoteField()
    if form.validate_on_submit():
        new_note = Note(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
    else:
        flash("Failed to add note. Please try again.", "danger")

    return redirect(url_for('notes'))


@app.route("/del-note", methods=['POST'])
@login_required
def del_note():
    if 'delete_note' in request.form:
        note_id = int(request.form['delete_note'])
        note_obj = Note.query.get_or_404(note_id)

        if note_obj.user_id == current_user.id:
            db.session.delete(note_obj)
            db.session.commit()
        else:
            flash("You don't have permission to delete this note.", "danger")
    return redirect(url_for('notes'))


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


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccount()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('account.html', form=form, title='Account')
