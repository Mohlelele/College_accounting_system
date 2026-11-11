import sys
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QSpinBox,
    QDateEdit,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QFileDialog,
)

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QTextDocument

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_connection


class FeesInvoicesModule(QMainWindow):
    """
    Invoices Module - Create invoices and download as PDF
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Invoices")
        self.resize(1100, 800)
        self.setMinimumSize(900, 650)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6FA;
            }
            QLabel {
                color: #243247;
                font-size: 13px;
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
            QComboBox, QSpinBox, QDateEdit, QLineEdit {
                padding: 8px;
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #CBD5E1;
                gridline-color: #E2E8F0;
            }
        """)

        self._build_ui()
        self._load_invoices()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        central = QWidget()
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.setStyleSheet("background-color: #64748B;")
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)

        # Title
        heading = QLabel("INVOICES")
        heading.setStyleSheet("font-size: 24px; font-weight: bold; color: #172B4D;")
        layout.addWidget(heading)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background-color: #E2E8F0;
                color: #243247;
                padding: 8px 16px;
                border: none;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #172B4D;
                color: white;
            }
        """)

        # Tab 1: Create Invoice
        self.tab_create = self._create_create_invoice_tab()
        self.tabs.addTab(self.tab_create, "Create Invoice")

        # Tab 2: View & Download
        self.tab_download = self._create_download_tab()
        self.tabs.addTab(self.tab_download, "Download Invoice")

        layout.addWidget(self.tabs)

    def _create_create_invoice_tab(self):
        """Create Invoice tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Form section
        form = QFormLayout()

        self.student_combo = QComboBox()
        self._load_students_combo()
        self.student_combo.currentIndexChanged.connect(self._on_student_selected)
        form.addRow("Student:", self.student_combo)

        self.course_combo = QComboBox()
        form.addRow("Course/Description:", self.course_combo)

        self.amount = QSpinBox()
        self.amount.setMaximum(9999999)
        self.amount.setSuffix(" R")
        form.addRow("Amount:", self.amount)

        self.invoice_date = QDateEdit()
        self.invoice_date.setDate(QDate.currentDate())
        form.addRow("Invoice Date:", self.invoice_date)

        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(30))
        form.addRow("Due Date:", self.due_date)

        self.description = QLineEdit()
        self.description.setPlaceholderText("e.g., Tuition Fee, Registration Fee")
        form.addRow("Description:", self.description)

        layout.addLayout(form)

        # Action buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Invoice")
        create_btn.clicked.connect(self._create_invoice)
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("background-color: #64748B;")
        clear_btn.clicked.connect(self._clear_form)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        return widget

    def _create_download_tab(self):
        """Download Invoice tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Invoice list
        title = QLabel("All Invoices")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels([
            "Invoice #", "Student", "Date", "Due Date", "Amount", "Status"
        ])
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.invoices_table)

        # Download button
        btn_layout = QHBoxLayout()
        download_btn = QPushButton("Download as PDF")
        download_btn.clicked.connect(self._download_invoice_pdf)
        btn_layout.addWidget(download_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def _load_students_combo(self):
        """Load students into combo box."""
        connection = get_connection()
        try:
            students = connection.execute("""
                SELECT id, student_number, first_name, last_name
                FROM students
                ORDER BY first_name, last_name
            """).fetchall()

            self.student_combo.clear()
            self.student_combo.addItem("— Select Student —", None)

            for student in students:
                name = f"{student['student_number']} - {student['first_name']} {student['last_name']}"
                self.student_combo.addItem(name, student["id"])
        finally:
            connection.close()

    def _on_student_selected(self):
        """Load student's enrolled courses when selected."""
        student_id = self.student_combo.currentData()
        
        if student_id is None:
            self.course_combo.clear()
            return

        connection = get_connection()
        try:
            # Get all courses enrolled by this student
            enrollments = connection.execute("""
                SELECT DISTINCT
                    c.id, c.course_code, c.course_name,
                    sc.academic_year,
                    cf.total_fee
                FROM student_courses sc
                JOIN courses c ON sc.course_id = c.id
                LEFT JOIN course_fees cf ON c.id = cf.course_id 
                    AND sc.academic_year = cf.academic_year
                WHERE sc.student_id = ?
                ORDER BY c.course_code
            """, (student_id,)).fetchall()

            self.course_combo.blockSignals(True)
            self.course_combo.clear()
            
            if not enrollments:
                self.course_combo.addItem("— No courses enrolled —", None)
            else:
                self.course_combo.addItem("— Select Course —", None)
                for enr in enrollments:
                    course_name = f"{enr['course_code']} - {enr['course_name']} ({enr['academic_year']})"
                    course_data = {
                        "course_id": enr["id"],
                        "amount": float(enr["total_fee"] or 0)
                    }
                    self.course_combo.addItem(course_name, course_data)
            
            self.course_combo.blockSignals(False)
            self.course_combo.currentIndexChanged.connect(self._on_course_selected)

        finally:
            connection.close()

    def _on_course_selected(self):
        """Update amount when course is selected."""
        course_data = self.course_combo.currentData()
        
        if course_data is None or not isinstance(course_data, dict):
            self.amount.setValue(0)
        else:
            self.amount.setValue(int(course_data["amount"]))

    def _load_invoices(self):
        """Load all invoices into the table."""
        connection = get_connection()
        try:
            invoices = connection.execute("""
                SELECT
                    i.id,
                    i.invoice_number,
                    s.first_name || ' ' || s.last_name as student_name,
                    i.invoice_date,
                    i.due_date,
                    i.total_amount,
                    i.status,
                    COALESCE(SUM(p.amount), 0) as paid_amount
                FROM invoices i
                JOIN students s ON i.student_id = s.id
                LEFT JOIN payments p ON p.invoice_id = i.id
                GROUP BY i.id
                ORDER BY i.invoice_date DESC
            """).fetchall()

            self.invoices_table.setRowCount(0)

            for inv in invoices:
                total = float(inv["total_amount"] or 0)
                paid = float(inv["paid_amount"] or 0)
                balance = max(0.0, total - paid)

                # Determine status color
                if balance <= 0:
                    status = "Paid"
                    status_color = "#16A34A"
                elif inv["due_date"] < datetime.now().strftime("%Y-%m-%d"):
                    status = "Overdue"
                    status_color = "#DC2626"
                else:
                    status = "Unpaid"
                    status_color = "#D97706"

                row = self.invoices_table.rowCount()
                self.invoices_table.insertRow(row)

                self.invoices_table.setItem(row, 0, QTableWidgetItem(inv["invoice_number"]))
                self.invoices_table.setItem(row, 1, QTableWidgetItem(inv["student_name"]))
                self.invoices_table.setItem(row, 2, QTableWidgetItem(inv["invoice_date"]))
                self.invoices_table.setItem(row, 3, QTableWidgetItem(inv["due_date"]))
                self.invoices_table.setItem(row, 4, QTableWidgetItem(f"R {total:,.2f}"))

                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor(status_color))
                self.invoices_table.setItem(row, 5, status_item)

                # Store invoice id for later use
                self.invoices_table.item(row, 0).invoice_id = inv["id"]

        finally:
            connection.close()

    def _create_invoice(self):
        """Create a new invoice."""
        student_id = self.student_combo.currentData()
        amount = self.amount.value()
        description = self.description.text() or "Course Fee"

        if student_id is None:
            QMessageBox.warning(self, "Missing Info", "Please select a student.")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter an amount greater than 0.")
            return

        invoice_date = self.invoice_date.date().toString("yyyy-MM-dd")
        due_date = self.due_date.date().toString("yyyy-MM-dd")

        if self.due_date.date() < self.invoice_date.date():
            QMessageBox.warning(self, "Invalid Dates", "Due date must be after invoice date.")
            return

        invoice_number = "INV-" + datetime.now().strftime("%Y%m%d%H%M%S")

        connection = get_connection()
        try:
            connection.execute("""
                INSERT INTO invoices (student_id, invoice_number, invoice_date, due_date, total_amount, status)
                VALUES (?, ?, ?, ?, ?, 'Unpaid')
            """, (student_id, invoice_number, invoice_date, due_date, amount))

            invoice_id = connection.execute(
                "SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,)
            ).fetchone()["id"]

            connection.execute("""
                INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, line_total)
                VALUES (?, ?, 1, ?, ?)
            """, (invoice_id, description, amount, amount))

            connection.commit()

            QMessageBox.information(
                self, "Success",
                f"Invoice created successfully!\n\n"
                f"Invoice Number: {invoice_number}\n"
                f"Amount: R {amount:,.2f}"
            )

            self._clear_form()
            self._load_invoices()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create invoice: {e}")
        finally:
            connection.close()

    def _download_invoice_pdf(self):
        """Download selected invoice as PDF."""
        row = self.invoices_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an invoice to download.")
            return

        invoice_number = self.invoices_table.item(row, 0).text()
        student_name = self.invoices_table.item(row, 1).text()
        amount = self.invoices_table.item(row, 4).text()
        invoice_date = self.invoices_table.item(row, 2).text()
        due_date = self.invoices_table.item(row, 3).text()

        # Get invoice details
        connection = get_connection()
        try:
            invoice = connection.execute("""
                SELECT i.id, i.invoice_number, s.student_number, s.email, s.phone,
                       s.first_name, s.last_name, i.invoice_date, i.due_date, i.total_amount
                FROM invoices i
                JOIN students s ON i.student_id = s.id
                WHERE i.invoice_number = ?
            """, (invoice_number,)).fetchone()

            if not invoice:
                QMessageBox.warning(self, "Not Found", "Invoice not found.")
                return

            # Generate HTML for PDF
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #172B4D; padding-bottom: 15px; }}
                    .header h1 {{ color: #172B4D; margin: 0; }}
                    .header p {{ margin: 5px 0; color: #666; }}
                    .details {{ margin-bottom: 30px; }}
                    .details-row {{ display: flex; margin-bottom: 10px; }}
                    .label {{ width: 150px; font-weight: bold; }}
                    .table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
                    .table th {{ background-color: #172B4D; color: white; padding: 10px; text-align: left; }}
                    .table td {{ border: 1px solid #ddd; padding: 10px; }}
                    .total {{ text-align: right; font-size: 18px; font-weight: bold; margin-top: 20px; }}
                    .footer {{ margin-top: 40px; text-align: center; color: #666; font-size: 10px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>LISTEC COLLEGE</h1>
                    <p>Financial Management System</p>
                    <p>TAX INVOICE</p>
                </div>

                <div class="details">
                    <div class="details-row">
                        <div class="label">Invoice Number:</div>
                        <div>{invoice['invoice_number']}</div>
                    </div>
                    <div class="details-row">
                        <div class="label">Invoice Date:</div>
                        <div>{invoice['invoice_date']}</div>
                    </div>
                    <div class="details-row">
                        <div class="label">Due Date:</div>
                        <div>{invoice['due_date']}</div>
                    </div>
                </div>

                <div class="details">
                    <h3 style="color: #172B4D;">BILL TO:</h3>
                    <div class="details-row">
                        <div class="label">Student Name:</div>
                        <div>{invoice['first_name']} {invoice['last_name']}</div>
                    </div>
                    <div class="details-row">
                        <div class="label">Student Number:</div>
                        <div>{invoice['student_number']}</div>
                    </div>
                    <div class="details-row">
                        <div class="label">Email:</div>
                        <div>{invoice['email'] or 'N/A'}</div>
                    </div>
                    <div class="details-row">
                        <div class="label">Phone:</div>
                        <div>{invoice['phone'] or 'N/A'}</div>
                    </div>
                </div>

                <table class="table">
                    <tr>
                        <th>Description</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                    <tr>
                        <td>Course Fee</td>
                        <td style="text-align: right;">R {float(invoice['total_amount']):,.2f}</td>
                    </tr>
                </table>

                <div class="total">
                    TOTAL DUE: R {float(invoice['total_amount']):,.2f}
                </div>

                <div class="footer">
                    <p>Thank you for your business.</p>
                    <p>LISTEC COLLEGE - Confidential</p>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </body>
            </html>
            """

            # Save PDF
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Invoice as PDF",
                f"{invoice_number}.pdf",
                "PDF Files (*.pdf)"
            )

            if file_path:
                doc = QTextDocument()
                doc.setHtml(html)

                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)

                doc.print(printer)

                QMessageBox.information(self, "Success", f"Invoice saved as PDF:\n{file_path}")
                self._load_invoices()

        finally:
            connection.close()

    def _clear_form(self):
        """Clear the create invoice form."""
        self.student_combo.setCurrentIndex(0)
        self.course_combo.setCurrentIndex(0)
        self.amount.setValue(0)
        self.invoice_date.setDate(QDate.currentDate())
        self.due_date.setDate(QDate.currentDate().addDays(30))
        self.description.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FeesInvoicesModule()
    window.show()
    sys.exit(app.exec())
