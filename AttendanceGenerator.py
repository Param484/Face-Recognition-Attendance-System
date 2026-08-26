import openpyxl
from pymongo import MongoClient
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from dotenv import load_dotenv
import os

# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")

client = MongoClient(MONGODB_CONNECTION_STRING)
db = client["attendance_system"]
students_collection = db["students"]


# ============================================================
# REPORT GENERATION
# ============================================================

def generate_attendance_report(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Attendance Report"

    sheet.append([
        "Date",
        "Student ID",
        "Name",
        "Major",
        "Year",
        "Attendance Status",
        "Attendance Time"
    ])

    current_date = start_date

    while current_date <= end_date:
        start_of_day = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            0, 0, 0
        )

        end_of_day = datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            23, 59, 59
        )

        students = students_collection.find()

        for student in students:
            attendance_status = "absent"
            attendance_time_str = "00:00:00"

            last_attendance_time_str = student.get(
                "last_attendance_time",
                ""
            )

            if last_attendance_time_str:
                try:
                    attendance_time = datetime.strptime(
                        last_attendance_time_str,
                        "%Y-%m-%d %H:%M:%S"
                    )

                    if start_of_day <= attendance_time <= end_of_day:
                        attendance_status = "present"
                        attendance_time_str = attendance_time.strftime(
                            "%H:%M:%S"
                        )

                except (ValueError, TypeError):
                    pass

            sheet.append([
                current_date.strftime("%Y-%m-%d"),
                student["_id"],
                student.get("name", ""),
                student.get("major", ""),
                student.get("year", ""),
                attendance_status,
                attendance_time_str
            ])

        current_date += timedelta(days=1)

    report_filename = (
        f"attendance_report_{start_date_str}_to_{end_date_str}.xlsx"
    )

    wb.save(report_filename)

    messagebox.showinfo(
        "Success",
        f"Attendance report generated successfully:\n{report_filename}"
    )


# ============================================================
# GUI
# ============================================================

def show_gui():
    window = tk.Tk()
    window.title("Attendance Report Generator")
    window.geometry("350x280")
    window.config(bg="#6f50f8")
    window.resizable(False, False)

    tk.Label(
        window,
        text="Attendance Report",
        font=("Arial", 18, "bold"),
        bg="#6f50f8"
    ).pack(pady=15)

    tk.Label(
        window,
        text="Start Date:",
        bg="#6f50f8"
    ).pack()

    entry_start_date = DateEntry(
        window,
        width=18,
        background="darkblue",
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd"
    )
    entry_start_date.pack(pady=5)

    tk.Label(
        window,
        text="End Date:",
        bg="#6f50f8"
    ).pack()

    entry_end_date = DateEntry(
        window,
        width=18,
        background="darkblue",
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd"
    )
    entry_end_date.pack(pady=5)

    def on_generate_report():
        start_date = entry_start_date.get().strip()
        end_date = entry_end_date.get().strip()

        today = datetime.today().date()

        try:
            start_date_obj = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()

            end_date_obj = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()

            if start_date_obj > today or end_date_obj > today:
                messagebox.showerror(
                    "Invalid Date",
                    "Start or End Date cannot be in the future."
                )
                return

            if start_date_obj > end_date_obj:
                messagebox.showerror(
                    "Invalid Date",
                    "Start Date cannot be later than End Date."
                )
                return

            generate_attendance_report(
                start_date,
                end_date
            )

            window.destroy()

        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Please enter dates in YYYY-MM-DD format."
            )

    tk.Button(
        window,
        text="Generate Report",
        command=on_generate_report
    ).pack(pady=20)

    window.mainloop()


if __name__ == "__main__":
    show_gui()
