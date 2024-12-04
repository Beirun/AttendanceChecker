from flask import Flask, render_template, url_for, request, redirect, flash, Response
from dbhelper import *
import cv2
import time

app = Flask(__name__)
app.secret_key = 'secret'

bool = False
attendance_id = ''

@app.route('/')
def index():
    data: list = getprocess("SELECT idno FROM students;")
    idnos: list = []
    for fields in data:
        idnos.append(fields[0])
    
    return render_template('home.html', idnos=idnos)


@app.route('/sse')
def sse():
    def event_stream():
        while True:
            if attendance_id:
                yield 'data: {}\n\n'.format(attendance_id)
            time.sleep(1)

    return Response(event_stream(), mimetype='text/event-stream')

def gen_frames():
    global bool
    global attendance_id
    cap = cv2.VideoCapture(0)
    qcd = cv2.QRCodeDetector()
    while True:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)  # Flip the frame horizontally
            ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
            if ret_qr:
                for s, p in zip(decoded_info, points):
                    if s:
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
                cap.release()
                
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/admin')
def admin():
    data: list = getprocess("SELECT username,password FROM users;")
    usernames : list = []
    passwords : list = []
    for fields in data:
        usernames.append(fields[0])
        passwords.append(fields[1])
    return render_template('login.html',usernames=usernames,passwords=passwords)

@app.route('/admin-login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']
    data: list = getprocess("SELECT username,password FROM users WHERE username = '"+username+"' AND password = '"+password+"';")
    if data:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('admin'))

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
    return redirect(url_for('index'))

@app.route('/saveimage', methods=['POST'])
def saveimage():
    image = request.files['webcam'] 
    idno = request.args.get('idno')
    image.save('static/images/'+idno+'.jpg')
    return redirect(url_for('index'))

@app.route('/list')
def list():
    data: list = getprocess("SELECT idno,lastname,firstname,course,level,image FROM students;")
    return render_template('list.html',students=data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')