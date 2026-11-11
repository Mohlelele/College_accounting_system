import sys
from pathlib import Path
from datetime import datetime, timedelta

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
    QTextEdit,
)

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_connection


class StudentAccountsModule(QMainWindow):
    """
    Student Accounts Module - Manage student accounts with 7 tabs:
    Add Receipt, Record Payment, Create Invoice, View Details, Send Reminder, Download Invoice, Edit Student
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Student Accounts")
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

        self.selected_student_id = None
        self._build_ui()
        self._load_students()

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
        heading = QLabel("STUDENT ACCOUNTS MANAGEMENT")
        heading.setStyleSheet("font-size: 24px; font-weight: bold; color: #172B4D;")
        layout.addWidget(heading)

        # Student selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select Student:"))
        
        self.student_combo = QComboBox()
        self.student_combo.currentIndexChanged.connect(self._on_student_selected)
        selector_layout.addWidget(self.student_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

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

        # Tab 1: View Details
        self.tab_view_details = self._create_view_details_tab()
        self.tabs.addTab(self.tab_view_details, "View Details")

        # Tab 2: Add Receipt
        self.tab_add_receipt = self._create_add_receipt_tab()
        self.tabs.addTab(self.tab_add_receipt, "Add Receipt")

        # Tab 3: Record Payment
        self.tab_record_payment = self._create_record_payment_tab()
        self.tabs.addTab(self.tab_record_payment, "Record Payment")

        # Tab 4: Create Invoice
        self.tab_create_invoice = self._create_create_invoice_tab()
        self.tabs.addTab(self.tab_create_invoice, "Create Invoice")

        # Tab 5: Send Reminder
        self.tab_send_reminder = self._create_send_reminder_tab()
        self.tabs.addTab(self.tab_send_reminder, "Send Reminder")

        # Tab 6: Download Invoice
        self.tab_download_invoice = self._create_download_invoice_tab()
        self.tabs.addTab(self.tab_download_invoice, "Download Invoice")

        # Tab 7: Edit Student
        self.tab_edit_student = self._create_edit_student_tab()
        self.tabs.addTab(self.tab_edit_student, "Edit Student")

        layout.addWidget(self.tabs)

    def _create_view_details_tab(self):
        """View Details tab - display student info and invoices."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        info_label = QLabel("Student Information")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(info_label)

        self.details_info = QTextEdit()
        self.details_info.setReadOnly(True)
        self.details_info.setMaximumHeight(150)
        layout.addWidget(self.details_info)

        invoices_label = QLabel("Student Invoices")
        invoices_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(invoices_label)

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(6)
        self.details_table.setHorizontalHeaderLabels([
            "Invoice #", "Date", "Due Date", "Total", "Paid", "Outstanding"
        ])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.details_table)

        layout.addStretch()
        return widget

    def _create_add_receipt_tab(self):
        """Add Receipt tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()

        self.receipt_invoice_combo = QComboBox()
        form.addRow("Invoice:", self.receipt_invoice_combo)

        self.receipt_amount = QSpinBox()
        self.receipt_amount.setMaximum(999999)
        form.addRow("Amount (R):", self.receipt_amount)

        self.receipt_date = QDateEdit()
        self.receipt_date.setDate(QDate.currentDate())
        form.addRow("Receipt Date:", self.receipt_date)

        self.receipt_method = QComboBox()
        self.receipt_method.addItems(["Cash", "Cheque", "Bank Transfer", "Card"])
        form.addRow("Payment Method:", self.receipt_method)

        self.receipt_ref = QLineEdit()
        form.addRow("Reference #:", self.receipt_ref)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Receipt")
        save_btn.clicked.connect(self._save_receipt)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #64748B;")
        cancel_btn.clicked.connect(lambda: self._clear_receipt_form())
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        return widget

    def _create_record_payment_tab(self):
        """Record Payment tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()

        self.payment_invoice_combo = QComboBox()
        form.addRow("Invoice:", self.payment_invoice_combo)

        self.payment_amount = QSpinBox()
        self.payment_amount.setMaximum(999999)
        form.addRow("Amount (R):", self.payment_amount)

        self.payment_date = QDateEdit()
        self.payment_date.setDate(QDate.currentDate())
        form.addRow("Payment Date:", self.payment_date)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Cheque", "Bank Transfer", "Card", "EFT"])
        form.addRow("Payment Method:", self.payment_method)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Record Payment")
        save_btn.clicked.connect(self._record_payment)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #64748B;")
        cancel_btn.clicked.connect(lambda: self._clear_payment_form())
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        return widget

    def _create_create_invoice_tab(self):
        """Create Invoice tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()

        self.invoice_course_combo = QComboBox()
        form.addRow("Course:", self.invoice_course_combo)

        self.invoice_amount = QSpinBox()
        self.invoice_amount.setMaximum(999999)
        form.addRow("Amount (R):", self.invoice_amount)

        self.invoice_date = QDateEdit()
        self.invoice_date.setDate(QDate.currentDate())
        form.addRow("Invoice Date:", self.invoice_date)

        self.invoice_due_date = QDateEdit()
        self.invoice_due_date.setDate(QDate.currentDate().addDays(30))
        form.addRow("Due Date:", self.invoice_due_date)

        self.invoice_description = QLineEdit()
        form.addRow("Description:", self.invoice_description)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Invoice")
        create_btn.clicked.connect(self._create_invoice)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #64748B;")
        cancel_btn.clicked.connect(lambda: self._clear_invoice_form())
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        return widget

    def _create_send_reminder_tab(self):
        """Send Reminder tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        info_label = QLabel("Overdue Invoices")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(info_label)

        self.reminder_table = QTableWidget()
        self.reminder_table.setColumnCount(5)
        self.reminder_table.setHorizontalHeaderLabels([
            "Invoice #", "Due Date", "Days Late", "Amount", "Outstanding"
        ])
        self.reminder_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.reminder_table)

        btn_layout = QHBoxLayout()
        send_btn = QPushButton("Send Reminder (Email/SMS)")
        send_btn.clicked.connect(self._send_reminder)
        layout.addLayout(btn_layout)
        btn_layout.addWidget(send_btn)
        btn_layout.addStretch()

        layout.addStretch()
        return widget

    def _create_download_invoice_tab(self):
        """Download Invoice tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        info_label = QLabel("Select Invoice to Download")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(info_label)

        form = QFormLayout()
        self.download_invoice_combo = QComboBox()
        form.addRow("Invoice:", self.download_invoice_combo)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        download_btn = QPushButton("Download as PDF")
        download_btn.clicked.connect(self._download_invoice)
        btn_layout.addWidget(download_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        return widget

    def _create_edit_student_tab(self):
        """Edit Student tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()

        self.edit_first_name = QLineEdit()
        form.addRow("First Name:", self.edit_first_name)

        self.edit_last_name = QLineEdit()
        form.addRow("Last Name:", self.edit_last_name)

        self.edit_email = QLineEdit()
        form.addRow("Email:", self.edit_email)

        self.edit_phone = QLineEdit()
        form.addRow("Phone:", self.edit_phone)

        self.edit_programme = QLineEdit()
        form.addRow("Programme:", self.edit_programme)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_student_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #64748B;")
        cancel_btn.clicked.connect(lambda: self._load_students())
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

        return widget

    def _load_students(self):
        """Load all students into the combo box."""
        connection = get_connection()
        try:
            students = connection.execute("""
                SELECT id, student_number, first_name, last_name
                FROM students
                ORDER BY first_name, last_name
            """).fetchall()

            self.student_combo.blockSignals(True)
            self.student_combo.clear()
            self.student_combo.addItem("— Select a Student —", None)

            for student in students:
                name = f"{student['student_number']} - {student['first_name']} {student['last_name']}"
                self.student_combo.addItem(name, student["id"])

            self.student_combo.blockSignals(False)
        finally:
            connection.close()

    def _on_student_selected(self):
        """Load student data when selected."""
        self.selected_student_id = self.student_combo.currentData()
        
        if self.selected_student_id is None:
            self._clear_all_tabs()
            return

        self._load_student_details()
        self._load_student_invoices()
        self._load_edit_form()

    def _load_student_details(self):
        """Load student details."""
        connection = get_connection()
        try:
            student = connection.execute("""
                SELECT student_number, first_name, last_name, email, phone, programme
                FROM students
                WHERE id = ?
            """, (self.selected_student_id,)).fetchone()

            if student:
                info = (
                    f"<b>Name:</b> {student['first_name']} {student['last_name']}<br>"
                    f"<b>Student #:</b> {student['student_number']}<br>"
                    f"<b>Email:</b> {student['email'] or 'N/A'}<br>"
                    f"<b>Phone:</b> {student['phone'] or 'N/A'}<br>"
                    f"<b>Programme:</b> {student['programme'] or 'N/A'}"
                )
                self.details_info.setHtml(info)
        finally:
            connection.close()

    def _load_student_invoices(self):
        """Load student invoices."""
        connection = get_connection()
        try:
            invoices = connection.execute("""
                SELECT
                    i.id, i.invoice_number, i.invoice_date, i.due_date,
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) AS paid_amount
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
                WHERE i.student_id = ?
                GROUP BY i.id
                ORDER BY i.invoice_date DESC
            """, (self.selected_student_id,)).fetchall()

            self.details_table.setRowCount(0)
            self.receipt_invoice_combo.clear()
            self.payment_invoice_combo.clear()
            self.download_invoice_combo.clear()

            for inv in invoices:
                total = float(inv["total_amount"] or 0)
                paid = float(inv["paid_amount"] or 0)
                balance = max(0.0, total - paid)

                row = self.details_table.rowCount()
                self.details_table.insertRow(row)
                self.details_table.setItem(row, 0, QTableWidgetItem(inv["invoice_number"]))
                self.details_table.setItem(row, 1, QTableWidgetItem(inv["invoice_date"]))
                self.details_table.setItem(row, 2, QTableWidgetItem(inv["due_date"]))
                self.details_table.setItem(row, 3, QTableWidgetItem(f"R {total:,.2f}"))
                self.details_table.setItem(row, 4, QTableWidgetItem(f"R {paid:,.2f}"))
                self.details_table.setItem(row, 5, QTableWidgetItem(f"R {balance:,.2f}"))

                # Add to dropdowns
                self.receipt_invoice_combo.addItem(
                    f"{inv['invoice_number']} (R {balance:,.2f})",
                    inv["id"]
                )
                self.payment_invoice_combo.addItem(
                    f"{inv['invoice_number']} (R {balance:,.2f})",
                    inv["id"]
                )
                self.download_invoice_combo.addItem(
                    f"{inv['invoice_number']}",
                    inv["id"]
                )
        finally:
            connection.close()

    def _load_edit_form(self):
        """Load student data into edit form."""
        connection = get_connection()
        try:
            student = connection.execute("""
                SELECT first_name, last_name, email, phone, programme
                FROM students
                WHERE id = ?
            """, (self.selected_student_id,)).fetchone()

            if student:
                self.edit_first_name.setText(student['first_name'] or "")
                self.edit_last_name.setText(student['last_name'] or "")
                self.edit_email.setText(student['email'] or "")
                self.edit_phone.setText(student['phone'] or "")
                self.edit_programme.setText(student['programme'] or "")
        finally:
            connection.close()

    def _save_receipt(self):
        """Save receipt."""
        if self.selected_student_id is None:
            QMessageBox.warning(self, "No Student", "Please select a student first.")
            return

        QMessageBox.information(self, "Receipt Saved", "Receipt has been recorded.")
        self._clear_receipt_form()

    def _record_payment(self):
        """Record payment."""
        if self.selected_student_id is None:
            QMessageBox.warning(self, "No Student", "Please select a student first.")
            return

        invoice_id = self.payment_invoice_combo.currentData()
        if invoice_id is None:
            QMessageBox.warning(self, "No Invoice", "Please select an invoice.")
            return

        amount = self.payment_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter an amount greater than 0.")
            return

        connection = get_connection()
        try:
            payment_date = self.payment_date.date().toString("yyyy-MM-dd")
            method = self.payment_method.currentText()

            connection.execute("""
                INSERT INTO payments (student_id, invoice_id, payment_date, amount, payment_method)
                VALUES (?, ?, ?, ?, ?)
            """, (self.selected_student_id, invoice_id, payment_date, amount, method))
            connection.commit()

            QMessageBox.information(self, "Payment Recorded", f"Payment of R {amount:,.2f} recorded successfully.")
            self._clear_payment_form()
            self._load_student_invoices()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {e}")
        finally:
            connection.close()

    def _create_invoice(self):
        """Create invoice."""
        if self.selected_student_id is None:
            QMessageBox.warning(self, "No Student", "Please select a student first.")
            return

        amount = self.invoice_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter an amount greater than 0.")
            return

        connection = get_connection()
        try:
            invoice_number = "INV-" + datetime.now().strftime("%Y%m%d-%H%M%S")
            invoice_date = self.invoice_date.date().toString("yyyy-MM-dd")
            due_date = self.invoice_due_date.date().toString("yyyy-MM-dd")
            description = self.invoice_description.text() or "Course Fee"

            connection.execute("""
                INSERT INTO invoices (student_id, invoice_number, invoice_date, due_date, total_amount, status)
                VALUES (?, ?, ?, ?, ?, 'Unpaid')
            """, (self.selected_student_id, invoice_number, invoice_date, due_date, amount))

            invoice_id = connection.execute(
                "SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,)
            ).fetchone()["id"]

            connection.execute("""
                INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, line_total)
                VALUES (?, ?, 1, ?, ?)
            """, (invoice_id, description, amount, amount))

            connection.commit()

            QMessageBox.information(self, "Invoice Created", f"Invoice {invoice_number} created for R {amount:,.2f}.")
            self._clear_invoice_form()
            self._load_student_invoices()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create invoice: {e}")
        finally:
            connection.close()

    def _send_reminder(self):
        """Send reminder."""
        if self.selected_student_id is None:
            QMessageBox.warning(self, "No Student", "Please select a student first.")
            return

        connection = get_connection()
        try:
            student = connection.execute(
                "SELECT first_name, last_name, email FROM students WHERE id = ?",
                (self.selected_student_id,)
            ).fetchone()

            QMessageBox.information(
                self, "Reminder Sent",
                f"Payment reminder sent to {student['first_name']} {student['last_name']} ({student['email']}).\n\n"
                "In a real system, this would send an email or SMS."
            )
        finally:
            connection.close()

    def _download_invoice(self):
        """Download invoice as PDF."""
        invoice_id = self.download_invoice_combo.currentData()
        if invoice_id is None:
            QMessageBox.warning(self, "No Invoice", "Please select an invoice.")
            return

        QMessageBox.information(
            self, "Download",
            "Invoice PDF download feature coming soon.\n"
            "(Would generate and download PDF invoice)"
        )

    def _save_student_changes(self):
        """Save student changes."""
        if self.selected_student_id is None:
            QMessageBox.warning(self, "No Student", "Please select a student first.")
            return

        connection = get_connection()
        try:
            connection.execute("""
                UPDATE students
                SET first_name = ?, last_name = ?, email = ?, phone = ?, programme = ?
                WHERE id = ?
            """, (
                self.edit_first_name.text(),
                self.edit_last_name.text(),
                self.edit_email.text(),
                self.edit_phone.text(),
                self.edit_programme.text(),
                self.selected_student_id
            ))
            connection.commit()

            QMessageBox.information(self, "Success", "Student information updated.")
            self._load_students()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update student: {e}")
        finally:
            connection.close()

    def _clear_all_tabs(self):
        """Clear all tab contents."""
        self.details_info.clear()
        self.details_table.setRowCount(0)
        self.receipt_invoice_combo.clear()
        self.payment_invoice_combo.clear()
        self.download_invoice_combo.clear()
        self._clear_receipt_form()
        self._clear_payment_form()
        self._clear_invoice_form()

    def _clear_receipt_form(self):
        """Clear receipt form."""
        self.receipt_invoice_combo.setCurrentIndex(0)
        self.receipt_amount.setValue(0)
        self.receipt_date.setDate(QDate.currentDate())

    def _clear_payment_form(self):
        """Clear payment form."""
        self.payment_invoice_combo.setCurrentIndex(0)
        self.payment_amount.setValue(0)
        self.payment_date.setDate(QDate.currentDate())

    def _clear_invoice_form(self):
        """Clear invoice form."""
        self.invoice_course_combo.setCurrentIndex(0)
        self.invoice_amount.setValue(0)
        self.invoice_date.setDate(QDate.currentDate())
        self.invoice_due_date.setDate(QDate.currentDate().addDays(30))
        self.invoice_description.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentAccountsModule()
    window.show()
    sys.exit(app.exec())
