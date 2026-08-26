import os
import cv2
import face_recognition
import cvzone
import numpy as np
import tkinter as tk
from tkinter import messagebox, filedialog
from pymongo import MongoClient
from datetime import datetime
import subprocess
import sys
import shutil
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION
# ============================================================
load_dotenv()
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
ADMIN_PASSWORD = "admin123"
ATTENDANCE_COOLDOWN_SECONDS = 5  # 24 hours

# ============================================================
# DATABASE
# ============================================================

client = MongoClient(MONGODB_CONNECTION_STRING)
db = client["attendance_system"]
students_collection = db["students"]

# ============================================================
# GLOBALS
# ============================================================

cap = None
encodeListKnown = []
studentIds = []
imgModeList = []
imgBackgroundTemplate = None


# ============================================================
# LOAD ORIGINAL MODE IMAGES
# ============================================================

def load_mode_images():
    global imgModeList

    folder_mode_path = os.path.join("Resources", "Modes")

    if not os.path.isdir(folder_mode_path):
        print("Warning: Resources/Modes folder was not found.")
        imgModeList = []
        return

    mode_path_list = os.listdir(folder_mode_path)
    imgModeList = []

    for mode_path in mode_path_list:
        image = cv2.imread(os.path.join(folder_mode_path, mode_path))
        if image is not None:
            imgModeList.append(image)

    print(f"Loaded {len(imgModeList)} mode image(s).")


# ============================================================
# FACE ENCODING
# ============================================================

def load_all_face_encodings():
    """
    Automatically creates face encodings from every image in Images/.
    No separate EncodeGenerator.py or EncodeFile.p is required.
    """
    global encodeListKnown, studentIds

    encodeListKnown = []
    studentIds = []

    os.makedirs("Images", exist_ok=True)

    image_files = [
        f for f in os.listdir("Images")
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    for filename in image_files:
        student_id = os.path.splitext(filename)[0]
        image_path = os.path.join("Images", filename)

        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if len(encodings) != 1:
                print(
                    f"Skipping {filename}: expected exactly one face, "
                    f"found {len(encodings)}."
                )
                continue

            encodeListKnown.append(encodings[0])
            studentIds.append(student_id)

        except Exception as e:
            print(f"Could not encode {filename}: {e}")

    print(f"Loaded {len(studentIds)} face encoding(s).")


def add_encoding_to_memory(student_id, image_path):
    """
    Encodes a newly registered student's image immediately.
    This means registration works without restarting the program.
    """
    global encodeListKnown, studentIds

    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) != 1:
        raise ValueError("The registration image must contain exactly one face.")

    # Remove an old encoding if this ID somehow already exists.
    if student_id in studentIds:
        index = studentIds.index(student_id)
        studentIds[index] = student_id
        encodeListKnown[index] = encodings[0]
    else:
        studentIds.append(student_id)
        encodeListKnown.append(encodings[0])


# ============================================================
# REGISTRATION
# ============================================================

def admin_login():
    login_window = tk.Toplevel()
    login_window.title("Admin Login")
    login_window.geometry("300x170")
    login_window.resizable(False, False)

    tk.Label(login_window, text="Enter Admin Password").pack(pady=10)

    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)
    password_entry.focus()

    def verify():
        if password_entry.get() == ADMIN_PASSWORD:
            login_window.destroy()
            open_registration_window()
        else:
            messagebox.showerror("Error", "Wrong Password")

    tk.Button(login_window, text="Login", command=verify).pack(pady=10)


def open_registration_window():
    reg_window = tk.Toplevel()
    reg_window.title("Student Registration")
    reg_window.geometry("450x520")
    reg_window.resizable(False, False)

    total_students = students_collection.count_documents({})

    tk.Label(
        reg_window,
        text=f"Total Registered Students: {total_students}",
        font=("Arial", 12, "bold"),
        fg="blue"
    ).pack(pady=10)

    tk.Label(reg_window, text="Student ID").pack()
    id_entry = tk.Entry(reg_window)
    id_entry.pack()

    tk.Label(reg_window, text="Name").pack()
    name_entry = tk.Entry(reg_window)
    name_entry.pack()

    tk.Label(reg_window, text="Major").pack()
    major_entry = tk.Entry(reg_window)
    major_entry.pack()

    selected_image = tk.StringVar(value="")

    def choose_image():
        file_path = filedialog.askopenfilename(
            title="Select Student Face Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png")]
        )

        if file_path:
            selected_image.set(file_path)

    def capture_from_camera():
        student_id = id_entry.get().strip()

        if not student_id:
            messagebox.showerror("Error", "Enter Student ID first.")
            return

        os.makedirs("Images", exist_ok=True)
        image_path = os.path.join("Images", f"{student_id}.png")

        camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            messagebox.showerror("Camera Error", "Could not open the camera.")
            return

        while True:
            success, frame = camera.read()

            if not success:
                break

            # Show instructions only on the preview.
            # The saved student image remains clean.
            display_frame = frame.copy()

            cv2.putText(
                display_frame,
                "Press SPACE to capture | ESC to cancel",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow("Capture Student Face", display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACE
                cv2.imwrite(image_path, frame)
                selected_image.set(image_path)
                break

            if key == 27:  # ESC
                break

        camera.release()
        cv2.destroyAllWindows()

    tk.Button(
        reg_window,
        text="Choose Existing Image",
        command=choose_image
    ).pack(pady=10)

    tk.Button(
        reg_window,
        text="Capture From Camera",
        command=capture_from_camera
    ).pack(pady=5)

    tk.Label(
        reg_window,
        textvariable=selected_image,
        wraplength=400
    ).pack(pady=5)

    def register_student():
        student_id = id_entry.get().strip()
        name = name_entry.get().strip()
        major = major_entry.get().strip()
        image_path = selected_image.get().strip()

        if not student_id or not name or not major:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        if not image_path or not os.path.exists(image_path):
            messagebox.showerror("Error", "Please choose or capture an image.")
            return

        # Prevent accidental duplicate registration.
        if students_collection.find_one({"_id": student_id}):
            messagebox.showerror(
                "Duplicate Student ID",
                f"Student ID {student_id} is already registered."
            )
            return

        try:
            # Validate that the image contains exactly one face.
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            encodings = face_recognition.face_encodings(image)

            if len(face_locations) != 1 or len(encodings) != 1:
                messagebox.showerror(
                    "Invalid Image",
                    "The image must contain exactly one clearly visible face."
                )
                return

            os.makedirs("Images", exist_ok=True)

            new_image_path = os.path.join("Images", f"{student_id}.png")

            # Save a copy using the Student ID as its filename.
            if os.path.abspath(image_path) != os.path.abspath(new_image_path):
                shutil.copy2(image_path, new_image_path)

            # Add the student directly to MongoDB.
            student_data = {
                "name": name,
                "major": major,
                "starting_year": datetime.now().year,
                "total_attendance": 0,
                "standing": "G",
                "year": 1,
                "last_attendance_time": ""
            }

            students_collection.insert_one({
                "_id": student_id,
                **student_data
            })

            # Add the new face encoding immediately.
            add_encoding_to_memory(student_id, new_image_path)

            messagebox.showinfo(
                "Success",
                f"{name} has been registered successfully.\n\n"
                "The student is ready for face recognition immediately."
            )

            reg_window.destroy()

        except Exception as e:
            messagebox.showerror("Registration Error", str(e))

    tk.Button(
        reg_window,
        text="Register Student",
        command=register_student
    ).pack(pady=20)


# ============================================================
# ATTENDANCE REPORT
# ============================================================

def open_attendance_report():
    """
    Launch the report generator from the main program.
    """
    try:
        subprocess.Popen(
            [sys.executable, os.path.join(os.path.dirname(__file__), "AttendanceGenerator.py")]
        )
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"Failed to open AttendanceGenerator.py:\n{e}"
        )


# ============================================================
# MAIN GUI
# ============================================================

def create_gui():
    window = tk.Tk()
    window.title("Attendance System")
    window.geometry("600x420+100+100")
    window.config(bg="#6f50f8")
    window.resizable(False, False)

    tk.Label(
        window,
        text="Face Recognition Attendance System",
        font=("Arial", 24),
        bg="#6f50f8"
    ).pack(pady=25)

    def show_help():
        messagebox.showinfo(
            "Help",
            "1. Use Registration to register a student.\n"
            "2. Choose an image or capture the student's face.\n"
            "3. The student is automatically added to MongoDB.\n"
            "4. Face encoding is automatically created.\n"
            "5. Press Start to mark attendance.\n"
            "6. Generate Report creates an Excel attendance report."
        )

    def start_face_recognition():
        window.destroy()
        start_face_recognition_operations()

    tk.Button(
        window,
        text="Start",
        font=("Arial", 16),
        command=start_face_recognition
    ).pack(pady=10)

    tk.Button(
        window,
        text="Registration",
        font=("Arial", 16),
        command=admin_login
    ).pack(pady=10)

    tk.Button(
        window,
        text="Generate Report",
        font=("Arial", 16),
        command=open_attendance_report
    ).pack(pady=10)

    tk.Button(
        window,
        text="Help",
        font=("Arial", 16),
        command=show_help
    ).pack(pady=10)

    window.mainloop()


# ============================================================
# THANK YOU PAGE
# ============================================================

def show_thank_you_page():
    thank_you_window = tk.Tk()
    thank_you_window.title("Face Attendance Done!")
    thank_you_window.geometry("400x200")
    thank_you_window.config(bg="#6f50f8")

    tk.Label(
        thank_you_window,
        text="Thank You!",
        font=("Arial", 15),
        bg="#6f50f8"
    ).pack(pady=20)

    tk.Label(
        thank_you_window,
        text="80% of success is showing up!",
        font=("Arial", 20),
        bg="#6f50f8"
    ).pack(pady=20)

    thank_you_window.after(3000, thank_you_window.destroy)
    thank_you_window.mainloop()


# ============================================================
# FACE RECOGNITION
# ============================================================

def start_face_recognition_operations():
    global cap

    if not encodeListKnown:
        messagebox.showwarning(
            "No Students",
            "No valid student face encodings were found.\n"
            "Please register at least one student first."
        )
        create_gui()
        return

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Could not open the camera.")
        create_gui()
        return

    img_background = cv2.imread("Resources/background.png")

    if img_background is None:
        cap.release()
        messagebox.showerror(
            "Resource Error",
            "Resources/background.png could not be found."
        )
        create_gui()
        return

    mode_type = 0
    counter = 0
    student_id = -1
    student_info = None
    img_student = None

    while True:
        success, img = cap.read()

        if not success:
            print("Error reading frame.")
            break

        img_small = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        img_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(img_small)
        face_encodings = face_recognition.face_encodings(
            img_small,
            face_locations
        )

        # Reset the background frame for every loop.
        current_background = img_background.copy()
        current_background[162:162 + 480, 55:55 + 640] = img

        # Original right-side UI from Resources/Modes.
        if imgModeList and 0 <= mode_type < len(imgModeList):
            current_background[
                44:44 + 633,
                808:808 + 414
            ] = imgModeList[mode_type]

        if face_locations:
            for face_encoding, face_location in zip(
                face_encodings,
                face_locations
            ):
                if not encodeListKnown:
                    continue

                matches = face_recognition.compare_faces(
                    encodeListKnown,
                    face_encoding
                )
                face_distances = face_recognition.face_distance(
                    encodeListKnown,
                    face_encoding
                )

                match_index = int(np.argmin(face_distances))

                if matches[match_index]:
                    y1, x2, y2, x1 = face_location
                    y1, x2, y2, x1 = (
                        y1 * 4,
                        x2 * 4,
                        y2 * 4,
                        x1 * 4
                    )

                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

                    current_background = cvzone.cornerRect(
                        current_background,
                        bbox,
                        rt=0
                    )

                    student_id = studentIds[match_index]

                    if counter == 0:
                        cvzone.putTextRect(
                            current_background,
                            "Loading",
                            (275, 400)
                        )
                        counter = 1
                        mode_type = 1

            if counter != 0:
                if counter == 1:
                    student_info = students_collection.find_one(
                        {"_id": student_id}
                    )

                    if student_info is None:
                        print(
                            f"Student with ID {student_id} "
                            "was not found in MongoDB."
                        )
                        counter = 0
                        mode_type = 0
                        continue

                    img_student = cv2.imread(
                        os.path.join("Images", f"{student_id}.png")
                    )

                    last_attendance_time_str = student_info.get(
                        "last_attendance_time",
                        ""
                    )

                    if last_attendance_time_str:
                        try:
                            last_attendance_time = datetime.strptime(
                                last_attendance_time_str,
                                "%Y-%m-%d %H:%M:%S"
                            )

                            seconds_elapsed = (
                                datetime.now() - last_attendance_time
                            ).total_seconds()

                        except ValueError:
                            seconds_elapsed = ATTENDANCE_COOLDOWN_SECONDS + 1

                    else:
                        seconds_elapsed = ATTENDANCE_COOLDOWN_SECONDS + 1

                    if seconds_elapsed > ATTENDANCE_COOLDOWN_SECONDS:
                        now_string = datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                        students_collection.update_one(
                            {"_id": student_id},
                            {
                                "$inc": {"total_attendance": 1},
                                "$set": {
                                    "last_attendance_time": now_string
                                }
                            }
                        )

                        student_info["total_attendance"] = (
                            student_info.get("total_attendance", 0) + 1
                        )
                        student_info["last_attendance_time"] = now_string

                        print(
                            f"Attendance marked for student {student_id}."
                        )

                    else:
                        print(
                            f"Attendance already marked within the "
                            f"last 24 hours for student {student_id}."
                        )
                        mode_type = 3
                        counter = 0

                if mode_type != 3 and student_info:
                    if 10 < counter < 20:
                        mode_type = 2

                    if imgModeList:
                        current_background[
                            44:44 + 633,
                            808:808 + 414
                        ] = imgModeList[mode_type]

                    if counter <= 10:
                        cv2.putText(
                            current_background,
                            str(student_info.get("total_attendance", 0)),
                            (861, 125),
                            cv2.FONT_HERSHEY_COMPLEX,
                            1,
                            (255, 255, 255),
                            1
                        )

                        cv2.putText(
                            current_background,
                            str(student_info.get("major", "")),
                            (1006, 550),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.5,
                            (255, 255, 255),
                            1
                        )

                        cv2.putText(
                            current_background,
                            str(student_id),
                            (1006, 493),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.5,
                            (255, 255, 255),
                            1
                        )

                        cv2.putText(
                            current_background,
                            str(student_info.get("standing", "G")),
                            (910, 625),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.6,
                            (100, 100, 100),
                            1
                        )

                        cv2.putText(
                            current_background,
                            str(student_info.get("year", 1)),
                            (1025, 625),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.6,
                            (100, 100, 100),
                            1
                        )

                        cv2.putText(
                            current_background,
                            str(student_info.get("starting_year", "")),
                            (1125, 625),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.6,
                            (100, 100, 100),
                            1
                        )

                        student_name = str(
                            student_info.get("name", "")
                        )

                        (w, h), _ = cv2.getTextSize(
                            student_name,
                            cv2.FONT_HERSHEY_COMPLEX,
                            1,
                            1
                        )

                        offset = (414 - w) // 2

                        cv2.putText(
                            current_background,
                            student_name,
                            (808 + offset, 445),
                            cv2.FONT_HERSHEY_COMPLEX,
                            1,
                            (50, 50, 50),
                            1
                        )

                        if img_student is not None:
                            try:
                                img_student_resized = cv2.resize(
                                    img_student,
                                    (216, 216)
                                )
                                current_background[
                                    175:175 + 216,
                                    909:909 + 216
                                ] = img_student_resized
                            except Exception:
                                pass

                    counter += 1

                    if counter >= 100:
                        counter = 0
                        mode_type = 0
                        student_info = None
                        img_student = None

        else:
            mode_type = 0
            counter = 0
            student_info = None

        cv2.imshow("Face Attendance", current_background)

        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    show_thank_you_page()


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    load_mode_images()
    load_all_face_encodings()
    create_gui()
