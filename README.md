# Face Recognition Attendance System

A Python-based face recognition attendance management system that automatically identifies registered students through a webcam and records their attendance in MongoDB.

The project is designed to eliminate manual attendance entry and provide a simple interface for student registration, face recognition, attendance tracking, and report generation.

---

## Features

### 👤 Student Registration
- Register students directly from the main application.
- Enter:
  - Student ID
  - Name
  - Major
- Select an existing student image or capture a new image using the webcam.
- Student information is automatically stored in MongoDB.
- No separate database insertion script is required.

### 🧠 Automatic Face Encoding
- Face encodings are generated automatically during registration.
- Encodings are loaded automatically when the application starts.
- No separate `EncodeGenerator.py` is required.
- Newly registered students can be recognized without manually generating encoding files.

### 📷 Face Recognition
- Uses the computer's webcam for real-time face recognition.
- Recognizes registered students automatically.
- Displays student information after recognition.
- Student information remains visible for approximately 5 seconds.
- Temporary loss of face detection does not immediately remove the recognized student's information.

### 📝 Automatic Attendance
- Attendance is recorded automatically when a registered student is recognized.
- Attendance data is stored in MongoDB.
- The system prevents repeated attendance marking within the configured 24-hour period.

### 📊 Attendance Reports
- Generate attendance reports in Excel format.
- Select start and end dates using a calendar date picker.
- Reports include:
  - Date
  - Student ID
  - Student Name
  - Major
  - Year
  - Attendance Status
  - Attendance Time

### 🔐 Admin Registration
- Student registration is protected by an administrator password.

### 🎥 Camera Controls
- Webcam starts when the **Start** button is selected.
- Press **Q** to close the facial recognition camera.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| OpenCV | Webcam and image processing |
| face_recognition | Face detection and recognition |
| face_recognition_models | Face recognition model data |
| CVZone | OpenCV interface enhancements |
| NumPy | Numerical operations |
| MongoDB | Student and attendance data storage |
| PyMongo | Python connection to MongoDB |
| OpenPyXL | Excel report generation |
| Tkinter | Desktop GUI |
| tkcalendar | Calendar-based date selection |
| python-dotenv | Secure environment variable management |

---
### Main Window

![Main Window](screenshots/https://github.com/Param484/Face-Recognition-Attendance-System/blob/c0bed41f6b915b6c459988dbc524ba95879dea20/Screenshot%202026-08-26%20220751.png)

## Project Structure

```text
Face-Recognition-Attendance-System/
│
├── main.py
├── AttendanceGenerator.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── resources/
│   ├── background.png
│   └── Modes/
│       ├── ...
│       └── ...
│
└── Images/
    └── .gitkeep
## Screenshots



### Student Registration

![Student Registration]((https://github.com/Param484/Face-Recognition-Attendance-System/blob/c0bed41f6b915b6c459988dbc524ba95879dea20/Screenshot%202026-08-26%20221328.png))

### Face Recognition

![Face Recognition]((https://github.com/Param484/Face-Recognition-Attendance-System/blob/a8fd52d7d6ee9e6da741ca68b0b6e20591b99650/Screenshot%20(44).png))

###Attendance Report

![Attendance Report]((https://github.com/Param484/Face-Recognition-Attendance-System/blob/c0bed41f6b915b6c459988dbc524ba95879dea20/Screenshot%202026-08-26%20221347.png))
