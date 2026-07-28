from flask import Flask,request,redirect,render_template,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import smtplib
import random
from email.message import EmailMessage
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash,check_password_hash
import uuid
import datetime
app = Flask(__name__)
app.secret_key="Azby"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    admission_number = db.Column(db.String(20), unique=True, nullable=False)

    name = db.Column(db.String(100), nullable=False)

    mobile_number = db.Column(db.String(10), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    branch = db.Column(db.String(10), nullable=False)

    section = db.Column(db.String(4), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    profile_pic = db.Column(
    db.String(200),
    nullable=False,
    default="default.png"
    )

    bio = db.Column(db.String(1000))
    linkedin = db.Column(db.String(255))
    github = db.Column(db.String(255))
    portfolio = db.Column(db.String(10000))
    skills = db.Column(db.String(2000))

    '''
    bio
    linkedin
    github
    portfolio
    skills
    '''   

    def __repr__(self):
        return f"{self.admission_number}"
    


class JobData(db.Model):

    jobid = db.Column(db.Integer, primary_key=True)

    userid = db.Column(db.Integer, nullable=False)

    jobtitle = db.Column(db.String(255), nullable=False)

    companyname = db.Column(db.String(255), nullable=False)

    location = db.Column(db.String(255), nullable=False)

    jobtype = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text, nullable=False)

    skillsreq = db.Column(db.Text, nullable=False)

    salary = db.Column(db.String(100), nullable=False)

    applicationlink = db.Column(db.String(500), nullable=False)

    dateposted = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"{self.jobid}"

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        adminno = request.form['admn'].strip()
        mobno = request.form['mob'].strip()
        passw = request.form['pass']
        # print("Admission entered:", adminno)
        # print("Mobile entered:", mobno)

        user = User.query.filter_by(
            admission_number=adminno,
            mobile_number=mobno,
        ).first()

        # print("User found:", user)
        if user:
            if check_password_hash(user.password,passw):
                session['login_admission_number'] = user.admission_number
                session['userid'] = user.id
                session['username'] = user.name
                return redirect('/dashboard')
            else:
                return render_template('login.html',message='Invalid Credentials. Please Try Again')
    return render_template("login.html")

@app.route('/')
def homepage():
    return render_template('homepage.html')


@app.route('/dashboard')
def dashboard():
    user_id = session.get('userid')

    if 'userid' not in session:
        return redirect('/login')
    
    user = User.query.get(user_id)
    total_alumni = User.query.count()
    total_jobs,total_events,total_messages=0,0,0

    if not user:
        session.pop('userid', None)
        return redirect('/')

    return render_template(
        'dashboard.html',
        user=user,
        total_jobs=total_jobs,
        total_events=total_events,
        total_messages=total_messages
    )
    # return render_template('dashboard.html')

@app.route('/signup',methods=['GET','POST'])
def signupuser():
    if request.method=='POST':
        admission = request.form['adminno']
        name = request.form['fullname']
        mobile = request.form['regmbno']
        password = request.form['pass']
        hashed_password = generate_password_hash(password)
        branch = request.form['branch']
        section = request.form['sec']
        tomail = request.form['email']
        profile = request.files['profilepic']
        filename='default.png'
        if profile and profile.filename != "":
            filename = str(uuid.uuid4()) + "_" + secure_filename(profile.filename)

            profile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        else:
            filename = "default.png"
        session['signup_data'] = {
            "admission": admission,
            "name": name,
            "mobile": mobile,
            "password": hashed_password,
            "branch": branch,
            "section": section,
            "email": tomail,
            'profile_pic':filename
        }
        confirmpassword = request.form['confirmpass']
        checkadmin = User.query.filter_by(admission_number=admission).first()
        checkmobile = User.query.filter_by(mobile_number=mobile).first()
        checkemail = User.query.filter_by(email=tomail).first()
        if checkadmin:
            return render_template('signup.html',message="User Already Exists!!")
        elif checkmobile:
            return render_template('signup.html',message="Mobile Number Already Exists!!")
        elif checkemail:
            return render_template('signup.html',message="Email Already Exists!!")
        elif password!=confirmpassword:
            return render_template('signup.html',message='Passwords do not match')
        else:
            #Send the otp via email
            otp = random.randint(100000,999999)
            session['signup_otp'] = otp
            signup_server = smtplib.SMTP('smtp.gmail.com',587)
            signup_server.starttls()
            signup_server.login('Harshadityag@gmail.com','bsnq dzkf cagw zthp')
            msg = EmailMessage()
            msg['Subject'] = 'OTP VERIFICATION'
            msg['From'] = 'harshadityag@gmail.com'
            msg['To'] = tomail
            msg.set_content(
                f"""
                Hello

                Your OTP for VConnect is: {otp}

                Do not share this OTP with anyone.

                Regards,
                Team VConnect
                """)
            signup_server.send_message(msg)
            signup_server.quit()
            print(session['signup_data'])
            return redirect('/verifyotp')

    else:
        return render_template('signup.html')

@app.route('/verifyotp', methods=['GET', 'POST'])
def verify():
    if 'signup_otp' not in session:
        return redirect('/')
    if request.method=='POST':
        user_otp = request.form['otp']
        if len(user_otp)!=6 or not user_otp.isdigit():
            return render_template('verifyotp.html',message="Enter only 6 digit code")
        if user_otp==str(session['signup_otp']):
            data = session['signup_data']
            print(session['signup_data'])
            newsignup_user = User(
                admission_number = data['admission'],
                name = data['name'],
                mobile_number = data['mobile'],
                password = data['password'],
                branch = data['branch'],
                section = data['section'],
                email = data['email'],
                profile_pic = data['profile_pic']
            )
            db.session.add(newsignup_user)
            db.session.commit()
            session.pop('signup_data', None)
            session.pop('signup_otp', None)
            return redirect('/login')
        else:
            return render_template('verifyotp.html',message='Invalid OTP')
    return render_template('verifyotp.html')

@app.route('/forgotpassword',methods=['POST','GET'])
def forgot():
    if request.method=='POST':
        if 'sendotp' in request.form:
            otp = random.randint(100000,999999)
            session['forgot_otp'] = str(otp)
            tomail = request.form['email']
            # session['forgotpassword_email'] = tomail
            session['forgot_email'] = tomail
            checkemail = User.query.filter_by(email=tomail).first()
            if checkemail:
                server = smtplib.SMTP('smtp.gmail.com',587)
                server.starttls()
                server.login('harshadityag@gmail.com','bsnq dzkf cagw zthp')
                msg = EmailMessage()
                msg['Subject']='EMAIL VERIFICATION'
                msg['From'] = 'harshadityag@gmail.com'
                msg['To'] = tomail
                msg.set_content(
                f"""
                Hello,

                Your OTP for VConnect is: {otp}

                Do not share this OTP with anyone.

                Regards,
                Team VConnect
                """
                )
                server.send_message(msg)
                server.quit()
                return render_template('forgotpassword.html',otp_sent = True,email=session.get('forgot_email'))
            else:
                return render_template('forgotpassword.html',message="Email doesn't exist.")
        elif 'verifyotp' in request.form:
            userotp = request.form['otp']
            if userotp == session.get('forgot_otp'):
                session.pop('forgot_otp', None)
                return redirect('/resetpassword')
            else:
                return render_template('forgotpassword.html',otp_sent=True,message="OTP Entered is Incorrect",email=session.get('forgot_email'))
    return render_template('forgotpassword.html')

@app.route('/resetpassword',methods=['GET','POST'])
def reset_password():
    print(session)
    if 'forgot_email' not in session:
        return redirect('/login')
    if request.method=='POST':
        # resetpassword_userid = session['userid']
        newpassword = request.form['newpassword']
        confirmnewpassword = request.form['confirmpassword']
        if newpassword==confirmnewpassword:
            resetpassword_user = User.query.filter_by(email = session['forgot_email']).first()
            resetpassword_user.password = newpassword
            db.session.commit()
            session.pop('forgot_email', None)
            session.pop('forgot_otp', None)
            # session.pop('forgot_email',None)
            return redirect('/login')
        else:
            return render_template('resetpassword.html',message='Both the passwords do not match')


    return render_template('resetpassword.html')


#LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')





@app.route('/profile',methods=['GET','POST'])
def profile_dashboard():
    if 'userid' not in session:
        return redirect('/')
    profile_userid = session['userid']
    Query_Object_Profile = User.query.filter_by(id=profile_userid).first()
    # session['profile_details'] = Query_Object_Profile
    # profile_details = {
    #     'id':profile_userid,
    #     'admission_number':Query_Object_Profile.admission_number,
    #     'name':Query_Object_Profile.name,
    #     'mobile_number':Query_Object_Profile.mobile_number,
    #     'password':Query_Object_Profile.password,
    #     'branch':Query_Object_Profile.branch,
    #     'section':Query_Object_Profile.section,
    #     'email':Query_Object_Profile.email,
    #     'profile_pic':Query_Object_Profile.profile_pic,
    # }
    return render_template('profile.html',user=Query_Object_Profile)




@app.route('/editprofile',methods=['GET','POST'])
def editprofile():
    if 'userid' not in session:
        return redirect('/')
    if request.method=='POST':
        edit_profile_details = User.query.filter_by(id=session.get('userid')).first()
        edit_profile_details.bio = request.form['bio']
        edit_profile_details.linkedin = request.form['linkedin']
        edit_profile_details.github = request.form['github']
        edit_profile_details.portfolio = request.form['portfolio']
        edit_profile_details.skills = request.form['skills']
        profile = request.files['profilepic']
        if profile and profile.filename != "":
            filename = str(uuid.uuid4()) + "_" + secure_filename(profile.filename)
            profile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            edit_profile_details.profile_pic = filename
        db.session.commit()
        return redirect('/profile')
    edit_profile_user_details=User.query.filter_by(id=session['userid']).first()
    return render_template('editprofile.html',user=edit_profile_user_details)



@app.route('/addjob',methods=['GET','POST'])
def addjob():
    if 'userid' not in session:
        return redirect('/')
    if request.method=='POST':
        jobtitle = request.form['jobtitle']
        companyname = request.form['companyname']
        location = request.form['location']
        jobtype = request.form['jobtype']
        salary = request.form['salary']
        applicationlink = request.form['applicationlink']
        skillsreq = request.form['skillsreq']
        description = request.form['description']
        upload_details = JobData(
            userid = session['userid'],
            jobtitle=jobtitle,
            companyname=companyname,
            location=location,
            jobtype=jobtype,
            salary=salary,
            applicationlink=applicationlink,
            skillsreq=skillsreq,
            description=description
        )
        db.session.add(upload_details)
        db.session.commit()
        return redirect('/browsejobs')
    return render_template('addjob.html')



@app.route('/jobs',methods=['GET','POST'])
def jobs():
    return render_template('jobs.html')





@app.route('/browsejobs')
def browsejobs():
    # if 'search' in i don't kno what to do here...
    search = request.args.get('search')
    if search:
        all_jobs = JobData.query.filter(
            or_(
                JobData.jobtitle.ilike(f"%{search}%"),
                JobData.companyname.ilike(f"%{search}%"),
                JobData.skillsreq.ilike(f"%{search}%")
            )
        ).order_by(JobData.dateposted.desc()).all()
    else:
        all_jobs = JobData.query.order_by(JobData.dateposted.desc()).all()
    joblist = []
    for job in all_jobs:
        conuser = User.query.filter_by(id=job.userid).first()
        joblist.append({'job':job,'user':conuser})
    return render_template('browsejobs.html',joblist=joblist)

@app.route('/viewdetails/<int:jobid>')
def jobdetails(jobid):
    if not 'userid' in session:
        return redirect('/')
    job_details = JobData.query.filter_by(jobid=jobid).first()
    if not job_details:
        return redirect('/browsejobs')
    poster = User.query.filter_by(id = job_details.userid).first()
    return render_template('viewdetails.html',job = job_details,poster=poster)



@app.route('/alumni')
def alumni():
    if 'userid' not in session:
        return redirect('/')
    searchalumni = request.args.get('search')
    if searchalumni:
        alumnidetails = User.query.filter(
            User.id!=session['userid'],
            or_(
                User.admission_number.ilike(f"%{searchalumni}%"),
                User.name.ilike(f"%{searchalumni}%"),
                User.branch.ilike(f"%{searchalumni}%")
            )
        ).order_by(User.id.asc()).all()
    else:
        alumnidetails = User.query.filter(User.id!=session['userid']).order_by(User.id.asc()).all()
    return render_template('alumni.html',alumnidetails=alumnidetails)


@app.route('/viewalumniprofile/<int:alumniuserid>')
def viewalumniprofile(alumniuserid):
    if 'userid' not in session:
        return redirect('/')
    alumniuserprofile = User.query.filter_by(id = alumniuserid).first()
    if not alumniuserprofile:
        return redirect('/alumni')
    alumnijobdata = JobData.query.filter_by(userid=alumniuserid).order_by(JobData.dateposted.desc()).all()
    return render_template('viewalumniprofile.html',alumniuserprofile=alumniuserprofile,alumnijobdata=alumnijobdata)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)