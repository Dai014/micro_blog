from urllib.parse import urlsplit

from flask import render_template, redirect, flash, url_for, request

from app import app,db
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa

from app.models import User


@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html',title='Home', posts = posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: # <-- Không cho phép nếu đã đăng nhập
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit(): # <-- Nếu form hợp lệ
        user = User(username=form.username.data, email=form.email.data) # Tạo User object
        user.set_password(form.password.data) # Set password (sẽ băm)
        db.session.add(user) # Thêm vào session
        db.session.commit() # Commit vào database
        flash('Congratulations, you are now a registered user!') # Thông báo thành công
        return redirect(url_for('login')) # Chuyển hướng đến trang login
    return render_template('register.html', title='Register', form=form)
