import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView
)

from database.db import get_connection


class FeesInvoicesModule(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Fees & Invoices")
        self.resize(950, 700)
        self.setMinimumSize(800, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6FA;
            }

            QLabel {
                color: #243247;
                font-size: 13px;
            }

            QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
            }

            QPushButton {
                background-color: #172B4D;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #344D70;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #CBD5E1;
                gridline-color: #E2E8F0;
            }
        """)

        self.create_interface()
        self.load_faculties()
        self.load_fee_records()

    def create_interface(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        heading = QLabel("Fees & Invoices")
        heading.setStyleSheet(
            "font-size: 25px; font-weight: bold;"
        )

        subtitle = QLabel(
            "Configure registration and tuition fees for LISTEC students."
        )

        layout.addWidget(heading)
        layout.addWidget(subtitle)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)

        self.faculty_combo = QComboBox()
        self.faculty_combo.currentIndexChanged.connect(
            self.load_programmes
        )

        self.programme_combo = QComboBox()

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2100)
        self.year_spin.setValue(2026)

        self.fee_type_combo = QComboBox()
        self.fee_type_combo.addItems([
            "Registration",
            "Tuition"
        ])

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("R ")

        form_layout.addWidget(QLabel("Faculty"))
        form_layout.addWidget(self.faculty_combo)

        form_layout.addWidget(QLabel("Programme and Level"))
        form_layout.addWidget(self.programme_combo)

        form_layout.addWidget(QLabel("Academic Year"))
        form_layout.addWidget(self.year_spin)

        form_layout.addWidget(QLabel("Fee Type"))
        form_layout.addWidget(self.fee_type_combo)

        form_layout.addWidget(QLabel("Fee Amount"))
        form_layout.addWidget(self.amount_spin)

        save_button = QPushButton("Save Fee Structure")
        save_button.clicked.connect(self.save_fee_structure)

        form_layout.addWidget(save_button)

        layout.addLayout(form_layout)

        records_heading = QLabel("Configured Fees")
        records_heading.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )

        layout.addWidget(records_heading)

        self.fee_table = QTableWidget()
        self.fee_table.setColumnCount(5)

        self.fee_table.setHorizontalHeaderLabels([
            "Faculty",
            "Programme",
            "Academic Year",
            "Fee Type",
            "Amount"
        ])

        self.fee_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(self.fee_table)

    def load_faculties(self):

        connection = get_connection()

        try:
            cursor = connection.cursor()

            faculties = cursor.execute("""
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

        finally:
            connection.close()

    def load_programmes(self):

        faculty_id = self.faculty_combo.currentData()

        self.programme_combo.clear()

        if faculty_id is None:
            return

        connection = get_connection()

        try:
            cursor = connection.cursor()

            programmes = cursor.execute("""
                SELECT id, programme_name, level
                FROM programmes
                WHERE faculty_id = ?
                AND level IN ('L5', 'N4', 'N5', 'N6')
                ORDER BY programme_name, level
            """, (faculty_id,)).fetchall()

            for programme in programmes:

                display_name = (
                    f"{programme['programme_name']} "
                    f"({programme['level']})"
                )

                self.programme_combo.addItem(
                    display_name,
                    programme["id"]
                )

        finally:
            connection.close()

    def save_fee_structure(self):

        programme_id = self.programme_combo.currentData()

        if programme_id is None:
            QMessageBox.warning(
                self,
                "Missing Programme",
                "Please select a programme."
            )
            return

        academic_year = self.year_spin.value()
        fee_type = self.fee_type_combo.currentText()
        amount = self.amount_spin.value()

        if amount <= 0:
            QMessageBox.warning(
                self,
                "Invalid Amount",
                "Please enter a fee amount greater than zero."
            )
            return

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO fee_structure (
                    programme_id,
                    academic_year,
                    fee_type,
                    amount
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(
                    programme_id,
                    academic_year,
                    fee_type
                )
                DO UPDATE SET
                    amount = excluded.amount
            """, (
                programme_id,
                academic_year,
                fee_type,
                amount
            ))

            connection.commit()

            QMessageBox.information(
                self,
                "Success",
                "Fee structure saved successfully."
            )

            self.load_fee_records()

        except Exception as error:

            connection.rollback()

            QMessageBox.critical(
                self,
                "Database Error",
                str(error)
            )

        finally:
            connection.close()

    def load_fee_records(self):

        connection = get_connection()

        try:
            cursor = connection.cursor()

            records = cursor.execute("""
                SELECT
                    f.faculty_name,
                    p.programme_name,
                    p.level,
                    fs.academic_year,
                    fs.fee_type,
                    fs.amount

                FROM fee_structure fs

                JOIN programmes p
                    ON fs.programme_id = p.id

                JOIN faculties f
                    ON p.faculty_id = f.id

                ORDER BY
                    fs.academic_year DESC,
                    f.faculty_name,
                    p.programme_name,
                    p.level,
                    fs.fee_type
            """).fetchall()

            self.fee_table.setRowCount(0)

            for record in records:

                row = self.fee_table.rowCount()
                self.fee_table.insertRow(row)

                values = [
                    record["faculty_name"],
                    f"{record['programme_name']} ({record['level']})",
                    str(record["academic_year"]),
                    record["fee_type"],
                    f"R {record['amount']:,.2f}"
                ]

                for column, value in enumerate(values):
                    self.fee_table.setItem(
                        row,
                        column,
                        QTableWidgetItem(value)
                    )

        finally:
            connection.close()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = FeesInvoicesModule()
    window.show()

    sys.exit(app.exec())