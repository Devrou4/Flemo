from flask import Flask, render_template, request, redirect, url_for, flash
from forms import RegistrationForm, LoginForm


app = Flask(__name__)

app.config['SECRET_KEY'] = 'c05c5ad21a274a97267a1fbe0b243a64'

task_list = [
    {'id': 1, 'tittle': 'Dummy Task 1', 'done': True},
    {'id': 2, 'tittle': 'Dummy Task 2', 'done': False}
]

# TODO refactor the templates to use a base


@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')


@app.route("/tasks")
def tasks():
    return render_template('tasks.html', task_list=task_list)


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
    return render_template('about.html')


@app.route("/login", methods=['GET','POST'])
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
