from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import db, login_manager
from app.models import User, UserRole
from app.forms import LoginForm, RegistrationForm, UserEditForm

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_user_active():
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', form=form, title='Sign In')

@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.is_admin():
        flash('Only administrators can register new users.', 'error')
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=UserRole(form.role.data)
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{user.username}" has been registered successfully!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/register.html', form=form, title='Register User')

@auth.route('/users')
@login_required
def users():
    if not current_user.is_admin():
        flash('Only administrators can view users.', 'error')
        return redirect(url_for('main.index'))
    
    users = User.query.order_by(User.full_name).all()
    return render_template('auth/users.html', users=users, title='User Management')

@auth.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_admin():
        flash('Only administrators can edit users.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = UserRole(form.role.data)
        user.is_active_user = form.is_active_user.data
        
        db.session.commit()
        flash(f'User "{user.username}" has been updated successfully!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/edit_user.html', form=form, user=user, title='Edit User')

@auth.route('/user/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin():
        flash('Only administrators can delete users.', 'error')
        return redirect(url_for('main.index'))
    
    if current_user.id == id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('auth.users'))
    
    user = User.query.get_or_404(id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{username}" has been deleted successfully!', 'success')
    return redirect(url_for('auth.users'))

@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='My Profile')