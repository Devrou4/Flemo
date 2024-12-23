from flask import render_template, request, redirect, url_for, flash
from flemo import app, db, bcrypt, mail
from flemo.forms import RegistrationForm, LoginForm, TaskForm, UpdateAccount, NoteField, RequestResetForm, \
    ResetPasswordForm, PhotoForm, NoteFolderForm, ChangeFolderForm
from flemo.models import User, Task, Note, Photo, NoteFolder
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from werkzeug.utils import secure_filename
import os
import markdown


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
    task_list = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', task_list=task_list, form=form, title='Tasks')


@app.route("/gallery", methods=['GET', 'POST'])
@login_required
def gallery():
    form = PhotoForm()

    if form.validate_on_submit():
        file = form.file.data
        if file:
            try:
                # Create a user-specific directory
                base_directory = os.path.abspath(os.path.dirname(__file__))
                user_directory = os.path.join(base_directory, 'static', 'user_data', str(current_user.id))
                os.makedirs(user_directory, exist_ok=True)  # Create the directory if it doesn't exist

                filename = secure_filename(file.filename)
                filepath = os.path.join(user_directory, filename)  # Save the file in the user's directory
                print(f"Saving file to: {filepath}")  # Debugging print
                file.save(filepath)

                # Create a new photo record in the database
                new_photo = Photo(title=filename, path=filepath, user_id=current_user.id)
                db.session.add(new_photo)
                db.session.commit()

                return redirect(url_for('gallery'))
            except Exception as e:
                print(f"Failed to save file: {e}")  # Log the error
                flash("Failed to upload the file. Please try again.", "danger")

    photo_list = Photo.query.filter_by(user_id=current_user.id).all()
    return render_template('gallery.html', photos=photo_list, form=form)


@app.route("/del-photo/<int:photo_id>", methods=['POST'])
@login_required
def del_photo(photo_id):
    photo = Photo.query.filter_by(id=photo_id).first()
    if photo:
        os.remove(photo.path)
        db.session.delete(photo)
        db.session.commit()
        return redirect(url_for('gallery'))


@app.route("/add-task", methods=['POST'])
@login_required
def add_task():
    form = TaskForm()
    edit_task_id = request.form.get("edit_task_id")

    if form.validate_on_submit():
        if edit_task_id:
            task = Task.query.get_or_404(int(edit_task_id))
            if task.user_id == current_user.id:
                task.title = form.task.data
                db.session.commit()

            else:
                flash("You don't have permission to edit this task.", "danger")
        else:
            new_task = Task(title=form.task.data, user_id=current_user.id)
            db.session.add(new_task)
            db.session.commit()

    else:
        flash("Failed to add task. Please try again.", "danger")

    return redirect(url_for('tasks'))


@app.route('/update-tasks', methods=['POST', 'GET'])
@login_required
def update_tasks():
    form = TaskForm()

    if 'remove_task' in request.form:
        task_id = int(request.form['remove_task'])
        task = Task.query.get_or_404(task_id)
        if task.user_id == current_user.id:
            db.session.delete(task)
            db.session.commit()
        else:
            flash("You don't have permission to delete this task.", "danger")

    elif 'edit_task' in request.form:
        task_id = int(request.form['edit_task'])
        task = Task.query.get_or_404(task_id)
        if task.user_id == current_user.id:
            return render_template(
                'tasks.html',
                task_list=Task.query.filter_by(user_id=current_user.id).all(),
                form=form,
                edit_task_id=task_id,
                task_title=task.title,
                title='Tasks'
            )
        else:
            flash("You don't have permission to edit this task.", "danger")

    else:
        tasks_db = Task.query.filter_by(user_id=current_user.id).all()
        updated = False
        for task in tasks_db:
            checkbox_name = f'task_done_{task.id}'
            new_status = checkbox_name in request.form
            if task.done != new_status:
                task.done = new_status
                updated = True

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
    folders = NoteFolder.query.filter_by(user_id=current_user.id).order_by(NoteFolder.title).all()
    folder_form = NoteFolderForm()
    if not NoteFolder.query.get(1):
        default_folder = NoteFolder(id=1, title='Uncategorized', user_id=current_user.id)
        db.session.add(default_folder)
        db.session.commit()
        return redirect(url_for('notes'))

    return render_template('notes.html', notes=notes_list, form=form, title='Notes', folders=folders, folder_form=folder_form)


@app.route("/notes/<int:note_id>", methods=["GET", "POST"])
@login_required
def note(note_id):
    form = NoteField()
    folder_form = NoteFolderForm()
    note_obj = Note.query.get_or_404(note_id)
    notes_list = Note.query.filter_by(user_id=current_user.id).all()
    layout = request.args.get('layout', '1')
    folders = NoteFolder.query.filter_by(user_id=current_user.id).order_by(NoteFolder.title).all()
    open_folders = request.args.get('open_folders', '').split(',')

    change_folder_form = ChangeFolderForm()
    choices = []
    for folder in folders:
        choices.append((folder.id, folder.title))
    change_folder_form.selected_folder.choices = choices

    if request.method == "POST":
        if form.validate_on_submit():
            layout = form.layout.data
            note_obj.title = form.title.data
            note_obj.content = form.content.data
            db.session.commit()
            return redirect(url_for("note", note_id=note_obj.id, title=note_obj.title, layout=layout))
        else:
            flash("Failed to update note. Please try again.", "danger")
    elif request.method == "GET":
        form.title.data = note_obj.title
        form.content.data = note_obj.content

    preview = markdown.markdown(note_obj.content)
    return render_template('note.html', form=form, notes=notes_list, folders=folders, open_folders=open_folders, note_id=note_id, title=note_obj.title, folder_form=folder_form, change_folder_form=change_folder_form, layout=layout, preview=preview)


@app.route("/new-folder", methods=['POST'])
@login_required
def new_folder():
    folder_form = NoteFolderForm()
    if folder_form.validate_on_submit():
        folder = NoteFolder(title=folder_form.title.data, user_id=current_user.id)
        db.session.add(folder)
        db.session.commit()

    return redirect(url_for('notes'))


@app.route("/change-folder/<int:note_id>", methods=['POST'])
@login_required
def change_folder(note_id):
    change_folder_form = ChangeFolderForm()
    if change_folder_form.submit():
        note_obj = Note.query.get_or_404(note_id)
        note_obj.folder_id = change_folder_form.selected_folder.data
        db.session.add(note_obj)
        db.session.commit()
    return redirect(url_for('notes'))


@app.route("/del-folder/<int:folder_id>", methods=['POST', 'GET'])
@login_required
def del_folder(folder_id):
    try:
        # Reassign notes in the folder to "Uncategorized"
        notes_list = Note.query.filter_by(user_id=current_user.id, folder_id=folder_id).all()
        for note_obj in notes_list:
            note_obj.folder_id = 1  # Assuming 1 is the ID for "Uncategorized"
        db.session.commit()

        # Delete the folder
        folder = NoteFolder.query.get_or_404(folder_id)
        db.session.delete(folder)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
    return redirect(url_for('notes'))


@app.route('/rename_folder/<int:folder_id>', methods=['POST'])
def rename_folder(folder_id):
    folder = NoteFolder.query.get_or_404(folder_id)  # Retrieve the folder using its ID
    new_name = request.form.get('title')  # Get the new title from the form
    if folder:
        folder.title = new_name
        db.session.commit()
    else:
        flash('Folder not found.', 'danger')
    return redirect(url_for('notes'))


@app.route("/add-note", methods=['POST'])
@login_required
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
@login_required
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


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='flemo@noreply.net', recipients=[user.email])
    msg.body = f'''To reset your password, click on the link below: 
{url_for('reset_token', token=token, _external=True)}
    
If you did not make this request, ignore this email
'''
    # mail.send(msg)


@app.route("/reset_password", methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('If an account with this email address exists, a password reset message will be sent shortly', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=form, title='Reset Password')


@app.route("/reset_password/<token>", methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_pw
        db.session.commit()
        flash(f'Your password has been updated.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form=form, title='Reset Password')
