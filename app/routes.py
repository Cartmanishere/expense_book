from app import app, db
from flask import render_template, redirect, url_for, flash
from app.forms import LoginForm, RegistrationForm, RecordForm
from flask_login import current_user, login_user, logout_user
from app.models import User, Record
from flask_login import login_required
from flask import request
from werkzeug.urls import url_parse
from dateutil import tz, parser
from_zone = tz.tzutc()
to_zone = tz.tzlocal()


@app.route('/')
@app.route('/index')
@login_required
def index():
    all_records = Record.query.filter_by(user=current_user).all()
    # Convert datetimes
    for record in all_records:
        utc = record.timestamp
        utc = utc.replace(tzinfo=from_zone)
        local = utc.astimezone(to_zone)
        record.timestamp = local.strftime('at %H:%M on %d/%m/%Y')

    if len(all_records) == 0:
        all_records = None
    return render_template('index.html', title='Home', user=current_user, records=all_records)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    form = RecordForm()
    if form.validate_on_submit():
        record = Record(amount=form.amount.data, desc=form.desc.data, category=form.category.data, user=current_user)
        db.session.add(record)
        db.session.commit()
        flash('Expense added in your expense book!', 'success')
        if 'another' in form.submit.data.lower():
            return redirect(url_for('add_record'))

        return redirect(url_for('index'))

    return render_template('add_record.html', title='Add Record', form=form)