from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm, TaskForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'c05c5ad21a274a97267a1fbe0b243a64'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    tasks = db.relationship('Task', backref='author', lazy=True)
    notes = db.relationship('Note', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Task('{self.title}', '{self.done}')"


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Note('{self.title}')"

task_list = [
    {'id': 1, 'title': 'Dummy Task 1', 'done': True},
    {'id': 2, 'title': 'Dummy Task 2', 'done': False}
]


@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html', title='Home')


@app.route("/tasks")
def tasks():
    form = TaskForm()
    return render_template('tasks.html', task_list=task_list, form=form)


@app.route("/add-task", methods=['POST'])
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        # Create a new task dictionary
        new_task = {
            'id': max(task['id'] for task in task_list) + 1 if task_list else 1,
            'title': form.task.data,
            'done': False
        }

        task_list.append(new_task)
    else:
        flash("Failed to add task. Please try again.", "danger")

    return redirect(url_for('tasks'))


@app.route('/update-tasks', methods=['POST'])
def update_tasks():
    global task_list

    if 'remove_task' in request.form:
        # Task removal request
        task_id = int(request.form['remove_task'])
        task_list[:] = [task for task in task_list if task['id'] != task_id]  # Remove task with matching id
    else:
        # Update task completion status
        for task in task_list:
            task['done'] = f'task_done_{task["id"]}' in request.form

    return redirect(url_for('tasks'))


@app.route("/notes")
def notes():
    return render_template('notes.html')


@app.route("/blog")
def blog():
    return render_template('blog.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@local.net' and form.password.data == 'admin':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful!', 'danger')

    return render_template('login.html', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
