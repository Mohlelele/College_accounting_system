import sys
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_connection


class CoursesModule(QMainWindow):
    """
    Courses Module — Manage courses, set fees per course,
    and enrol students into courses.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Course Management")
        self.resize(1050, 750)
        self.setMinimumSize(850, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6FA;
            }
            QLabel {
                color: #243247;
                font-size: 13px;
            }
            QComboBox, QLineEdit, QTextEdit,
            QDateEdit, QDoubleSpinBox, QSpinBox {
                padding: 8px;
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #172B4D;
                color: white;
                padding: 10px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #344D70;
            }
            QPushButton:disabled {
                background-color: #94A3B8;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #CBD5E1;
                gridline-color: #E2E8F0;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #E2E8F0;
                color: #243247;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 3px;
            }
            QTabBar::tab:selected {
                background-color: #172B4D;
                color: white;
            }
        """)

        # Ensure the three courses tables exist before building the UI
        self._create_tables()

        self._selected_course_id = None   # used in Fees tab
        self._enrol_course_id = None      # used in Enrolment tab

        self._build_ui()
        self._load_courses_table()
        self._load_fees_course_combo()
        self._load_enrol_combos()
        self._load_enrolments_table()

    # ------------------------------------------------------------------
    # Schema bootstrap
    # ------------------------------------------------------------------

    def _create_tables(self):
        """Create courses, course_fees, and student_courses if missing."""
        connection = get_connection()
        try:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS courses (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_code  TEXT    NOT NULL UNIQUE,
                    course_name  TEXT    NOT NULL,
                    duration     TEXT,
                    description  TEXT,
                    created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS course_fees (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id     INTEGER NOT NULL
                                      REFERENCES courses(id),
                    academic_year INTEGER NOT NULL,
                    total_fee     REAL    NOT NULL CHECK(total_fee >= 0),
                    registration_fee REAL DEFAULT 0 CHECK(registration_fee >= 0),
                    created_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(course_id, academic_year)
                );

                CREATE TABLE IF NOT EXISTS student_courses (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id    INTEGER NOT NULL
                                      REFERENCES students(id),
                    course_id     INTEGER NOT NULL
                                      REFERENCES courses(id),
                    academic_year INTEGER NOT NULL,
                    enrolled_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, course_id, academic_year)
                );
            """)
            connection.commit()
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Main UI builder
    # ------------------------------------------------------------------

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        central = QWidget()
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

        root = QVBoxLayout(central)
        root.setContentsMargins(25, 25, 25, 25)
        root.setSpacing(15)

        # Back button at top
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.setStyleSheet("background-color: #64748B;")
        back_btn.clicked.connect(self.close)
        root.addWidget(back_btn)

        heading = QLabel("COURSE MANAGEMENT")
        heading.setStyleSheet(
            "font-size: 25px; font-weight: bold; color: #183153;"
        )
        subtitle = QLabel(
            "Add courses, configure their fees, and enrol students."
        )
        root.addWidget(heading)
        root.addWidget(subtitle)

        tabs = QTabWidget()
        tabs.addTab(self._build_courses_tab(), "Courses")
        tabs.addTab(self._build_fees_tab(), "Course Fees")
        tabs.addTab(self._build_enrolment_tab(), "Student Enrolment")

        root.addWidget(tabs)

    # ------------------------------------------------------------------
    # Tab 1 — Courses (add / view / delete)
    # ------------------------------------------------------------------

    def _build_courses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ---- Add course form ----
        form_label = QLabel("Add a New Course")
        form_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(form_label)

        form = QFormLayout()
        form.setSpacing(10)

        self._code_field = QLineEdit()
        self._code_field.setPlaceholderText("e.g. BUS101")

        self._name_field = QLineEdit()
        self._name_field.setPlaceholderText("e.g. Business Management")

        self._duration_field = QLineEdit()
        self._duration_field.setPlaceholderText("e.g. 1 Year, 6 Months")

        self._desc_field = QTextEdit()
        self._desc_field.setMaximumHeight(80)
        self._desc_field.setPlaceholderText("Optional course description")

        form.addRow("Course Code *:", self._code_field)
        form.addRow("Course Name *:", self._name_field)
        form.addRow("Duration:", self._duration_field)
        form.addRow("Description:", self._desc_field)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Course")
        add_btn.clicked.connect(self._add_course)
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(
            "background-color: #64748B;"
        )
        clear_btn.clicked.connect(self._clear_course_form)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ---- Course list ----
        list_label = QLabel("All Courses")
        list_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(list_label)

        self._courses_table = QTableWidget()
        self._courses_table.setColumnCount(5)
        self._courses_table.setHorizontalHeaderLabels([
            "ID", "Code", "Name", "Duration", "Description"
        ])
        self._courses_table.setColumnHidden(0, True)
        self._courses_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._courses_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self._courses_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._courses_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._courses_table.itemSelectionChanged.connect(self._on_course_selected)
        layout.addWidget(self._courses_table)

        action_btn_row = QHBoxLayout()

        edit_btn = QPushButton("Edit Selected Course")
        edit_btn.setStyleSheet("background-color: #2563EB;")
        edit_btn.clicked.connect(self._edit_course)

        del_btn = QPushButton("Delete Selected Course")
        del_btn.setStyleSheet("background-color: #DC2626;")
        del_btn.clicked.connect(self._delete_course)

        action_btn_row.addWidget(edit_btn)
        action_btn_row.addWidget(del_btn)
        action_btn_row.addStretch()
        layout.addLayout(action_btn_row)

        return widget

    # ------------------------------------------------------------------
    # Tab 2 — Course Fees
    # ------------------------------------------------------------------

    def _build_fees_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form_label = QLabel("Set / Update Course Fees")
        form_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(form_label)

        form = QFormLayout()
        form.setSpacing(10)

        self._fee_course_combo = QComboBox()
        self._fee_course_combo.currentIndexChanged.connect(
            self._on_fee_course_changed
        )

        self._fee_year_spin = QSpinBox()
        self._fee_year_spin.setRange(2020, 2100)
        self._fee_year_spin.setValue(QDate.currentDate().year())

        self._total_fee_spin = QDoubleSpinBox()
        self._total_fee_spin.setRange(0.01, 999_999_999)
        self._total_fee_spin.setDecimals(2)
        self._total_fee_spin.setPrefix("R ")

        self._reg_fee_spin = QDoubleSpinBox()
        self._reg_fee_spin.setRange(0, 999_999_999)
        self._reg_fee_spin.setDecimals(2)
        self._reg_fee_spin.setPrefix("R ")

        form.addRow("Course *:", self._fee_course_combo)
        form.addRow("Academic Year *:", self._fee_year_spin)
        form.addRow("Total Course Fee *:", self._total_fee_spin)
        form.addRow("Registration Fee (optional):", self._reg_fee_spin)

        layout.addLayout(form)

        save_fee_btn = QPushButton("Save Course Fee")
        save_fee_btn.clicked.connect(self._save_course_fee)
        layout.addWidget(save_fee_btn)

        fees_label = QLabel("Configured Course Fees")
        fees_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(fees_label)

        self._fees_table = QTableWidget()
        self._fees_table.setColumnCount(5)
        self._fees_table.setHorizontalHeaderLabels([
            "Course Code", "Course Name", "Academic Year",
            "Total Fee", "Registration Fee"
        ])
        self._fees_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._fees_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self._fees_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._fees_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self._fees_table)

        del_fee_btn = QPushButton("Delete Selected Fee")
        del_fee_btn.setStyleSheet("background-color: #DC2626;")
        del_fee_btn.clicked.connect(self._delete_course_fee)
        layout.addWidget(del_fee_btn)

        return widget

    # ------------------------------------------------------------------
    # Tab 3 — Student Enrolment
    # ------------------------------------------------------------------

    def _build_enrolment_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form_label = QLabel("Enrol a Student into a Course")
        form_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(form_label)

        form = QFormLayout()
        form.setSpacing(10)

        self._enrol_student_combo = QComboBox()
        self._enrol_course_combo = QComboBox()

        self._enrol_year_spin = QSpinBox()
        self._enrol_year_spin.setRange(2020, 2100)
        self._enrol_year_spin.setValue(QDate.currentDate().year())

        form.addRow("Student *:", self._enrol_student_combo)
        form.addRow("Course *:", self._enrol_course_combo)
        form.addRow("Academic Year *:", self._enrol_year_spin)

        layout.addLayout(form)

        enrol_btn = QPushButton("Enrol Student")
        enrol_btn.clicked.connect(self._enrol_student)
        layout.addWidget(enrol_btn)

        enrol_label = QLabel("Current Enrolments")
        enrol_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(enrol_label)

        # Search bar for enrolments
        self._enrol_search = QLineEdit()
        self._enrol_search.setPlaceholderText(
            "Search by student number, name or course..."
        )
        self._enrol_search.textChanged.connect(self._load_enrolments_table)
        layout.addWidget(self._enrol_search)

        self._enrolments_table = QTableWidget()
        self._enrolments_table.setColumnCount(6)
        self._enrolments_table.setHorizontalHeaderLabels([
            "ID", "Student Number", "Student Name",
            "Course Code", "Course Name", "Academic Year"
        ])
        self._enrolments_table.setColumnHidden(0, True)
        self._enrolments_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._enrolments_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self._enrolments_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._enrolments_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self._enrolments_table)

        unenrol_btn = QPushButton("Remove Selected Enrolment")
        unenrol_btn.setStyleSheet("background-color: #DC2626;")
        unenrol_btn.clicked.connect(self._remove_enrolment)
        layout.addWidget(unenrol_btn)

        return widget

    # ------------------------------------------------------------------
    # Courses tab — logic
    # ------------------------------------------------------------------

    def _on_course_selected(self):
        """When a course is selected, load its data into the form for editing."""
        row = self._courses_table.currentRow()
        if row < 0:
            return

        code = self._courses_table.item(row, 1).text()
        name = self._courses_table.item(row, 2).text()
        duration = self._courses_table.item(row, 3).text()
        description = self._courses_table.item(row, 4).text()

        self._code_field.setText(code)
        self._name_field.setText(name)
        self._duration_field.setText(duration)
        self._desc_field.setPlainText(description)

    def _add_course(self):
        code = self._code_field.text().strip().upper()
        name = self._name_field.text().strip()
        duration = self._duration_field.text().strip()
        description = self._desc_field.toPlainText().strip()

        if not code or not name:
            QMessageBox.warning(
                self, "Missing Fields",
                "Course Code and Course Name are required."
            )
            return

        connection = get_connection()
        try:
            connection.execute("""
                INSERT INTO courses (course_code, course_name, duration, description)
                VALUES (?, ?, ?, ?)
            """, (code, name, duration or None, description or None))
            connection.commit()

            QMessageBox.information(
                self, "Success",
                f"Course '{code} — {name}' added successfully."
            )
            self._clear_course_form()
            self._load_courses_table()
            self._load_fees_course_combo()
            self._load_enrol_combos()

        except Exception as error:
            connection.rollback()
            if "UNIQUE constraint" in str(error):
                QMessageBox.warning(
                    self, "Duplicate Code",
                    f"A course with code '{code}' already exists."
                )
            else:
                QMessageBox.critical(self, "Database Error", str(error))
        finally:
            connection.close()

    def _load_courses_table(self):
        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT id, course_code, course_name, duration, description
                FROM courses
                ORDER BY course_code
            """).fetchall()

            self._courses_table.setRowCount(0)
            for row in rows:
                r = self._courses_table.rowCount()
                self._courses_table.insertRow(r)
                for col, val in enumerate([
                    row["id"], row["course_code"], row["course_name"],
                    row["duration"] or "", row["description"] or ""
                ]):
                    self._courses_table.setItem(
                        r, col, QTableWidgetItem(str(val))
                    )
        finally:
            connection.close()

    def _delete_course(self):
        row = self._courses_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select a course to delete."
            )
            return

        course_id = int(self._courses_table.item(row, 0).text())
        code = self._courses_table.item(row, 1).text()
        name = self._courses_table.item(row, 2).text()

        answer = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete course '{code} — {name}'?\n\n"
            "This will also remove its fees and all student enrolments.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        connection = get_connection()
        try:
            connection.execute(
                "DELETE FROM student_courses WHERE course_id = ?",
                (course_id,)
            )
            connection.execute(
                "DELETE FROM course_fees WHERE course_id = ?",
                (course_id,)
            )
            connection.execute(
                "DELETE FROM courses WHERE id = ?",
                (course_id,)
            )
            connection.commit()

            self._load_courses_table()
            self._load_fees_course_combo()
            self._load_fees_table()
            self._load_enrol_combos()
            self._load_enrolments_table()

        except Exception as error:
            connection.rollback()
            QMessageBox.critical(self, "Delete Error", str(error))
        finally:
            connection.close()

    def _on_course_selected(self):
        """When a course is selected, load its data into the form for editing."""
        row = self._courses_table.currentRow()
        if row < 0:
            return

        code = self._courses_table.item(row, 1).text()
        name = self._courses_table.item(row, 2).text()
        duration = self._courses_table.item(row, 3).text()
        description = self._courses_table.item(row, 4).text()

        self._code_field.setText(code)
        self._name_field.setText(name)
        self._duration_field.setText(duration)
        self._desc_field.setPlainText(description)

    def _edit_course(self):
        """Edit the selected course."""
        row = self._courses_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select a course to edit."
            )
            return

        course_id = int(self._courses_table.item(row, 0).text())
        old_code = self._courses_table.item(row, 1).text()

        code = self._code_field.text().strip().upper()
        name = self._name_field.text().strip()
        duration = self._duration_field.text().strip()
        description = self._desc_field.toPlainText().strip()

        if not code or not name:
            QMessageBox.warning(
                self, "Missing Fields",
                "Course Code and Course Name are required."
            )
            return

        connection = get_connection()
        try:
            # Check if new code is unique (or same as old code)
            if code != old_code:
                existing = connection.execute(
                    "SELECT id FROM courses WHERE course_code = ?",
                    (code,)
                ).fetchone()
                if existing:
                    QMessageBox.warning(
                        self, "Duplicate Code",
                        f"A course with code '{code}' already exists."
                    )
                    return

            connection.execute("""
                UPDATE courses
                SET course_code = ?, course_name = ?, duration = ?, description = ?
                WHERE id = ?
            """, (code, name, duration or None, description or None, course_id))
            connection.commit()

            QMessageBox.information(
                self, "Success",
                f"Course '{code} — {name}' updated successfully."
            )
            self._clear_course_form()
            self._load_courses_table()
            self._load_fees_course_combo()
            self._load_enrol_combos()

        except Exception as error:
            connection.rollback()
            QMessageBox.critical(self, "Update Error", str(error))
        finally:
            connection.close()
            QMessageBox.warning(
                self, "No Selection", "Please select a course to delete."
            )
            return

        course_id = int(self._courses_table.item(row, 0).text())
        code = self._courses_table.item(row, 1).text()
        name = self._courses_table.item(row, 2).text()

        answer = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete course '{code} — {name}'?\n\n"
            "This will also remove its fees and all student enrolments.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        connection = get_connection()
        try:
            connection.execute(
                "DELETE FROM student_courses WHERE course_id = ?",
                (course_id,)
            )
            connection.execute(
                "DELETE FROM course_fees WHERE course_id = ?",
                (course_id,)
            )
            connection.execute(
                "DELETE FROM courses WHERE id = ?",
                (course_id,)
            )
            connection.commit()

            self._load_courses_table()
            self._load_fees_course_combo()
            self._load_fees_table()
            self._load_enrol_combos()
            self._load_enrolments_table()

        except Exception as error:
            connection.rollback()
            QMessageBox.critical(self, "Delete Error", str(error))
        finally:
            connection.close()

    def _clear_course_form(self):
        self._code_field.clear()
        self._name_field.clear()
        self._duration_field.clear()
        self._desc_field.clear()

    # ------------------------------------------------------------------
    # Course Fees tab — logic
    # ------------------------------------------------------------------

    def _load_fees_course_combo(self):
        connection = get_connection()
        try:
            courses = connection.execute("""
                SELECT id, course_code, course_name
                FROM courses
                ORDER BY course_code
            """).fetchall()

            self._fee_course_combo.blockSignals(True)
            self._fee_course_combo.clear()
            self._fee_course_combo.addItem("— Select a course —", None)
            for c in courses:
                self._fee_course_combo.addItem(
                    f"{c['course_code']} — {c['course_name']}", c["id"]
                )
            self._fee_course_combo.blockSignals(False)
            self._load_fees_table()
        finally:
            connection.close()

    def _on_fee_course_changed(self, *_):
        self._load_fees_table()

    def _load_fees_table(self):
        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT
                    c.course_code,
                    c.course_name,
                    cf.id        AS fee_id,
                    cf.academic_year,
                    cf.total_fee,
                    cf.registration_fee
                FROM course_fees cf
                JOIN courses c ON cf.course_id = c.id
                ORDER BY cf.academic_year DESC, c.course_code
            """).fetchall()

            self._fees_table.setRowCount(0)
            for row in rows:
                r = self._fees_table.rowCount()
                self._fees_table.insertRow(r)
                values = [
                    row["course_code"],
                    row["course_name"],
                    str(row["academic_year"]),
                    f"R {row['total_fee']:,.2f}",
                    f"R {row['registration_fee']:,.2f}",
                ]
                for col, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, row["fee_id"])
                    self._fees_table.setItem(r, col, item)
        finally:
            connection.close()

    def _save_course_fee(self):
        course_id = self._fee_course_combo.currentData()
        if course_id is None:
            QMessageBox.warning(
                self, "No Course", "Please select a course first."
            )
            return

        year = self._fee_year_spin.value()
        total_fee = self._total_fee_spin.value()
        reg_fee = self._reg_fee_spin.value()

        if total_fee <= 0:
            QMessageBox.warning(
                self, "Invalid Amount", "Total fee must be greater than zero."
            )
            return

        connection = get_connection()
        try:
            connection.execute("""
                INSERT INTO course_fees (course_id, academic_year, total_fee, registration_fee)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(course_id, academic_year)
                DO UPDATE SET total_fee = excluded.total_fee,
                              registration_fee = excluded.registration_fee
            """, (course_id, year, total_fee, reg_fee))
            connection.commit()

            QMessageBox.information(
                self, "Saved",
                f"Course fee of R {total_fee:,.2f} saved for "
                f"academic year {year}."
            )
            self._load_fees_table()

        except Exception as error:
            connection.rollback()
            QMessageBox.critical(self, "Database Error", str(error))
        finally:
            connection.close()

    def _delete_course_fee(self):
        row = self._fees_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select a fee row to delete."
            )
            return

        fee_id = self._fees_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        course_code = self._fees_table.item(row, 0).text()
        year = self._fees_table.item(row, 2).text()

        answer = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete the course fee for {course_code} ({year})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        connection = get_connection()
        try:
            connection.execute(
                "DELETE FROM course_fees WHERE id = ?", (fee_id,)
            )
            connection.commit()
            self._load_fees_table()
        except Exception as error:
            connection.rollback()
            QMessageBox.critical(self, "Delete Error", str(error))
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Enrolment tab — logic
    # ------------------------------------------------------------------

    def _load_enrol_combos(self):
        connection = get_connection()
        try:
            students = connection.execute("""
                SELECT id, student_number, first_name, last_name
                FROM students
                ORDER BY first_name, last_name
            """).fetchall()

            self._enrol_student_combo.clear()
            self._enrol_student_combo.addItem("— Select a student —", None)
            for s in students:
                self._enrol_student_combo.addItem(
                    f"{s['student_number']} — "
                    f"{s['first_name']} {s['last_name']}",
                    s["id"]
                )

            courses = connection.execute("""
                SELECT id, course_code, course_name
                FROM courses
                ORDER BY course_code
            """).fetchall()

            self._enrol_course_combo.clear()
            self._enrol_course_combo.addItem("— Select a course —", None)
            for c in courses:
                self._enrol_course_combo.addItem(
                    f"{c['course_code']} — {c['course_name']}", c["id"]
                )
        finally:
            connection.close()

    def _enrol_student(self):
        student_id = self._enrol_student_combo.currentData()
        course_id = self._enrol_course_combo.currentData()
        year = self._enrol_year_spin.value()

        if student_id is None or course_id is None:
            QMessageBox.warning(
                self, "Missing Selection",
                "Please select both a student and a course."
            )
            return

        connection = get_connection()
        try:
            connection.execute("""
                INSERT INTO student_courses (student_id, course_id, academic_year)
                VALUES (?, ?, ?)
            """, (student_id, course_id, year))
            connection.commit()

            QMessageBox.information(
                self, "Enrolled",
                "Student enrolled successfully."
            )
            self._load_enrolments_table()

        except Exception as error:
            connection.rollback()
            if "UNIQUE constraint" in str(error):
                QMessageBox.warning(
                    self, "Already Enrolled",
                    "This student is already enrolled in that course "
                    "for the selected academic year."
                )
            else:
                QMessageBox.critical(self, "Enrolment Error", str(error))
        finally:
            connection.close()

    def _load_enrolments_table(self, *_):
        search = ""
        if hasattr(self, "_enrol_search"):
            search = self._enrol_search.text().strip()

        like = f"%{search}%"

        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT
                    sc.id,
                    s.student_number,
                    s.first_name || ' ' || s.last_name AS student_name,
                    c.course_code,
                    c.course_name,
                    sc.academic_year
                FROM student_courses sc
                JOIN students s ON sc.student_id = s.id
                JOIN courses   c ON sc.course_id  = c.id
                WHERE s.student_number LIKE ?
                   OR s.first_name     LIKE ?
                   OR s.last_name      LIKE ?
                   OR c.course_code    LIKE ?
                   OR c.course_name    LIKE ?
                ORDER BY sc.academic_year DESC, s.first_name, c.course_code
            """, (like, like, like, like, like)).fetchall()

            self._enrolments_table.setRowCount(0)
            for row in rows:
                r = self._enrolments_table.rowCount()
                self._enrolments_table.insertRow(r)
                for col, val in enumerate([
                    row["id"],
                    row["student_number"],
                    row["student_name"],
                    row["course_code"],
                    row["course_name"],
                    str(row["academic_year"]),
                ]):
                    self._enrolments_table.setItem(
                        r, col, QTableWidgetItem(str(val))
                    )
        finally:
            connection.close()

    def _remove_enrolment(self):
        row = self._enrolments_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "No Selection",
                "Please select an enrolment to remove."
            )
            return

        enrolment_id = int(self._enrolments_table.item(row, 0).text())
        student_name = self._enrolments_table.item(row, 2).text()
        course_code = self._enrolments_table.item(row, 3).text()

        answer = QMessageBox.question(
            self, "Confirm Remove",
            f"Remove {student_name} from {course_code}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        connection = get_connection()
        try:
            connection.execute(
                "DELETE FROM student_courses WHERE id = ?",
                (enrolment_id,)
            )
            connection.commit()
            self._load_enrolments_table()
        except Exception as error:
            connection.rollback()
            QMessageBox.critical(self, "Remove Error", str(error))
        finally:
            connection.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoursesModule()
    window.show()
    sys.exit(app.exec())
