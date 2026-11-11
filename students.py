
import sys
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QFormLayout,
    QComboBox, QSpinBox
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_connection


class StudentsModule(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC - Student Management")
        self.resize(950, 700)
        self.setMinimumSize(800, 600)


        self.setup_ui()
        self.load_faculties()
        self.load_students()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Back button at top
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.setStyleSheet("background-color: #64748B;")
        back_btn.clicked.connect(self.close)
        main_layout.addWidget(back_btn)

        title = QLabel("STUDENT MANAGEMENT")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #183153;"
        )
        main_layout.addWidget(title)

        form_layout = QFormLayout()

        self.student_number = QLineEdit()
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()

        # Faculty dropdown
        self.faculty_combo = QComboBox()
        self.faculty_combo.currentIndexChanged.connect(
            self.load_programmes
        )

        # Programme dropdown
        self.programme_combo = QComboBox()
        self.programme_combo.currentIndexChanged.connect(
            self.load_levels
        )

        # Level dropdown
        self.level_combo = QComboBox()

        # Academic year
        self.academic_year = QSpinBox()
        self.academic_year.setRange(2020, 2100)
        self.academic_year.setValue(datetime.now().year)

        form_layout.addRow("Student Number:", self.student_number)
        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("Faculty:", self.faculty_combo)
        form_layout.addRow("Programme:", self.programme_combo)
        form_layout.addRow("Level:", self.level_combo)
        form_layout.addRow("Academic Year:", self.academic_year)
        form_layout.addRow("Phone:", self.phone)
        form_layout.addRow("Email:", self.email)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()

        save_button = QPushButton("Register Student")
        save_button.clicked.connect(self.register_student)

        clear_button = QPushButton("Clear Fields")
        clear_button.clicked.connect(self.clear_fields)

        button_layout.addWidget(save_button)
        button_layout.addWidget(clear_button)

        main_layout.addLayout(button_layout)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search by student number or name..."
        )
        self.search_box.textChanged.connect(self.search_students)

        main_layout.addWidget(self.search_box)

        self.student_table = QTableWidget()
        self.student_table.setColumnCount(7)

        self.student_table.setHorizontalHeaderLabels([
            "ID", "Student Number", "First Name",
            "Last Name", "Programme", "Phone", "Email"
        ])

        self.student_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.student_table.horizontalHeader().setStretchLastSection(True)

        main_layout.addWidget(self.student_table)

        self.setLayout(main_layout)

    def load_faculties(self):
        connection = get_connection()

        try:
            faculties = connection.execute("""
                SELECT id, faculty_name
                FROM faculties
                ORDER BY faculty_name
            """).fetchall()

            self.faculty_combo.clear()

            for faculty in faculties:
                self.faculty_combo.addItem(
                    faculty["faculty_name"],
                    faculty["id"]
                )

            self.load_programmes()

        finally:
            connection.close()

    def load_programmes(self, *_):
        faculty_id = self.faculty_combo.currentData()

        self.programme_combo.clear()
        self.level_combo.clear()

        if faculty_id is None:
            return

        connection = get_connection()

        try:
            programmes = connection.execute("""
                SELECT DISTINCT programme_name
                FROM programmes
                WHERE faculty_id = ?
                ORDER BY programme_name
            """, (faculty_id,)).fetchall()

            for programme in programmes:
                self.programme_combo.addItem(
                    programme["programme_name"]
                )

            self.load_levels()

        finally:
            connection.close()

    def load_levels(self, *_):
        faculty_id = self.faculty_combo.currentData()
        programme_name = self.programme_combo.currentText()

        self.level_combo.clear()

        if faculty_id is None or not programme_name:
            return

        connection = get_connection()

        try:
            levels = connection.execute("""
                SELECT id, level
                FROM programmes
                WHERE faculty_id = ?
                AND programme_name = ?
                ORDER BY level
            """, (faculty_id, programme_name)).fetchall()

            for item in levels:
                self.level_combo.addItem(
                    item["level"],
                    item["id"]
                )

        finally:
            connection.close()

    def register_student(self):
        student_number = self.student_number.text().strip()
        first_name = self.first_name.text().strip()
        last_name = self.last_name.text().strip()

        faculty_id = self.faculty_combo.currentData()
        programme_name = self.programme_combo.currentText()
        programme_id = self.level_combo.currentData()
        level = self.level_combo.currentText()

        if not student_number or not first_name or not last_name:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Student number, first name and last name are required."
            )
            return

        if faculty_id is None or programme_id is None:
            QMessageBox.warning(
                self,
                "Academic Information Missing",
                "Please select a faculty, programme and level."
            )
            return

        connection = get_connection()

        try:
            connection.execute("""
                INSERT INTO students (
                    student_number,
                    first_name,
                    last_name,
                    programme,
                    phone,
                    email,
                    faculty_id,
                    programme_id,
                    academic_year
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_number,
                first_name,
                last_name,
                f"{programme_name} {level}",
                self.phone.text().strip(),
                self.email.text().strip(),
                faculty_id,
                programme_id,
                self.academic_year.value()
            ))

            connection.commit()

            QMessageBox.information(
                self,
                "Success",
                "Student registered successfully!"
            )

            self.clear_fields()
            self.load_students()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Registration Error",
                str(error)
            )

        finally:
            connection.close()

    def load_students(self):
        connection = get_connection()

        try:
            students = connection.execute("""
                SELECT * FROM students
                ORDER BY id DESC
            """).fetchall()

            self.display_students(students)

        finally:
            connection.close()

    def display_students(self, students):
        self.student_table.setRowCount(0)

        for row_index, student in enumerate(students):
            self.student_table.insertRow(row_index)

            values = [
                student["id"],
                student["student_number"],
                student["first_name"],
                student["last_name"],
                student["programme"],
                student["phone"],
                student["email"]
            ]

            for column_index, value in enumerate(values):
                self.student_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value or ""))
                )

    def search_students(self, search_text):
        connection = get_connection()

        try:
            search = f"%{search_text.strip()}%"

            students = connection.execute("""
                SELECT * FROM students
                WHERE student_number LIKE ?
                   OR first_name LIKE ?
                   OR last_name LIKE ?
                ORDER BY id DESC
            """, (search, search, search)).fetchall()

            self.display_students(students)

        finally:
            connection.close()

    def clear_fields(self):
        self.student_number.clear()
        self.first_name.clear()
        self.last_name.clear()
        self.phone.clear()
        self.email.clear()

        self.academic_year.setValue(datetime.now().year)

        if self.faculty_combo.count() > 0:
            self.faculty_combo.setCurrentIndex(0)
