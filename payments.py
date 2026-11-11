
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDoubleSpinBox,
    QComboBox,
    QDateEdit,
    QMessageBox,
)

from database.db import get_connection


class PaymentsModule(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Payments & Receipts")
        self.resize(1150, 750)
        self.setMinimumSize(900, 600)

        self.selected_invoice_id = None
        self.selected_balance = 0.0

        self.create_payments_table()
        self.create_interface()
        self.load_invoices()

    def create_payments_table(self):
        connection = get_connection()

        try:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    receipt_number TEXT NOT NULL UNIQUE,
                    payment_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    reference TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id)
                        REFERENCES invoices(id)
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_payments_invoice_id
                ON payments(invoice_id)
            """)

            connection.commit()

        finally:
            connection.close()

    def create_interface(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        # Back button at top
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.setStyleSheet("background-color: #64748B;")
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)

        heading = QLabel("PAYMENTS & RECEIPTS")
        heading.setStyleSheet(
            "font-size: 25px; font-weight: bold; color: #183153;"
        )
        layout.addWidget(heading)

        subtitle = QLabel(
            "Record student payments and manage outstanding invoices."
        )
        layout.addWidget(subtitle)

        search_layout = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search by student number, student name or invoice number..."
        )
        self.search_box.textChanged.connect(self.load_invoices)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_invoices)

        search_layout.addWidget(self.search_box)
        search_layout.addWidget(refresh_button)

        layout.addLayout(search_layout)

        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(9)
        self.invoice_table.setHorizontalHeaderLabels([
            "ID",
            "Student Number",
            "Student Name",
            "Invoice Number",
            "Invoice Date",
            "Invoice Total",
            "Paid",
            "Outstanding",
            "Status",
        ])

        self.invoice_table.setColumnHidden(0, True)
        self.invoice_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.invoice_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.invoice_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.invoice_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.invoice_table.itemSelectionChanged.connect(
            self.select_invoice
        )

        layout.addWidget(QLabel("Student Invoices"))
        layout.addWidget(self.invoice_table)

        payment_heading = QLabel("Record a Payment")
        payment_heading.setStyleSheet(
            "font-size: 19px; font-weight: bold;"
        )
        layout.addWidget(payment_heading)

        form = QFormLayout()

        self.selected_invoice_label = QLabel("No invoice selected")
        self.balance_label = QLabel("R 0.00")

        self.payment_amount = QDoubleSpinBox()
        self.payment_amount.setRange(0.01, 999999999)
        self.payment_amount.setDecimals(2)
        self.payment_amount.setPrefix("R ")
        self.payment_amount.setMaximum(0.01)

        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())

        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Cash",
            "EFT",
            "Card",
            "Other",
        ])

        self.reference_field = QLineEdit()
        self.reference_field.setPlaceholderText(
            "Optional payment reference"
        )

        form.addRow("Selected Invoice:", self.selected_invoice_label)
        form.addRow("Outstanding Balance:", self.balance_label)
        form.addRow("Payment Amount:", self.payment_amount)
        form.addRow("Payment Date:", self.payment_date)
        form.addRow("Payment Method:", self.payment_method)
        form.addRow("Reference:", self.reference_field)

        layout.addLayout(form)

        button_layout = QHBoxLayout()

        self.record_button = QPushButton("Record Payment")
        self.record_button.clicked.connect(self.record_payment)
        self.record_button.setEnabled(False)

        clear_button = QPushButton("Clear Selection")
        clear_button.clicked.connect(self.clear_selection)

        button_layout.addWidget(self.record_button)
        button_layout.addWidget(clear_button)

        layout.addLayout(button_layout)

    def load_invoices(self, *_):
        connection = get_connection()

        try:
            search = f"%{self.search_box.text().strip()}%"

            records = connection.execute("""
                SELECT
                    i.id AS invoice_id,
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    i.invoice_number,
                    i.invoice_date,
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) AS paid_amount
                FROM invoices i
                JOIN students s ON i.student_id = s.id
                LEFT JOIN payments p ON p.invoice_id = i.id
                WHERE s.student_number LIKE ?
                   OR s.first_name LIKE ?
                   OR s.last_name LIKE ?
                   OR i.invoice_number LIKE ?
                GROUP BY i.id
                ORDER BY i.invoice_date DESC, i.id DESC
            """, (search, search, search, search)).fetchall()

            self.invoice_table.setRowCount(0)

            for record in records:
                row = self.invoice_table.rowCount()
                self.invoice_table.insertRow(row)

                total = float(record["total_amount"] or 0)
                paid = float(record["paid_amount"] or 0)
                balance = max(0.0, total - paid)

                if balance <= 0.005:
                    status = "Paid"
                elif paid > 0:
                    status = "Partially Paid"
                else:
                    status = "Unpaid"

                values = [
                    record["invoice_id"],
                    record["student_number"],
                    f"{record['first_name']} {record['last_name']}",
                    record["invoice_number"],
                    record["invoice_date"],
                    f"R {total:,.2f}",
                    f"R {paid:,.2f}",
                    f"R {balance:,.2f}",
                    status,
                ]

                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))

                    if column == 0:
                        item.setData(
                            Qt.ItemDataRole.UserRole,
                            record["invoice_id"]
                        )

                    if column == 7:
                        item.setData(
                            Qt.ItemDataRole.UserRole,
                            balance
                        )

                    self.invoice_table.setItem(row, column, item)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Invoice Loading Error",
                str(error)
            )

        finally:
            connection.close()

    def select_invoice(self):
        row = self.invoice_table.currentRow()

        if row < 0:
            return

        invoice_item = self.invoice_table.item(row, 0)
        balance_item = self.invoice_table.item(row, 7)

        self.selected_invoice_id = invoice_item.data(
            Qt.ItemDataRole.UserRole
        )

        self.selected_balance = float(
            balance_item.data(Qt.ItemDataRole.UserRole) or 0
        )

        invoice_number = self.invoice_table.item(row, 3).text()

        self.selected_invoice_label.setText(invoice_number)
        self.balance_label.setText(
            f"R {self.selected_balance:,.2f}"
        )

        if self.selected_balance > 0.005:
            self.payment_amount.setMaximum(self.selected_balance)
            self.payment_amount.setValue(self.selected_balance)
            self.record_button.setEnabled(True)
        else:
            self.payment_amount.setMaximum(0.01)
            self.payment_amount.setValue(0)
            self.record_button.setEnabled(False)

    def clear_selection(self):
        self.invoice_table.clearSelection()

        self.selected_invoice_id = None
        self.selected_balance = 0.0

        self.selected_invoice_label.setText("No invoice selected")
        self.balance_label.setText("R 0.00")

        self.payment_amount.setMaximum(0.01)
        self.payment_amount.setValue(0)

        self.record_button.setEnabled(False)
        self.reference_field.clear()

    def record_payment(self):
        if self.selected_invoice_id is None:
            QMessageBox.warning(
                self,
                "Select Invoice",
                "Please select an invoice first."
            )
            return

        amount = self.payment_amount.value()

        if amount <= 0:
            QMessageBox.warning(
                self,
                "Invalid Amount",
                "Please enter a payment amount greater than zero."
            )
            return

        connection = get_connection()

        try:
            cursor = connection.cursor()

            invoice = cursor.execute("""
                SELECT total_amount
                FROM invoices
                WHERE id = ?
            """, (self.selected_invoice_id,)).fetchone()

            if invoice is None:
                raise Exception("The selected invoice no longer exists.")

            paid = cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS total_paid
                FROM payments
                WHERE invoice_id = ?
            """, (self.selected_invoice_id,)).fetchone()

            total = float(invoice["total_amount"] or 0)
            already_paid = float(paid["total_paid"] or 0)
            outstanding = max(0.0, total - already_paid)

            if amount > outstanding + 0.005:
                QMessageBox.warning(
                    self,
                    "Payment Too High",
                    f"The outstanding balance is R {outstanding:,.2f}."
                )
                return

            receipt_number = (
                "RCT-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            )

            payment_date = self.payment_date.date().toString(
                "yyyy-MM-dd"
            )

            method = self.payment_method.currentText()
            reference = self.reference_field.text().strip()

            # Fetch student_id for this invoice (required by live schema)
            invoice_row = cursor.execute("""
                SELECT student_id FROM invoices WHERE id = ?
            """, (self.selected_invoice_id,)).fetchone()

            cursor.execute("""
                INSERT INTO payments (
                    student_id,
                    invoice_id,
                    payment_date,
                    amount,
                    payment_method,
                    reference_number
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                invoice_row["student_id"],
                self.selected_invoice_id,
                payment_date,
                amount,
                method,
                reference,
            ))

            new_paid = already_paid + amount

            if total - new_paid <= 0.005:
                status = "Paid"
            else:
                status = "Partially Paid"

            cursor.execute("""
                UPDATE invoices
                SET status = ?
                WHERE id = ?
            """, (status, self.selected_invoice_id))

            connection.commit()

            receipt_text = self.get_receipt_text(
                receipt_number,
                self.selected_invoice_id,
                amount,
                payment_date,
                method,
                reference,
                total,
                new_paid,
                max(0.0, total - new_paid),
            )

            QMessageBox.information(
                self,
                "Payment Recorded",
                "Payment recorded successfully.\n\n"
                f"Receipt Number: {receipt_number}\n"
                f"Amount Received: R {amount:,.2f}\n"
                f"Remaining Balance: R {max(0.0, total - new_paid):,.2f}"
            )

            answer = QMessageBox.question(
                self,
                "Print Receipt",
                "Would you like to print this payment receipt?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            )

            if answer == QMessageBox.StandardButton.Yes:
                self.print_receipt(receipt_text)

            self.clear_selection()
            self.load_invoices()

        except Exception as error:
            connection.rollback()
            QMessageBox.critical(
                self,
                "Payment Error",
                str(error)
            )

        finally:
            connection.close()

    def get_receipt_text(
        self,
        receipt_number,
        invoice_id,
        amount,
        payment_date,
        method,
        reference,
        total,
        paid,
        balance
    ):
        connection = get_connection()

        try:
            details = connection.execute("""
                SELECT
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    i.invoice_number
                FROM invoices i
                JOIN students s ON i.student_id = s.id
                WHERE i.id = ?
            """, (invoice_id,)).fetchone()

            if details is None:
                raise Exception("Student or invoice details not found.")

            return f"""
            <html>
            <body style="font-family: Arial; padding: 25px;">
                <h1 style="text-align: center;">LISTEC COLLEGE</h1>
                <h2 style="text-align: center;">OFFICIAL PAYMENT RECEIPT</h2>
                <hr>
                <p><b>Receipt Number:</b> {receipt_number}</p>
                <p><b>Payment Date:</b> {payment_date}</p>
                <p><b>Student Number:</b> {details['student_number']}</p>
                <p><b>Student Name:</b>
                {details['first_name']} {details['last_name']}</p>
                <p><b>Invoice Number:</b> {details['invoice_number']}</p>
                <hr>
                <h2>Payment Details</h2>
                <p><b>Amount Received:</b> R {amount:,.2f}</p>
                <p><b>Payment Method:</b> {method}</p>
                <p><b>Reference:</b> {reference or 'N/A'}</p>
                <hr>
                <p><b>Invoice Total:</b> R {total:,.2f}</p>
                <p><b>Total Paid:</b> R {paid:,.2f}</p>
                <p><b>Outstanding Balance:</b> R {balance:,.2f}</p>
                <hr>
                <p style="text-align: center;">
                    Thank you for your payment.
                </p>
                <p style="text-align: center;">
                    LISTEC COLLEGE
                </p>
            </body>
            </html>
            """

        finally:
            connection.close()

    def print_receipt(self, receipt_text):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            document = QTextDocument()
            document.setHtml(receipt_text)
            document.print(printer)
