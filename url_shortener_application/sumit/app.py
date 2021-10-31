import os,string,random,pyperclip
from flask import Flask,render_template,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

###########################SQL Alchemy Configuration###################################

basedir= os.path.abspath(os.path.dirname(__file__)) ##getting the path of the application server directory
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///' + os.path.join(basedir,'data.sqlite')  ###joining the sqlite with directory
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY'] = 'mykey'

db= SQLAlchemy(app)   ###passing the into SQL Alchemy
Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"
#########################################################################################


######################################## Create a Model ################################################


class shorturl(db.Model):
    __tablename__ ='shorturl'
    id=db.Column(db.Integer,primary_key=True)
    original_url= db.Column(db.String(600),nullable=False)
    shorted_url =db.Column(db.String(30),nullable=False)
    
    def __init__(self,original_url,shorted_url):
        self.original_url =original_url
        self.shorted_url=shorted_url

@login_manager.user_loader
def load_user(user_id):
    return logindata.query.get(user_id)

class logindata(db.Model, UserMixin):

    # Creating database for login credentials
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    user_name = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    def __init__(self, Username, password):
        self.user_name = Username
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

##############################################


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        user = logindata(Username=request.form.get('Username'),
                    password=request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # Grab the user from our User Models table
        user = logindata.query.filter_by(user_name=request.form.get('Username')).first()

        # Check that the user was supplied and the password is right
        # The check_password method comes from the User object
        if user is not None and user.check_password(request.form.get('password')):

            #Log in the user
            login_user(user)

            # If a user was trying to visit a page that requires a login
            # flask saves that URL as 'next'.
            next = request.args.get('next')

            # So let's now check if that next exists, otherwise we'll go to
            # the welcome page.
            if next == None or not next[0]=='/':
                next = url_for('index')

            return redirect(next)
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
    
#############################################3
def short_url_generator(num):
    while True:
        code= ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(num))
        short_url = shorturl.query.filter_by(shorted_url=code).first()
        if not short_url:
            return code


@app.route('/shortner',methods=['GET','POST'])
@login_required
def shortner():
    if request.method =='POST':
        url_entered=request.form.get('in_1')
        found_url = shorturl.query.filter_by(original_url=url_entered).first()

        if found_url:
            return redirect(url_for("display_short_url", url=found_url.shorted_url))
        else:
            short_url=short_url_generator(8)
            new_link=shorturl(url_entered,short_url)
            db.session.add(new_link)
            db.session.commit()
            return redirect(url_for("display_short_url", url=short_url))
    else:
        return render_template("url_typer.html")


@app.route('/<short_url>')
def redirection(short_url):
    long_url = shorturl.query.filter_by(shorted_url=short_url).first()
    if long_url:
        return redirect(long_url.original_url)
    else:
        return f'<h1>Url doesnt exist</h1>'

@app.route('/display/<url>')
@login_required
def display_short_url(url):
    return render_template('urls.html', short_url_display=url)

@app.route('/copy')
def copy():
    copied_str=request.form.get('input')
    pyperclip.copy(copied_str)
    return render_template('urls.html')

@app.route('/history')
@login_required
def history():
    return render_template('history.html', vals=shorturl.query.all())
    

if __name__ =="__main__":
    app.run(debug=True)


