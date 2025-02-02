from flask import Blueprint, jsonify, request, redirect, url_for, jsonify, flash, session
from bson.objectid import ObjectId
from . import mongo
from flask import Blueprint, render_template
from emailing import send_email_inquirey, reset_password_code, contact_email
import random
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from lists import Industries, University
from datetime import datetime, timedelta, date
from better_profanity import profanity


main = Blueprint('main', __name__)

profanity.load_censor_words()
UPLOAD_FOLDER = 'app/static/images/profilepics'
UPLOAD_FOLDER_RESUME = 'app/static/pdf/resumes'
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit


ALLOWED_EXTENSIONS_RESUME = {'pdf'}
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_pdf(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_RESUME

@main.route('/')
def home():
    return render_template('home.html')

main = Blueprint('main', __name__)



@main.route('/')
def home():
    return render_template('home.html')

@main.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == "POST":
        # Get form data
        c_date = str(date.today())
        active = "active"
        
        fname = request.form['fname']
        fname = fname.lower()        
        fname = fname.capitalize()
        
        lname = request.form['Lname']
        lname = lname.lower()        
        lname = lname.capitalize()
        
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        phone = request.form['phone']
        address = request.form['address']
        state = request.form['state']
        
        city = request.form['city']
        city = city.lower()        
        city = city.capitalize()
        
        zip_code = request.form['zip']  # Renamed to avoid conflict with Python's `zip`
        ato = request.form['ATO']
        uniname = request.form['uniname']
        degree = request.form['degree']
        yearofstudy = request.form['yearffstudy']
        citywork = request.form['citywork']
        relocation = request.form['relocation']
        industry_preference = request.form.getlist('industryPreference[]')
        skills = request.form['skills']
        certifications = request.form['certifications']
        linkedin = request.form['linkedin']
        
        pfpfile = request.files.get('pfpfile')
        resumefile = request.files.get('resumefile')
        
        random_combination = random.randint(1000000, 9999999)
        fname = fname.replace(" ", "")
        lname = lname.replace(" ", "")
        student_id = fname[0]+lname[0]+str(random_combination)
        
        # Handle profile picture
        if pfpfile and allowed_file(pfpfile.filename):
            if len(pfpfile.read()) > MAX_CONTENT_LENGTH:
                flash('Profile picture is too large. Maximum size is 5 MB.', 'danger')
                return redirect(request.url)  # redirect back to the form
            pfpfile.seek(0)  # Reset the file pointer after reading the size
            filename = f"{student_id}_{secure_filename(pfpfile.filename)}"
            pfpfilepath = os.path.join(UPLOAD_FOLDER, filename)
            pfpfile.save(pfpfilepath)
        else:
            flash('Invalid file format for profile picture or no file selected', 'danger')
            pfpfilepath = ""

        # Handle resume file (optional)
        if resumefile and allowed_file_pdf(resumefile.filename):
            if len(resumefile.read()) > MAX_CONTENT_LENGTH:
                flash('Resume is too large. Maximum size is 5 MB.', 'danger')
                return redirect(request.url)
            resumefile.seek(0)  # Reset the file pointer
            resumefilename = f"{student_id}_{secure_filename(resumefile.filename)}"
            resumefilepath = os.path.join(UPLOAD_FOLDER_RESUME, resumefilename)
            resumefile.save(resumefilepath)
        else:
            resumefilename = ''


        

        
        
        collection = mongo.db.students  # Replace with your collection name
        records = collection.find()
    
        existing_user = collection.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
        if existing_user:
            return render_template("student_signup_fail.html", Industry=Industries, unis=University)

                
        
        # Create a document to insert into MongoDB
        student_data = {
            "account_status": "unlocked",
            "login_attempt": 0,
            "last_login": c_date,
            "status": active,
            "student_id": student_id,
            "fname": fname,
            "lname": lname,
            "pfpfile": filename,
            "resumefile": resumefilename,
            "email": email,
            "password": password,
            "phone": phone,
            "address": address,
            "state": state,
            "city": city,
            "zip": zip_code,
            "ato": ato,
            "uniname": uniname,
            "degree": degree,
            "year_of_study": yearofstudy,
            "city_work": citywork,
            "relocation": relocation,
            "industry_preference": industry_preference,
            "skills": skills,
            "certifications": certifications,
            "linkedin": linkedin
        }
        
        # Insert the document into the MongoDB collection
        mongo.db.students.insert_one(student_data)  # Replace `students` with your collection name
        
        print(jsonify({"message": "Student data added successfully!"}))
        return redirect(url_for('main.student_login'))
    
    
    return render_template("student_signup.html", Industry = Industries, unis = University)

@main.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['exampleInputEmail1']
        password = request.form['inputPassword5']
        
        collection = mongo.db.students  # Replace with your collection name
        records = collection.find()

        found = False
        
        
        for record in records:
            if record["email"].lower() == email.lower() and record['account_status'] == "locked":
                now = datetime.now()
                time_difference = record["locked_until"] - now
                # Extract minutes as an integer
                minutes_difference = time_difference.total_seconds() // 60 
                
                if minutes_difference < 0: 
                    mongo.db.students.update_one(
                        {"email": email},  # Query to find the document
                        {"$set": {"account_status": "unlocked",
                                  "login_attempt": 0
                        }})
                    return render_template('student_login.html', locked="now")
                
                else:
                    return render_template('student_login.html', locked=record["locked_until"])
                
            if record["email"].lower() == email.lower() and check_password_hash(record['password'], password):
                session['student_id'] = record['student_id']
                
                c_date = str(date.today())                
                mongo.db.students.update_one(
                    {"student_id": session['student_id']},  # Query to find the document
                    {"$set": {"last_login": c_date,
                              "login_attempt": 0}}        # Use $set to specify fields to update
                )
                
                return redirect(url_for('main.student_dashboard'))  # Replace this with a redirect or response
            
            elif record["email"].lower() == email.lower():
                login_attempt = record["login_attempt"] + 1
                
                if login_attempt >= 3:
                    now = datetime.now()
                    future_time = now + timedelta(minutes=3)
                    
                    mongo.db.students.update_one(
                        {"email": email},  # Query to find the document
                        {"$set": {"account_status": "locked",
                                  "locked_until": future_time
                                  }}        # Use $set to specify fields to update
                    ) 
                
                mongo.db.students.update_one(
                    {"email": email},  # Query to find the document
                    {"$set": {"login_attempt": login_attempt}}        # Use $set to specify fields to update
                ) 
            
        else:                    
            return render_template("student_login_fail.html")
        
        
    return render_template('student_login.html', locked="no")


@main.route('/business_contact', methods=['GET', 'POST'])
def business_contact():
    if request.method == 'POST':
        bname = request.form['bname']
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['exampleInputEmail1']
        pnumber = request.form['pnumber']
        
        print(email, bname, fname, lname, pnumber)
        response = send_email_inquirey(email, bname, fname, lname, pnumber)
        print(response)
        # Add your login logic here
         # Replace this with a redirect or response
    return render_template('businesscontact.html')

@main.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('main.student_login'))
    
    collection = mongo.db.students  # Replace with your collection name
    student = collection.find_one({"student_id": session['student_id']})
             
    return render_template('student_dashboard_v2.html', records=student)

    

@main.route('/business_login', methods=['GET', 'POST'])
def business_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        collection = mongo.db.business  # Replace with your collection name
        records = collection.find()
        business = collection.find_one({"email": email})
        
        found = False
        for record in records:
            if record["email"].lower() == email.lower() and record['account_status'] == "locked":
                now = datetime.now()
                time_difference = record["locked_until"] - now
                # Extract minutes as an integer
                minutes_difference = time_difference.total_seconds() // 60 
                
                if minutes_difference < 0: 
                    mongo.db.business.update_one(
                        {"email": email},  # Query to find the document
                        {"$set": {"account_status": "unlocked",
                                  "login_attempt": 0
                        }})
                    return render_template('business_login.html', locked="now")
                
                else:
                    return render_template('business_login.html', locked=record["locked_until"])
            
            
            if record["email"].lower() == email.lower() and check_password_hash(record['password'], password):
                session['business_id'] = business['email']  # Store student_id in session
                
                c_date = str(date.today())                
                mongo.db.business.update_one(
                    {"email": session['business_id']},  # Query to find the document
                    {"$set": {"last_login": c_date}}        # Use $set to specify fields to update
                )
                
                return redirect(url_for('main.business_dashboard'))
            
            
            elif record["email"].lower() == email.lower():
                login_attempt = record["login_attempt"] + 1
                
                if login_attempt >= 3:
                    now = datetime.now()
                    future_time = now + timedelta(minutes=3)
                    
                    mongo.db.business.update_one(
                        {"email": email},  # Query to find the document
                        {"$set": {"account_status": "locked",
                                  "locked_until": future_time
                                  }}        # Use $set to specify fields to update
                    ) 
                
                mongo.db.business.update_one(
                    {"email": email},  # Query to find the document
                    {"$set": {"login_attempt": login_attempt}}        # Use $set to specify fields to update
                ) 
            
        else:    
            return render_template("business_login_fail.html")
        
        
    return render_template('business_login.html', locked="no")


@main.route('/business_dashboard', methods=['GET', 'POST'])
def business_dashboard():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))

    email = session["business_id"]
    print(f"Accessed dashboard with email: {email}")
    if request.method == 'POST':
        # Only handle form data if it's a POST request
        random_combination = random.randint(1000000, 9999999)
        code = email.replace(" ", "")
        post_id = email[0:1] + str(random_combination)
        
        # Collect the form data
        title = request.form['jobtitle']
        industry = request.form['Industry']
        state = request.form['state']
        city = request.form['city']
        desc = request.form['textarea']
        c_date = str(date.today())
        
        censored_text = profanity.censor(desc)
        if "***" in censored_text:
            flash("Profanity detected. You need to wash your mouth out.", 'danger')
            return redirect(request.url)
        
        # Update MongoDB with the job post data
        student_filter = {"email": email} 
        update_operation = {
            "$push": {
                "jobposts": {
                    "post_id": post_id,
                    "title": title,
                    "location": f"{city}, {state}",
                    "state": state,
                    "city": city,
                    "industry": industry,
                    "description": desc,
                    "responses": [],
                    "date": c_date,
                }
            }
        }
        
        result = mongo.db.business.update_one(student_filter, update_operation)
        
        if result.modified_count > 0:
            return redirect(url_for('main.business_dashboard'))
        else:
            return redirect(url_for('main.business_dashboard'))
    
    # This block will run only on GET requests (when the page is first loaded)
    collection = mongo.db.business  # Replace with your collection name
    student_collection = mongo.db.students
    student_records = student_collection.find()
    savedstudents = []
    currentstudents = []
    records = collection.find()
    for record in records:
        if record["email"] == email:  
            student_records = list(student_collection.find())  # Convert cursor to a list

            # Create a set of student_ids in currentstudents for quick lookup
            current_student_ids = {currentstudent["student_id"] for currentstudent in record["currentstudents"]}

            # Process savedstudents
            for savedstudent in record["savedstudents"]:
                if savedstudent["student_id"] in current_student_ids:  # Skip if already in currentstudents
                    continue
                
                for student in student_records:
                    if savedstudent["student_id"] == student["student_id"]:
                        savedstudents.append(student)

            # Process currentstudents
            for currentstudent in record["currentstudents"]:
                for student1 in student_records:
                    if currentstudent["student_id"] == student1["student_id"]:
                        student1["accepted"] = currentstudent["accepted"]
                        currentstudents.append(student1)

            # Render the template once matching is complete
            return render_template(
                'business_dashboard.html',
                records=record,
                Industry=Industries,
                students=savedstudents,
                current=currentstudents
            )
    else:
        print("error occurred")



@main.route('/student_finder', methods=['GET', 'POST'])
def student_finder():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))

    email = session["business_id"]
    
    if request.method == 'POST':
        student_data = request.json  # This will be the student object sent from JavaScript
        
        student_filter = {"email": email} 
        update_operation = {
            "$push": {
                "savedstudents": {
                    "student_id": student_data["student_id"],
                }
            }
        }
        
        result = mongo.db.business.update_one(student_filter, update_operation)
        
        
        return redirect(url_for('main.student_finder'))


    # Prepare collections
    collection = mongo.db.business
    student_collection = mongo.db.students
    
    # Fetch all records
    records = collection.find()
    student_records = student_collection.find()
    
    for record in records:
        if record["email"] == email:
            saved_students_ids = {student["student_id"] for student in record["savedstudents"]}  # Create a set of saved student IDs
              
            student_records = [
                student for student in student_records 
                if student["student_id"] not in saved_students_ids and student["status"] == "active"
            ]
            
            return render_template('student_finder.html', Industry=Industries, unis=University, students=student_records)


@main.route('/student_saver', methods=['GET', 'POST'])
def student_saver():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))
    
    email = session["business_id"]
    if request.method == 'POST':
        
        c_date = str(date.today())
        student_data = request.json  # This will be the student object sent from JavaScript
        student_filter = {"email": email} 
        update_operation = {
                "$push": {
                    "currentstudents": {
                        "student_id": student_data["student_id"],
                        "accepted":  c_date,     
                    }
                }
            }
            
        result = mongo.db.business.update_one(student_filter, update_operation)
            
            
        return redirect(url_for('main.business_dashboard'))
    
    
@main.route('/student_unsaver', methods=['POST'])
def student_unsaver():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))
    
    email = session["business_id"]
    if request.method == 'POST':
        # Ensure you can see what is being received
        print("Received student data for unsaving:", request.json)
        
        student_data = request.json  # Get student data from the request
        
        # Define the filter and update operation to remove the student_id
        student_filter = {"email": email}
        update_operation = {
            "$pull": {
                "savedstudents": {
                    "student_id": student_data["student_id"]  # Match the student_id to remove
                }
            }
        }
        
        # Perform the update operation
        result = mongo.db.business.update_one(student_filter, update_operation)

        # Respond with a success message
        if result.modified_count > 0:
            print("success")
        else:
            print("failed")

@main.route('/student_uncurrent', methods=['POST'])
def student_uncurrent():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))
    
    email = session["business_id"]
    if request.method == 'POST':
        # Ensure you can see what is being received
        print("Received student data for unsaving:", request.json)
        
        student_data = request.json  # Get student data from the request
        
        # Define the filter and update operation to remove the student_id
        student_filter = {"email": email}
        update_operation = {
            "$pull": {
                "currentstudents": {
                    "student_id": student_data["student_id"]  # Match the student_id to remove
                }
            }
        }
        
        # Perform the update operation
        result = mongo.db.business.update_one(student_filter, update_operation)

        # Respond with a success message
        if result.modified_count > 0:
            print("success")
        else:
            print("failed")
            
@main.route('/job_searcher', methods=['GET', 'POST'])
def jobsearcher():
    if 'student_id' not in session:
        return redirect(url_for('main.student_login'))
    
    student_id = session["student_id"]
    
    if request.method == 'POST':
        postid = request.form['postid']
        fname = request.form['fname']
        lname = request.form['lname']
        desc = request.form['desc']
        
        censored_text = profanity.censor(desc)
        if "***" in censored_text:
            flash("Profanity detected. You need to wash your mouth out.", 'danger')
            return redirect(request.url)
         
        # Use dot notation with array filters to update the specific jobpost's responses array
        jobposts_filter = {
            "jobposts.post_id": postid  # Find the job post with the given post_id
        }

        update_operation = {
            "$push": {
                "jobposts.$.responses": {  # Use positional operator '$' to target the correct job post
                    "student_id": student_id,
                    "desc": desc,     
                }
            }
        }
            
        result = mongo.db.business.update_one(jobposts_filter, update_operation)
    
    # Query the student's record by student_id to get industry preferences
    student = mongo.db.students.find_one({"student_id": student_id})
    if not student:
        return redirect(url_for('main.student_login'))  # or handle as necessary
    
    # Query all businesses and their job posts
    businesses = mongo.db.business.find()
    
    job_posts = []
    
    # Filter job posts based on student's industry preference
    for business in businesses:
        for jobpost in business["jobposts"]:
            if any(response["student_id"] == student_id for response in jobpost.get("responses", [])):
                continue
            
            if jobpost["industry"] in student["industry_preference"]:
                jobpost["business"] = business["bname"]
                
                job_posts.append(jobpost)
    
    return render_template('jobsearcher.html', jobposts=job_posts)

@main.route('/post_response', methods=['GET', 'POST'])
def post_response():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))
    
    email = session["business_id"]
    
    if request.method == 'POST':  # When the request is a POST (e.g., from the fetch in JavaScript)
        post = request.json  # Get post_id from the request
        
        # Replace with your collection name
        collection = mongo.db.business  
        student_collection = mongo.db.students
        
        student_records = student_collection.find()
        business = collection.find_one({"email": email})  # Fetch the business for the session user
        
        if not business:
            return {"error": "Business not found"}, 404
        
        # Locate the jobpost with the provided post_id
        jobpost = next(
            (jp for jp in business.get("jobposts", []) if jp["post_id"] == post["post_id"]), 
            None
        )
        
        if not jobpost:
            return {"error": "Job post not found"}, 404

        # Extract responses and match with students
        student_responses = []
        for response in jobpost.get("responses", []):
            saved_student = False  # Initialize saved_student for each response
            for savedstudents in business.get("savedstudents", []):  # Ensure to use .get() to avoid KeyError
                if savedstudents.get("student_id") == response["student_id"]:
                    saved_student = True
                    break  # Exit the loop early if a match is found
            
            student = student_collection.find_one({"student_id": response["student_id"]})
            if student:
                student_copy = student.copy()
                student_copy["saved"] = "yes" if saved_student else "no"
                student_copy["response"] = response.get("desc", "No description provided")
                student_responses.append(student_copy)
        
        # Render the target page with the passed data
        return render_template('post_response.html', post_id=post['post_id'], students=student_responses)
    
    elif request.method == 'GET':  # When the request is a GET (e.g., when the page URL is directly visited)
        post_id = request.args.get('post_id')  # Get the post_id from the query parameter
        
        if not post_id:
            return {"error": "Missing post_id"}, 400  # Bad request if post_id is missing
        
        # Fetch the necessary data for the given post_id (similar to POST logic)
        collection = mongo.db.business  
        student_collection = mongo.db.students
        business = collection.find_one({"email": session["business_id"]})
        
        if not business:
            return {"error": "Business not found"}, 404
        
        jobpost = next(
            (jp for jp in business.get("jobposts", []) if jp["post_id"] == post_id), 
            None
        )
        print(jobpost)
        
        if not jobpost:
            return {"error": "Job post not found"}, 404

        # Extract responses and match with students (similar to POST logic)
        student_responses = []
        for response in jobpost.get("responses", []):
            saved_student = False
            
            for savedstudents in business.get("savedstudents", []):  # Ensure to use .get() to avoid KeyError
                if savedstudents.get("student_id") == response["student_id"]:
                    saved_student = True
                    break
            
            student = student_collection.find_one({"student_id": response["student_id"]})
            if student:
                student_copy = student.copy()
                student_copy["saved"] = "yes" if saved_student else "no"
                student_copy["response"] = response.get("desc", "No description provided")
                student_responses.append(student_copy)
        
        # Render the target page with the passed data
        return render_template('post_response.html', post_id=post_id, students=student_responses, industries = Industries, jobpost = jobpost)
    
    return {"error": "Invalid request method"}, 400  # Bad request if method is neither GET nor POST


@main.route('/post_edit', methods=['POST'])
def post_edit():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))
    
    # Collect the form data
    post_id = request.form.get("post_id")  # Use .get() to avoid KeyError
    title = request.form.get('jobtitle')
    industry = request.form.get('Industry')
    state = request.form.get('state')
    city = request.form.get('city')
    desc = request.form.get('textarea')
    c_date = str(date.today())
    
    if not post_id:
        return {"error": "Missing post_id"}, 400  # Handle missing post_id gracefully

    # Debugging: Print the values
    print(f"Post ID: {post_id}, Title: {title}, Industry: {industry}, State: {state}, City: {city}, Desc: {desc}")

    # Update MongoDB with the job post data
    business_filter = {"email": session["business_id"], "jobposts.post_id": post_id}
    update_operation = {
        "$set": {
            "jobposts.$.title": title,
            "jobposts.$.industry": industry,
            "jobposts.$.state": state,
            "jobposts.$.city": city,
            "jobposts.$.description": desc,
            "jobposts.$.date": c_date,
        }
    }
    result = mongo.db.business.update_one(business_filter, update_operation)

    if result.modified_count == 0:
        return {"error": "Failed to update post"}, 400

    return redirect(url_for('main.post_response', post_id=post_id))

@main.route('/post_delete', methods=['POST'])
def post_delete():
    if 'business_id' not in session:
        return redirect(url_for('main.business_login'))
    
    post = request.json
    post_id = post["post_id"]
    
    business_filter = {"email": session["business_id"], "jobposts.post_id": post_id}
    update_operation = {
        "$pull": {
            "jobposts": {"post_id": post_id}  # Match the post_id to remove the job post
        }
    }
    
    # Perform the update operation
    result = mongo.db.business.update_one(business_filter, update_operation)
    
    if result.modified_count > 0:
        return {"message": "Post deleted successfully"}, 200
    else:
        return {"error": "Post not found or deletion failed"}, 404


@main.route('/edit_student', methods=['GET', 'POST'])
def edit_student():
    if 'student_id' not in session:
        return redirect(url_for('main.student_login'))
    
    student_id = session["student_id"]
    student = mongo.db.students.find_one({"student_id": student_id})
    
    if request.method == 'POST':
        # Get form data
        active = request.form['active']
        fname = request.form['fname']
        lname = request.form['Lname']
        phone = request.form['phone']
        address = request.form['address']
        state = request.form['state']
        city = request.form['city']
        zip_code = request.form['zip']  # Avoid conflict with Python's zip
        ato = request.form['ATO']
        uniname = request.form['uniname']
        degree = request.form['degree']
        yearofstudy = request.form['yearffstudy']
        citywork = request.form['citywork']
        relocation = request.form['relocation']
        industry_preference = request.form.getlist('industryPreference[]')
        skills = request.form['skills']
        certifications = request.form['certifications']
        linkedin = request.form['linkedin']
        
        # Handle profile picture
        pfpfile = request.files.get('pfpfile')
        if pfpfile and allowed_file(pfpfile.filename):
            # Check if file size is within limit
            if len(pfpfile.read()) > MAX_CONTENT_LENGTH:
                flash('Profile picture is too large. Maximum size is 5 MB.', 'danger')
                return redirect(request.url)  # Redirect back to the form
            
            pfpfile.seek(0)  # Reset the file pointer after reading the size
            filename = f"{student_id}_{secure_filename(pfpfile.filename)}"
            pfpfilepath = os.path.join(UPLOAD_FOLDER, filename)
            pfpfile.save(pfpfilepath)
        else:
            filename = student.get('pfpfile', '')  # Use existing file if no new file uploaded

        # Handle resume file (optional)
        resumefile = request.files.get('resumefile')
        if resumefile and allowed_file_pdf(resumefile.filename):
            # Check if file size is within limit
            if len(resumefile.read()) > MAX_CONTENT_LENGTH:
                flash('Resume is too large. Maximum size is 5 MB.', 'danger')
                return redirect(request.url)  # Redirect back to the form
            
            resumefile.seek(0)  # Reset the file pointer after reading the size
            resumefilename = f"{student_id}_{secure_filename(resumefile.filename)}"
            resumefilepath = os.path.join(UPLOAD_FOLDER_RESUME, resumefilename)
            resumefile.save(resumefilepath)
        else:
            resumefilename = student.get('resumefile', '')

        # Update the student document
        student_data = {
            "status": active,
            "fname": fname,
            "lname": lname,
            "pfpfile": filename,
            "resumefile": resumefilename,
            "phone": phone,
            "address": address,
            "state": state,
            "city": city,
            "zip": zip_code,
            "ato": ato,
            "uniname": uniname,
            "degree": degree,
            "year_of_study": yearofstudy,
            "city_work": citywork,
            "relocation": relocation,
            "industry_preference": industry_preference,
            "skills": skills,
            "certifications": certifications,
            "linkedin": linkedin
        }

        # Update the student document in MongoDB
        mongo.db.students.update_one(
            {"student_id": student_id},  # Query to find the document
            {"$set": student_data}       # Data to update
        )

        flash("Student data updated successfully!", "success")
        return redirect(url_for('main.student_dashboard'))
    
    return render_template('edit_student.html', student=student, unis=University, Industry=Industries)

@main.route('/delete_student', methods=['POST'])
def delete_student():
    if 'student_id' not in session:
        return redirect(url_for('main.student_login'))
    
    print("hello")
    
    pullstudent = request.json
    pullstudent_id = pullstudent["student_id"]

    # Ensure `student_id` is a unique field, not an array
    result = mongo.db.students.delete_one({"student_id": pullstudent_id})

    if result.deleted_count > 0:
        return {"message": "Student deleted successfully"}, 200
    else:
        return {"error": "Student not found or deletion failed"}, 404
    

@main.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['inputPassword5']
        
        collection = mongo.db.admin  # Replace with your collection name
        records = collection.find()
    
        found = False
        for record in records:
            if record["username"] == username and check_password_hash(record['password'], password):
                session['username'] = record['username']
                print("logged in")
                return redirect(url_for('main.admin_dashboard')) 
            
        else:    
            return render_template("admin_login.html", login = False)
        
        
    return render_template('admin_login.html', login = True)

@main.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('main.home'))
    
            
    student_collection = mongo.db.students  # Replace with your collection name
    student_records = student_collection.find()
    
    business_collection = mongo.db.business  # Replace with your collection name
    business_records = business_collection.find()
    
    
    return render_template('admin_dashboard.html', students = student_records, businesses = business_records)

@main.route('/admin_add_business', methods=['GET', 'POST'])
def admin_add_business():
        if 'username' not in session:
            return redirect(url_for('main.home'))
        
        c_date = str(date.today()) 
        
        bname = request.form['bname']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        industry = request.form['industry']
        location = request.form['Location']
        description = request.form['Description']
        
        collection = mongo.db.business  # Replace with your collection name
        records = collection.find()
        
        for record in records:
            if record["email"].lower() == email.lower():
                return redirect(url_for('main.admin_dashboard'))  
        
        business_data = {
            "account_status": "unlocked",
            "login_attempt": 0,
            "bname": bname,
            "email": email,
            "password": password,
            "industry": industry,
            "location": location,
            "description": description,
            "jobposts": [],
            "savedstudents": [],
            "currentstudents": [],
            "last_login": c_date,
        }       
        
        mongo.db.business.insert_one(business_data) 
        return redirect(url_for('main.admin_dashboard')) 

@main.route('/admin_edit_student', methods=['GET', 'POST'])        
def admin_edit_student():
    if 'username' not in session:
        return redirect(url_for('main.home'))
    
    student_id = request.args.get('student_id')
    student = mongo.db.students.find_one({"student_id": student_id})
    
    if request.method == 'POST':
        # Get form data
        active = request.form['active']
        fname = request.form['fname']
        lname = request.form['Lname']
        phone = request.form['phone']
        address = request.form['address']
        state = request.form['state']
        city = request.form['city']
        zip_code = request.form['zip']  # Avoid conflict with Python's zip
        ato = request.form['ATO']
        uniname = request.form['uniname']
        degree = request.form['degree']
        yearofstudy = request.form['yearffstudy']
        citywork = request.form['citywork']
        relocation = request.form['relocation']
        industry_preference = request.form.getlist('industryPreference[]')
        skills = request.form['skills']
        certifications = request.form['certifications']
        linkedin = request.form['linkedin']
        
        # Handle profile picture
        pfpfile = request.files.get('pfpfile')
        if pfpfile and allowed_file(pfpfile.filename):
            # Check if file size is within limit
            if len(pfpfile.read()) > MAX_CONTENT_LENGTH:
                flash('Profile picture is too large. Maximum size is 5 MB.', 'danger')
                return redirect(request.url)  # Redirect back to the form
            
            pfpfile.seek(0)  # Reset the file pointer after reading the size
            filename = f"{student_id}_{secure_filename(pfpfile.filename)}"
            pfpfilepath = os.path.join(UPLOAD_FOLDER, filename)
            pfpfile.save(pfpfilepath)
        else:
            filename = student.get('pfpfile', '')  # Use existing file if no new file uploaded

        # Handle resume file (optional)
        resumefile = request.files.get('resumefile')
        if resumefile and allowed_file_pdf(resumefile.filename):
            # Check if file size is within limit
            if len(resumefile.read()) > MAX_CONTENT_LENGTH:
                flash('Resume is too large. Maximum size is 5 MB.', 'danger')
                return redirect(request.url)  # Redirect back to the form
            
            resumefile.seek(0)  # Reset the file pointer after reading the size
            resumefilename = f"{student_id}_{secure_filename(resumefile.filename)}"
            resumefilepath = os.path.join(UPLOAD_FOLDER_RESUME, resumefilename)
            resumefile.save(resumefilepath)
        else:
            resumefilename = student.get('resumefile', '')

        # Update the student document
        student_data = {
            "status": active,
            "fname": fname,
            "lname": lname,
            "pfpfile": filename,
            "resumefile": resumefilename,
            "phone": phone,
            "address": address,
            "state": state,
            "city": city,
            "zip": zip_code,
            "ato": ato,
            "uniname": uniname,
            "degree": degree,
            "year_of_study": yearofstudy,
            "city_work": citywork,
            "relocation": relocation,
            "industry_preference": industry_preference,
            "skills": skills,
            "certifications": certifications,
            "linkedin": linkedin
        }

        # Update the student document in MongoDB
        mongo.db.students.update_one(
            {"student_id": student_id},  # Query to find the document
            {"$set": student_data}       # Data to update
        )

        flash("Student data updated successfully!", "success")
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_edit_student.html', student=student, unis=University, Industry=Industries)


@main.route('/admin_delete_student', methods=['POST'])
def admin_delete_student():
    if 'username' not in session:
        return redirect(url_for('main.home'))
    
    print("hello")
    
    student_id = request.form['student_id']

    # Ensure `student_id` is a unique field, not an array
    result = mongo.db.students.delete_one({"student_id": student_id})

    if result.deleted_count > 0:
        return redirect(url_for('main.admin_dashboard'))
    else:
        return {"error": "Student not found or deletion failed"}, 404
    
    
@main.route('/admin_delete_business', methods=['POST'])
def admin_delete_business():
    if 'username' not in session:
        return redirect(url_for('main.home'))
    
    busemail = request.form['busemail']

    # Ensure `student_id` is a unique field, not an array
    result = mongo.db.business.delete_one({"email": busemail})

    if result.deleted_count > 0:
        return redirect(url_for('main.admin_dashboard'))
    else:
        return {"error": "Student not found or deletion failed"}, 404    
    

@main.route('/admin_pause_student', methods=['POST'])
def admin_pause_student():
    if 'username' not in session:
        return redirect(url_for('main.home'))
    
    # Get the list of student_ids from the request JSON
    students = request.json
    
    for student_id in students:
        print(f"Pausing student with ID: {student_id}")
        
        # Find the student by their student_id and update their status to "paused"
        result = mongo.db.students.update_one(
            {"student_id": student_id},  # Find the student by student_id
            {"$set": {"status": "paused"}}  # Update the status to "paused"
        )
        
        # Check if the student was found and the update was successful
        if result.matched_count > 0:
            print(f"Student {student_id} paused successfully.")
        else:
            print(f"Student {student_id} not found.")
    
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin_edit_business', methods=['GET', 'POST'])        
def admin_edit_business():
    if 'username' not in session:
        return redirect(url_for('main.home'))
    
    
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        bname = request.form['bname']
        industry = request.form['industry']
        Location = request.form['Location']
        Description = request.form['Description']

        
        student = mongo.db.students.find_one({"email": email})

        # Update the student document
        business_data = {
            "bname": bname,
            "email": email,
            "industry": industry,
            "location": Location,
            "description": Description,
        }

        # Update the student document in MongoDB
        mongo.db.business.update_one(
            {"email": email},  # Query to find the document
            {"$set": business_data}       # Data to update
        )

        return redirect(url_for('main.admin_dashboard'))


@main.route('/forget_password', methods=['GET', 'POST'])        
def forget_password():
    # Variables to track form submission state
    code_send = request.args.get('code_send', False)
    error = request.args.get('error', False)
    confirm = request.args.get('confirm', False)
    complete = request.args.get('complete', False)
    code = session.get('reset_code', None)
    email = session.get('email', None)
    
    # Render the forgot password page with context
    return render_template('forgotpassword.html', code_send=code_send, error=error, code=code, confirm=confirm, complete = complete)


@main.route('/send_code', methods=['POST'])        
def send_code():
    collection = mongo.db.students  # Replace with your collection name
    bus_collection = mongo.db.business
    email = request.form.get('email')  # Safely get the email from form
    random_combination = random.randint(1000000, 9999999)
    
    # Iterate over student records to find a match
    for student in collection.find():
        if student["email"] == email:
            session['reset_code'] = random_combination
            session['email'] = email
            session['database'] = "student"
            print(random_combination)
            reset_password_code(student["email"], student["fname"], student["lname"], random_combination)
            return redirect(url_for('main.forget_password', code_send=True))
    
    for business in bus_collection.find():
        if business["email"] == email:
            session['reset_code'] = random_combination
            session['email'] = email
            session['database'] = "business"
            print(random_combination)
            reset_password_code(business["email"], business["bname"], "", random_combination)
            return redirect(url_for('main.forget_password', code_send=True))
    
    
    # If no match, redirect with an error flag
    return redirect(url_for('main.forget_password', error=True))


@main.route('/check_code', methods=['POST'])        
def check_code():
    
    if 'email' not in session:
        return redirect(url_for('main.forget_password'))
    
    email = session["email"]
    code = session["reset_code"]
    print(code)
    
    usercode = request.form.get('code')
    if str(code) == usercode: 
        print("you got through!")
        return redirect(url_for('main.forget_password', confirm=True))
        
    else:
        return redirect(url_for('main.forget_password', error=True, code_send=True))
    
    
@main.route('/change_password', methods=['POST'])        
def change_password():
    
    if 'email' not in session:
        return redirect(url_for('main.forget_password'))
    
    email = session["email"]
    
    password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
    
    if session["database"] == "student":
        student_data = {
            "password": password,
        }

        # Update the student document in MongoDB
        mongo.db.students.update_one(
            {"email": email},  # Query to find the document
            {"$set": student_data}       # Data to update
        )

        return redirect(url_for('main.forget_password', complete = True))
    
    else:
        business_data = {
            "password": password,
        }

        # Update the student document in MongoDB
        mongo.db.business.update_one(
            {"email": email},  # Query to find the document
            {"$set": business_data}       # Data to update
        )

        return redirect(url_for('main.forget_password', complete = True))
    


@main.app_errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@main.app_errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large. Maximum size is 5 MB.", 'danger')
    return redirect(request.url)


@main.route('/contact', methods=['POST','GET'])        
def contact():
    if request.method == 'POST':
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form['email']
        message = request.form['message'] 
        
        response = contact_email(email, fname, lname, message)
        print(response)
        return render_template("contact.html", sent = "yes")
    
    
    return render_template("contact.html", sent = "no")

@main.route('/about', methods=['POST','GET'])        
def about():
    return render_template("about.html", sent = "no")
