from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, WatchlistItem
from extensions import db
from stock_service import get_or_create_stock

auth_bp = Blueprint('auth', __name__)

DEFAULT_WATCHLIST_TICKERS = ["AAPL", "MSFT", "NVDA"]


def _add_default_watchlist(user):
    for ticker in DEFAULT_WATCHLIST_TICKERS:
        try:
            stock = get_or_create_stock(ticker)
        except Exception as e:
            print(f"Error occurred while fetching default stock '{ticker}': {str(e)}")
            continue
        if not stock:
            continue
        db.session.add(WatchlistItem(user_id=user.id, stock_ticker=stock.ticker))
    db.session.commit()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return redirect(url_for('auth.register'))
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        _add_default_watchlist(new_user)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('auth.login'))
    return render_template('login.html')
@auth_bp.route('/logout')
@login_required
def signout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))