import sys
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_connection


class StudentStatementsModule(QMainWindow):
    """
    Student Account Statements — View student payment history,
    balances, and generate printable statements.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Student Statements")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6FA;
            }
            QLabel {
                color: #243247;
                font-size: 13px;
            }
            QComboBox, QLineEdit {
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
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Back button at top
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.setStyleSheet("background-color: #64748B;")
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)

        heading = QLabel("STUDENT ACCOUNT STATEMENTS")
        heading.setStyleSheet(
            "font-size: 25px; font-weight: bold; color: #183153;"
        )
        subtitle = QLabel(
            "View student payment history, balances, and generate statements."
        )
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        # Student search/select
        form = QFormLayout()
        form.setSpacing(10)

        self.student_combo = QComboBox()
        self.student_combo.currentIndexChanged.connect(self._load_statement)

        form.addRow("Select Student:", self.student_combo)
        layout.addLayout(form)

        # Student info display
        self.info_label = QLabel("Select a student to view their statement.")
        self.info_label.setStyleSheet(
            "font-size: 14px; padding: 15px; background-color: white; "
            "border: 1px solid #CBD5E1; border-radius: 5px;"
        )
        layout.addWidget(self.info_label)

        # Summary section
        summary_layout = QHBoxLayout()

        self.total_label = QLabel("Total Owing: R 0.00")
        self.total_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #DC2626; "
            "padding: 15px; background-color: white; "
            "border: 1px solid #CBD5E1; border-radius: 5px;"
        )

        self.paid_label = QLabel("Total Paid: R 0.00")
        self.paid_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #16A34A; "
            "padding: 15px; background-color: white; "
            "border: 1px solid #CBD5E1; border-radius: 5px;"
        )

        self.balance_label = QLabel("Balance: R 0.00")
        self.balance_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #D97706; "
            "padding: 15px; background-color: white; "
            "border: 1px solid #CBD5E1; border-radius: 5px;"
        )

        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(self.paid_label)
        summary_layout.addWidget(self.balance_label)
        layout.addLayout(summary_layout)

        # Invoices section
        inv_label = QLabel("Invoices")
        inv_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(inv_label)

        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels([
            "Invoice Number", "Date", "Due Date",
            "Total", "Paid", "Balance"
        ])
        self.invoices_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.invoices_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.invoices_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.invoices_table.setMaximumHeight(200)
        layout.addWidget(self.invoices_table)

        # Payments section
        pay_label = QLabel("Payment History")
        pay_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(pay_label)

        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)
        self.payments_table.setHorizontalHeaderLabels([
            "Date", "Receipt Number", "Amount",
            "Method", "Reference"
        ])
        self.payments_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.payments_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.payments_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.payments_table)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.print_btn = QPushButton("Print / Download Statement")
        self.print_btn.clicked.connect(self._print_statement)
        self.print_btn.setEnabled(False)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background-color: #64748B;")
        refresh_btn.clicked.connect(self._load_statement)

        btn_layout.addWidget(self.print_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_students(self):
        connection = get_connection()
        try:
            students = connection.execute("""
                SELECT id, student_number, first_name, last_name
                FROM students
                ORDER BY first_name, last_name
            """).fetchall()

            self.student_combo.blockSignals(True)
            self.student_combo.clear()
            self.student_combo.addItem("— Select a student —", None)

            for s in students:
                self.student_combo.addItem(
                    f"{s['student_number']} — "
                    f"{s['first_name']} {s['last_name']}",
                    s["id"]
                )
            self.student_combo.blockSignals(False)
        finally:
            connection.close()

    def _load_statement(self, *_):
        self.selected_student_id = self.student_combo.currentData()

        if self.selected_student_id is None:
            self.info_label.setText("Select a student to view their statement.")
            self.total_label.setText("Total Owing: R 0.00")
            self.paid_label.setText("Total Paid: R 0.00")
            self.balance_label.setText("Balance: R 0.00")
            self.invoices_table.setRowCount(0)
            self.payments_table.setRowCount(0)
            self.print_btn.setEnabled(False)
            return

        connection = get_connection()
        try:
            # Get student details
            student = connection.execute("""
                SELECT
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    s.email,
                    s.phone,
                    s.programme
                FROM students s
                WHERE s.id = ?
            """, (self.selected_student_id,)).fetchone()

            if not student:
                self.info_label.setText("Student not found.")
                return

            info_text = (
                f"<b>{student['first_name']} {student['last_name']}</b> "
                f"({student['student_number']})<br>"
                f"Programme: {student['programme'] or 'N/A'}<br>"
                f"Email: {student['email'] or 'N/A'} | "
                f"Phone: {student['phone'] or 'N/A'}"
            )
            self.info_label.setText(info_text)

            # Get invoices
            invoices = connection.execute("""
                SELECT
                    i.invoice_number,
                    i.invoice_date,
                    i.due_date,
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) AS paid_amount
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
                WHERE i.student_id = ?
                GROUP BY i.id
                ORDER BY i.invoice_date DESC
            """, (self.selected_student_id,)).fetchall()

            self.invoices_table.setRowCount(0)
            total_owing = 0.0
            total_paid = 0.0

            for inv in invoices:
                total = float(inv["total_amount"] or 0)
                paid = float(inv["paid_amount"] or 0)
                balance = max(0.0, total - paid)

                total_owing += total
                total_paid += paid

                row = self.invoices_table.rowCount()
                self.invoices_table.insertRow(row)
                self.invoices_table.setItem(
                    row, 0, QTableWidgetItem(inv["invoice_number"])
                )
                self.invoices_table.setItem(
                    row, 1, QTableWidgetItem(inv["invoice_date"])
                )
                self.invoices_table.setItem(
                    row, 2, QTableWidgetItem(inv["due_date"])
                )
                self.invoices_table.setItem(
                    row, 3, QTableWidgetItem(f"R {total:,.2f}")
                )
                self.invoices_table.setItem(
                    row, 4, QTableWidgetItem(f"R {paid:,.2f}")
                )
                self.invoices_table.setItem(
                    row, 5, QTableWidgetItem(f"R {balance:,.2f}")
                )

            # Get payments
            payments = connection.execute("""
                SELECT
                    p.payment_date,
                    p.reference_number,
                    p.amount,
                    p.payment_method
                FROM payments p
                WHERE p.student_id = ?
                ORDER BY p.payment_date DESC, p.id DESC
            """, (self.selected_student_id,)).fetchall()

            self.payments_table.setRowCount(0)
            for pay in payments:
                row = self.payments_table.rowCount()
                self.payments_table.insertRow(row)
                self.payments_table.setItem(
                    row, 0, QTableWidgetItem(pay["payment_date"])
                )
                self.payments_table.setItem(
                    row, 1, QTableWidgetItem(pay["reference_number"] or "")
                )
                self.payments_table.setItem(
                    row, 2, QTableWidgetItem(f"R {pay['amount']:,.2f}")
                )
                self.payments_table.setItem(
                    row, 3, QTableWidgetItem(pay["payment_method"] or "")
                )
                self.payments_table.setItem(
                    row, 4, QTableWidgetItem("")
                )

            outstanding = max(0.0, total_owing - total_paid)

            self.total_label.setText(f"Total Owing: R {total_owing:,.2f}")
            self.paid_label.setText(f"Total Paid: R {total_paid:,.2f}")
            self.balance_label.setText(f"Balance: R {outstanding:,.2f}")

            self.print_btn.setEnabled(True)

        except Exception as error:
            QMessageBox.critical(
                self, "Load Error", f"Failed to load statement: {error}"
            )
        finally:
            connection.close()

    def _print_statement(self):
        if self.selected_student_id is None:
            return

        connection = get_connection()
        try:
            # Get all data again for the statement
            student = connection.execute("""
                SELECT
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    s.email,
                    s.phone,
                    s.programme
                FROM students s
                WHERE s.id = ?
            """, (self.selected_student_id,)).fetchone()

            invoices = connection.execute("""
                SELECT
                    i.invoice_number,
                    i.invoice_date,
                    i.due_date,
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) AS paid_amount
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
                WHERE i.student_id = ?
                GROUP BY i.id
                ORDER BY i.invoice_date DESC
            """, (self.selected_student_id,)).fetchall()

            payments = connection.execute("""
                SELECT
                    p.payment_date,
                    p.reference_number,
                    p.amount,
                    p.payment_method
                FROM payments p
                WHERE p.student_id = ?
                ORDER BY p.payment_date DESC, p.id DESC
            """, (self.selected_student_id,)).fetchall()

            # Build HTML statement
            html = self._build_statement_html(student, invoices, payments)

            # Print or save as PDF
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPrinter.PageSize.A4)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)

            # Default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = (
                f"Statement_{student['student_number']}_"
                f"{timestamp}.pdf"
            )
            printer.setOutputFileName(str(Path.home() / "Desktop" / filename))

            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                doc = QTextDocument()
                doc.setHtml(html)
                doc.print(printer)

                QMessageBox.information(
                    self,
                    "Statement Generated",
                    f"Statement saved to:\n{printer.outputFileName()}"
                )

        except Exception as error:
            QMessageBox.critical(
                self, "Print Error", f"Failed to generate statement: {error}"
            )
        finally:
            connection.close()

    def _build_statement_html(self, student, invoices, payments):
        """Build HTML for the student statement."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        total_owing = 0.0
        total_paid = 0.0
        for inv in invoices:
            total_owing += float(inv["total_amount"] or 0)
            total_paid += float(inv["paid_amount"] or 0)
        outstanding = max(0.0, total_owing - total_paid)

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    margin: 20px;
                }}
                h1 {{
                    color: #172B4D;
                    font-size: 22pt;
                    margin-bottom: 5px;
                }}
                h2 {{
                    color: #344D70;
                    font-size: 14pt;
                    margin-top: 20px;
                    margin-bottom: 10px;
                    border-bottom: 2px solid #CBD5E1;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                th {{
                    background-color: #172B4D;
                    color: white;
                    padding: 8px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 6px;
                    border-bottom: 1px solid #E2E8F0;
                }}
                .summary {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #F4F6FA;
                    border: 1px solid #CBD5E1;
                    border-radius: 5px;
                }}
                .summary-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 5px 0;
                    font-size: 12pt;
                }}
                .summary-row.total {{
                    font-size: 14pt;
                    font-weight: bold;
                    border-top: 2px solid #172B4D;
                    padding-top: 10px;
                    margin-top: 10px;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 9pt;
                    color: #64748B;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <h1>LISTEC COLLEGE</h1>
            <p style="color: #64748B; margin-top: 0;">Student Account Statement</p>
            <p style="font-size: 9pt; color: #64748B;">Generated: {now}</p>

            <h2>Student Information</h2>
            <p>
                <strong>Name:</strong> {student['first_name']} {student['last_name']}<br>
                <strong>Student Number:</strong> {student['student_number']}<br>
                <strong>Programme:</strong> {student['programme'] or 'N/A'}<br>
                <strong>Email:</strong> {student['email'] or 'N/A'}<br>
                <strong>Phone:</strong> {student['phone'] or 'N/A'}
            </p>

            <h2>Invoices</h2>
            <table>
                <thead>
                    <tr>
                        <th>Invoice Number</th>
                        <th>Date</th>
                        <th>Due Date</th>
                        <th>Total</th>
                        <th>Paid</th>
                        <th>Balance</th>
                    </tr>
                </thead>
                <tbody>
        """

        for inv in invoices:
            total = float(inv["total_amount"] or 0)
            paid = float(inv["paid_amount"] or 0)
            balance = max(0.0, total - paid)
            html += f"""
                    <tr>
                        <td>{inv['invoice_number']}</td>
                        <td>{inv['invoice_date']}</td>
                        <td>{inv['due_date']}</td>
                        <td>R {total:,.2f}</td>
                        <td>R {paid:,.2f}</td>
                        <td>R {balance:,.2f}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>

            <h2>Payment History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Receipt Number</th>
                        <th>Amount</th>
                        <th>Method</th>
                    </tr>
                </thead>
                <tbody>
        """

        for pay in payments:
            html += f"""
                    <tr>
                        <td>{pay['payment_date']}</td>
                        <td>{pay['reference_number'] or 'N/A'}</td>
                        <td>R {pay['amount']:,.2f}</td>
                        <td>{pay['payment_method'] or 'N/A'}</td>
                    </tr>
            """

        html += f"""
                </tbody>
            </table>

            <div class="summary">
                <div class="summary-row">
                    <span>Total Invoiced:</span>
                    <span>R {total_owing:,.2f}</span>
                </div>
                <div class="summary-row">
                    <span>Total Paid:</span>
                    <span style="color: #16A34A;">R {total_paid:,.2f}</span>
                </div>
                <div class="summary-row total">
                    <span>Outstanding Balance:</span>
                    <span style="color: #DC2626;">R {outstanding:,.2f}</span>
                </div>
            </div>

            <div class="footer">
                <p>LISTEC College Financial Management System</p>
                <p>This is a computer-generated statement.</p>
            </div>
        </body>
        </html>
        """

        return html


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentStatementsModule()
    window.show()
    sys.exit(app.exec())
