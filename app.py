from flask import Flask, render_template, url_for, request, session, redirect, flash, Response, jsonify, make_response
from dbhelper import *
import cv2
import time
app = Flask(__name__)
app.secret_key = 'secret'

app.config["SECRET_KEY"] = "secret"



bool = False
attendance_id = ''

@app.route('/')
def index():
    global attendance_id, bool
    attendance_id = ''
    bool = False
    data: list = getprocess("SELECT idno FROM students;")
    idnos: list = []
    for fields in data:
        idnos.append(fields[0])
    
    return render_template('home.html', idnos=idnos)

@app.route('/getIdnos', methods=['GET'])
def get_idnos():
    data: list = getprocess("SELECT idno FROM students;")
    idnos: list = []
    for fields in data:
        idnos.append(fields[0])
    return jsonify(idnos)

@app.route('/sse')
def sse():
    def event_stream():
        global attendance_id
        global bool
        while True:
            if bool and attendance_id:
                yield 'event: message\n'
                yield 'data: {}\n\n'.format(attendance_id)
                bool = False
                attendance_id = ''
            time.sleep(1)

    return Response(event_stream(), mimetype='text/event-stream')

def gen_frames():
    global bool
    global attendance_id
    data: list = getprocess("SELECT idno FROM students;")
    idnos: list = []
    for fields in data:
        idnos.append(fields[0])
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    qcd = cv2.QRCodeDetector()
    while True:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)  # Flip the frame horizontally
            ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
            if ret_qr:
                for s, p in zip(decoded_info, points):
                    if s:
                        print(s)
                        attendance_id = s
                        bool = True
                        color = (0, 255, 0)
                    else:
                        color = (0, 0, 255)
                    frame = cv2.polylines(frame, [p.astype(int)], True, color, 8)
            ret, jpeg = cv2.imencode('.png', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/png\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            if bool:
                if attendance_id in idnos:
                    cap.release() # Reset attendance_id if not in idnos
            
                
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/admin')
def admin():
    if is_logged_in():
        return redirect(url_for('list'))
    data: list = getprocess("SELECT username,password FROM users;")
    usernames : list = []
    passwords : list = []
    for fields in data:
        usernames.append(fields[0])
        passwords.append(fields[1])
    return render_template('login.html',usernames=usernames,passwords=passwords)

@app.route('/logout', methods=['POST'])
def logout():
    session["logged_in"] = False
    return redirect(url_for('admin'))

@app.route('/admin-login', methods=['POST'])
def admin_login():
    username = request.json['username']
    password = request.json['password']
    print("asda")
    data: list = getprocess("SELECT username,password FROM users WHERE username = '"+username+"' AND password = '"+password+"';")
    if data:
        session["logged_in"] = True

        return jsonify({'message': 'Login successful', 'redirect_url': '/list'})
    else:
        return redirect(url_for('admin'))

def is_logged_in():
    return session.get('logged_in', False)

@app.route('/add')
def add():
    if not is_logged_in():
        return redirect(url_for('admin'))
    data: list = getprocess("SELECT idno FROM students;")
    idnos: list = []
    for fields in data:
        idnos.append(fields[0])
    return render_template('index.html', idnos=idnos)


@app.route('/addAttendance', methods=['POST'])
def add_attendance():
    idno = request.json['idno']
    lastname = request.json['lastname']
    firstname = request.json['firstname']
    course = request.json['course']
    level = request.json['level']
    log = request.json['log']

    print("INSERT INTO attendance (idno,lastname,firstname,course,level,log) VALUES ('"+idno+"','"+lastname+"','"+firstname+"','"+course+"','"+level+"','"+log+"');")
    postprocess("INSERT INTO attendance (idno,lastname,firstname,course,level,log) VALUES ('"+idno+"','"+lastname+"','"+firstname+"','"+course+"','"+level+"','"+log+"');")

    return jsonify({'message': 'Attendance added successfully'})

@app.route('/getstudentinfo', methods=['GET'])
def get_student_info():
    idno = request.args.get('idno')
    data: list = getprocess("SELECT idno,lastname,firstname,course,level,image FROM students WHERE idno = '"+idno+"';")
    student = {'idno': data[0][0], 'lastname': data[0][1], 'firstname': data[0][2], 'course': data[0][3], 'level': data[0][4], 'image': data[0][5]}
    print(student)
    return jsonify(student)

@app.route('/save', methods=['POST'])
def save():
    idno = request.form['idnoentered'] 
    lastname = request.form['lastnameentered'] 
    firstname = request.form['firstnameentered'] 
    course = request.form['courseentered'] 
    level = request.form['levelentered'] 
    image = 'static/images/'+idno+'.jpg'
    if not idno or not lastname or not firstname or not course or not level:
        flash('All fields are required!')
        return redirect(url_for('index'))
    postprocess("INSERT INTO students (idno,lastname,firstname,course,level,image) VALUES ('"+idno+"','"+lastname+"','"+firstname+"','"+course+"','"+level+"','"+image+"');")
    flash('Student record added successfully!')
    return redirect(url_for('add'))

@app.route('/saveimage', methods=['POST'])
def saveimage():
    image = request.files['webcam'] 
    idno = request.args.get('idno')
    image.save('static/images/'+idno+'.jpg')
    return redirect(url_for('add'))

@app.route('/list')
def list():
    if not is_logged_in():
        return redirect(url_for('admin'))
    data: list = getprocess("SELECT idno,lastname,firstname,course,level,image FROM students;")
    return render_template('list.html',students=data)

@app.route('/deletestudent', methods=['POST'])
def deletestudent():
    idno = request.args.get('idno')
    postprocess("DELETE FROM students WHERE idno = '"+idno+"';")
    flash('Student record deleted successfully!')
    return redirect(url_for('list'))


@app.route('/attendance')
def attendance():
    if not is_logged_in():
        return redirect(url_for('admin'))
    attendance = getprocess("SELECT * FROM attendance;")
    return render_template('attendance.html', attendance=attendance)

@app.route('/editstudent', methods=['POST'])
def editstudent():
    previousidno = request.json['previousidno']
    idno = request.json['idno']
    lastname = request.json['lastname']
    firstname = request.json['firstname']
    course = request.json['course']
    level = request.json['level']
    image = 'static/images/'+idno+'.jpg'


    print(previousidno)
    print(idno)
    if previousidno is idno:
        postprocess("UPDATE students SET lastname = '"+lastname+"', firstname = '"+firstname+"', course = '"+course+"', level = '"+level+"' WHERE idno = '"+previousidno+"';")
        return redirect(url_for('list'))
    
    postprocess("UPDATE students SET idno = '"+idno+"', lastname = '"+lastname+"', firstname = '"+firstname+"', course = '"+course+"', level = '"+level+"', image = '"+image+"' WHERE idno = '"+previousidno+"';")
    return redirect(url_for('list'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')