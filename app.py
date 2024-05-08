from flask import Flask, render_template, jsonify,redirect, url_for, request ,send_file ,session, Response
import cv2
import json
import os
import face_recognition
import numpy as np
import utils

app = Flask(__name__)


app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a session key

with open("details.json", "r") as jf:
    data = json.load(jf)


@app.route('/', methods=['GET', 'POST'])
def login():
  
    if request.method == 'POST':
        global latitude 
        global longitude

        email = request.form['email']
        password = request.form['password']
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        print('user'+email+ "password" +password )
        print(latitude, longitude)

        # set this to true if user is admin
        session['is_admin'] = False

        if email in data["login"]["admin"].keys():
            session['is_admin'] = True
            if data["login"]["admin"][email] == password:
                return redirect(url_for('dashboard'))

        elif email in data["login"]["user"].keys():
            if data["login"]["user"][email] == password:
                return redirect(url_for('newReport'))

        # if(session.get('is_admin')):
        #     return redirect(url_for('dashboard'))
        # else:
        #     return redirect(url_for('newReport'))

        
    return render_template('Login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirm-password']

        print('user'+email+ "password" +password +'confirmPassword'+confirmPassword )

        with open("details.json", 'w') as jf:
            data["login"]["user"][email] = password
            json.dump(data, jf)

        return redirect(url_for('login'))
    
    return render_template('Signup.html')


@app.route('/new-report', methods=['GET','POST'])
def newReport():
    
    if session.get('is_admin'):     #admin cannot access
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        dob = request.form['dob']
        gender = request.form['gender']
        suspectedLocation = request.form['suspectedLocation']
        lastDate = request.form['lastDate']
        number = request.form['number']
        photo = request.files['photo']
        

        # print('user :'+email+ "name: "+name+ " dob : "+dob)
        if photo:
            photo.save(f"./static/assets/{number}.png")
                       
        report_details = {
            "name": name, "email": email, "dob": dob, "gender": gender, "suspectedLocation": suspectedLocation, "lastDate": lastDate,
            "number": number, "photo": f"./static/assets/{number}.png"
        }

        with open("details.json", "w") as jfd:
            data["missing_details"][number] = report_details
            json.dump(data, jfd)

        utils.encode(f"./static/assets/{number}.png", number)

        response_data = {'success': True}

        return jsonify(response_data)

    return render_template('NewReport.html')


@app.route('/dashboard', methods=['GET','POST'])
def dashboard():

    if not session.get('is_admin'):             #return if not admin
        return redirect(url_for('login'))
    
    dashboard_data = get_dashboard_data()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        
        return jsonify({'dashboard_data': dashboard_data})


    return render_template('Dashboard.html', dashboard_data=dashboard_data)


def get_dashboard_data():
    #sample data
    return {
        'admin': list(data['login']['admin'].keys())[0],
        'location': 'Location',
        'total_population': 9989899,
        'missing_cases_received': len(data["missing_details"]),
        'missing_cases_solved': len(data["missing_details"])-len(os.listdir('./data')),
        'cases_pending': len(data["missing_details"]),
        'most_vulnerable_zone': 'TTK Road',
        'least_vulnerable_zone': 'Anjugam Nagar'
    }


@app.route('/complaints', methods=['GET', 'POST'])
def complaints():

    if not session.get('is_admin'):         #return if not admin
        return redirect(url_for('login'))
    
    complaints_data = get_complaints_data()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        print('Returning JSON:', complaints_data)
        return jsonify({'complaints_data': complaints_data})

    print('Rendering HTML:', complaints_data)
    return render_template('Complaints.html', complaints_data=complaints_data)


def get_complaints_data():
    #sample data
    return list(data['missing_details'].values())



@app.route('/past-report', methods=['GET','POST'])
def pastReport():
    
    if session.get('is_admin'):     #admin cannot access
        return redirect(url_for('dashboard'))
    
    past_reports_data = get_complaints_data()

    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        
        return jsonify({'past_reports': past_reports_data})


    return render_template('PastReport.html', past_reports=past_reports_data)




@app.route('/complaint-details', methods=['GET','POST'])
def complaintDetails():

    if not session.get('is_admin'):         #return if not admin
        return redirect(url_for('login'))
    

    complaint_detail = get_single_complaint_data()

    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'complaint_detail': complaint_detail})


    return render_template('SingleComplaint.html', complaint_detail=complaint_detail)


def get_single_complaint_data():
#for testing
    return {
            'name': 'Ajay Shrivastava',
            'dob': '10-09-1991',
            'gender': 'Male',
            'suspected_location': 'Near Adarsh Nagar, New Delhi',
            'last_date': '10-07-2023',
            'contact_number': '9898873233',
            'contact_email': 'rahul@gmail.com'
        }


def generate_utils(file_path):
    print(latitude, longitude)
    lat, lng = float(latitude), float(longitude)
    res = ""
    if target_data:
        res = utils.create_map(target_data, lat, lng)
        utils.send_email(target_data['email'], target_data['name'], file_path, res)

    return res



@app.route('/notifications', methods=['GET','POST'])
def notifications():

    if not session.get('is_admin'):         #return if not admin
        return redirect(url_for('login'))
    
    response= { "name" : "Police Station" , "address":"Chetpet, Chennai" , "distance" :"2.3 KM" , "map": ""}
    
    #map to be replace with actual map
    try:
        return render_template('Notify.html', response=res)#res
    except:
        return render_template('Notify.html', response={})


@app.route('/live')
def live():

    if not session.get('is_admin'):         #return if not admin
        return redirect(url_for('login'))
    

    return render_template('Live.html')
    

def capture_video():

    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break 
        
        with open('encodings.json') as json_file:
            json_data = json.load(json_file)
            
        known_encodings = json_data['encodings']
        known_faces = json_data['ids']
        
        face_recognition.tolerance = 0.85

        imgS = cv2.resize(frame,(0,0),None,0.25,0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        
        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
        
        for encodeFace,faceLoc in zip(encodesCurFrame,facesCurFrame):
            matches = face_recognition.compare_faces(known_encodings, encodeFace)
            faceDis = face_recognition.face_distance(known_encodings, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = known_faces[matchIndex].upper()
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                cv2.rectangle(frame, (x1,y2-35), (x2,y2), (0,255,0), cv2.FILLED)
                cv2.putText(frame,name, (x1+6,y2-6), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255), 2)

                global target_data, res
                target_data = data['missing_details'][name]

                if target_data['email'] not in data['sent']:
                    file_path = f'./data/{target_data["name"]}_ann.png'
                    stat_file_path = './static/assets/image.png'
                    cv2.imwrite(file_path, frame)
                    cv2.imwrite(stat_file_path, frame)
                    res = generate_utils(file_path)
                    data['sent'].append(target_data['email'])
                

        # Encode the frame to JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)

        if not ret:
            print("Error: Could not encode frame.")
            break

        # Convert the JPEG frame to bytes
        frame_bytes = jpeg.tobytes()

        # Yield the frame bytes with the appropriate boundary
        yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result



@app.route('/video_feed')
def video_feed():
    return Response(capture_video(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    app.run(debug=True)