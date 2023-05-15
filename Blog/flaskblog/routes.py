from flask import render_template, url_for, flash, redirect,request, abort
from flaskblog import app, db, bcrypt
from flaskblog.models import User, Post
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flask_login import login_user, current_user, logout_user, login_required
import secrets
from PIL import Image
import os  #> to grab the image fileextnsion and save it as it was uploaded by user
# posts = [
#     {
#         'author': 'Kunal Wade',
#         'title': 'Blog Post 1',
#         'content': 'First post content',
#         'date_posted': 'January 18, 2023'
#     },
#     {
#         'author': 'Guido Van Russom',
#         'title': 'Blog Post 2',
#         'content': 'Second post content',
#         'date_posted': 'January 18,2023'
#     },
#     {
#         'author': 'Jordan Walke',
#         'title': 'Blog Post 3',
#         'content': 'Third post content',
#         'date_posted': 'January 18,2023'
#     },
#     {
#         'author': 'ALan Kay',
#         'title': 'Blog Post 4',
#         'content': 'Fourth post content',
#         'date_posted': 'January 18,2023'
#     },
# ]


@app.route("/")
@app.route("/home")
def home():
    #~!Pagination
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    #~%When user is logged in and tries to click login and register then it should redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account has been created! You can Login now!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    # ~*When user is logged in and tries to click login and register then it should redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        # if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            # flash('You have been logged in!', 'success')
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data) 
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


#~^ Logout routes
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

#~* Picture data function
def save_picture(form_picture):
    #~%To avoid collisions pf file name from user and the pic file saved on our file system we use random_hex
    random_hex = secrets.token_hex(8)
    _,f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics',picture_fn)
    ##To resize the Image --use Pillow pacakge

    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
#~>Decorator for if the user tries to route to account through localhost link then to display that login is required to see account
#~!This will redirect to login page with msg:Please login to access the page
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your Account has been updated!','success')
        return redirect(url_for('account'))
    #~#For the Account form to be already populated with the current user -user name and email
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html',title='Account', image_file= image_file, form=form)


@app.route("/post/new", methods=['GET','POST'])
@login_required
def new_post():
    form =PostForm()
    if form.validate_on_submit():
        post=Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your Post has been created!','success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',form = form, legend='New Post')


#~!Adding variable to routes 
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id) #~#get_or_404 gives the post with id if it exists either gives 404 error
    return render_template("post.html",title=post.title, post=post)


#~% Route to update post
@app.route('/post/<int:post_id>/update', methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)   #~*Not Found
    if post.author != current_user:
        abort(403)       #~#Forbidden
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title  #~>FOr changes in legend
        form.content.data = post.content
        
    return render_template('create_post.html', title="Update Post", form=form, legend='Update Post')

#~! Route to delete post
@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your Post has been deleted!','success')
    return redirect(url_for('home'))

@app.route('/user.<string:username>')
def user_posts(username):
    page = request.args.get('page',1,type = int)
    user = User.query.filter_by(username = username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('user_posts.html',posts=posts,user=user)