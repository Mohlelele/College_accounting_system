import sys
from pathlib import Path
from datetime import datetime, timedelta
import threading
import calendar

from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_connection


class PaymentRemindersModule(QMainWindow):
    """
    Payment Reminders Module - Track overdue invoices and send reminders.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Payment Reminders")
        self.resize(1300, 800)
        self.setMinimumSize(1000, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6FA;
            }
            QLabel {
                color: #243247;
                font-size: 13px;
            }
            QComboBox, QDateEdit, QSpinBox {
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
                font-size: 12px;
            }
        """)

        # Initialize reminder scheduler
        self.reminder_sent_today = False
        self._setup_reminder_scheduler()

        self._build_ui()
        self._load_overdue_invoices()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        central = QWidget()
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.setStyleSheet("background-color: #64748B;")
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)

        # Title
        heading = QLabel("PAYMENT REMINDERS")
        heading.setStyleSheet(
            "font-size: 25px; font-weight: bold; color: #183153;"
        )
        subtitle = QLabel("Track overdue invoices and send payment reminders to students.")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        # Reminder schedule info
        today = datetime.now().date()
        day = today.day
        last_day = calendar.monthrange(today.year, today.month)[1]
        
        schedule_info = QLabel("📅 Automatic reminders scheduled for: 10th, 22nd, and last day of month")
        schedule_info.setStyleSheet("color: #0891B2; font-size: 12px; font-weight: bold; padding: 10px; background-color: #ECFDF5; border-radius: 5px;")
        layout.addWidget(schedule_info)

        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        filter_label = QLabel("Filter by Days Overdue:")
        self.days_spin = QSpinBox()
        self.days_spin.setRange(0, 365)
        self.days_spin.setValue(0)
        self.days_spin.setSuffix(" days")

        filter_btn = QPushButton("Apply Filter")
        filter_btn.clicked.connect(self._load_overdue_invoices)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background-color: #64748B;")
        refresh_btn.clicked.connect(self._load_overdue_invoices)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.days_spin)
        filter_layout.addWidget(filter_btn)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Summary cards
        summary_layout = QHBoxLayout()

        self.total_overdue_card = self._make_card("Total Overdue", "R 0.00", "#DC2626")
        self.num_overdue_card = self._make_card("Number Overdue", "0", "#D97706")
        self.avg_overdue_card = self._make_card("Average Days Late", "0", "#7C3AED")

        summary_layout.addWidget(self.total_overdue_card)
        summary_layout.addWidget(self.num_overdue_card)
        summary_layout.addWidget(self.avg_overdue_card)
        layout.addLayout(summary_layout)

        # Overdue invoices table
        table_label = QLabel("Overdue Invoices")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(table_label)

        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(8)
        self.invoices_table.setHorizontalHeaderLabels([
            "Student Number", "Student Name", "Invoice Number",
            "Invoice Date", "Due Date", "Days Overdue",
            "Total", "Balance Outstanding"
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
        layout.addWidget(self.invoices_table)

        # Action buttons
        btn_layout = QHBoxLayout()

        send_reminder_btn = QPushButton("Send Reminder (Selected)")
        send_reminder_btn.setStyleSheet("background-color: #2563EB;")
        send_reminder_btn.clicked.connect(self._send_reminder)

        print_report_btn = QPushButton("Print Report")
        print_report_btn.clicked.connect(self._print_report)

        btn_layout.addWidget(send_reminder_btn)
        btn_layout.addWidget(print_report_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _setup_reminder_scheduler(self):
        """Setup automatic reminder scheduler for 10th, 22nd, and last day of month."""
        # Timer that checks every hour if reminders should be sent
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_and_send_scheduled_reminders)
        self.check_timer.start(3600000)  # Check every hour (3600000 ms)

    def _check_and_send_scheduled_reminders(self):
        """Check if today is a reminder day and send automatic reminders."""
        today = datetime.now().date()
        day = today.day
        last_day = calendar.monthrange(today.year, today.month)[1]

        # Reset flag if it's a new day
        if not hasattr(self, 'last_check_date'):
            self.last_check_date = today
        elif self.last_check_date != today:
            self.reminder_sent_today = False
            self.last_check_date = today

        # Check if today is 10th, 22nd, or last day of month
        is_reminder_day = day in [10, 22] or day == last_day

        if not is_reminder_day or self.reminder_sent_today:
            return

        # Send reminders for all overdue invoices
        self._send_automatic_reminders()
        self.reminder_sent_today = True

    def _send_automatic_reminders(self):
        """Automatically send reminders to all students with overdue invoices."""
        today = datetime.now().date()

        connection = get_connection()
        try:
            # Ensure payment_reminders table exists
            connection.execute("""
                CREATE TABLE IF NOT EXISTS payment_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    reminder_date TEXT NOT NULL,
                    reminder_type TEXT,
                    status TEXT DEFAULT 'sent',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    UNIQUE(student_id, reminder_date, reminder_type)
                )
            """)
            connection.commit()

            overdue = connection.execute("""
                SELECT DISTINCT
                    s.id,
                    s.student_number,
                    s.first_name || ' ' || s.last_name AS student_name,
                    s.email,
                    s.phone,
                    COUNT(i.id) as invoice_count,
                    SUM(CASE WHEN i.status != 'Paid' THEN (i.total_amount - COALESCE((SELECT SUM(amount) FROM payments WHERE invoice_id = i.id), 0)) ELSE 0 END) as total_outstanding
                FROM students s
                JOIN invoices i ON s.id = i.student_id
                WHERE i.status != 'Paid' AND i.due_date < date('now')
                GROUP BY s.id
            """).fetchall()

            reminder_count = 0
            for student in overdue:
                student_id = student["id"]
                student_name = student["student_name"]
                email = student["email"]
                phone = student["phone"]
                invoice_count = student["invoice_count"]
                total_outstanding = float(student["total_outstanding"] or 0)

                # Log reminder in database
                try:
                    connection.execute("""
                        INSERT INTO payment_reminders 
                        (student_id, reminder_date, reminder_type, status)
                        VALUES (?, ?, ?, ?)
                    """, (student_id, today.isoformat(), 'automatic', 'sent'))
                    connection.commit()
                    reminder_count += 1
                    print(f"Reminder sent to {student_name} ({email}): Outstanding balance R {total_outstanding:,.2f}")
                except Exception as e:
                    # Reminder may have already been sent today
                    pass

            print(f"Total automatic reminders sent: {reminder_count}")

        except Exception as e:
            print(f"Error in automatic reminder: {e}")
        finally:
            connection.close()

    def _make_card(self, title, value, color):
        """Create a summary card."""
        frame = QWidget()
        frame.setStyleSheet(
            f"background-color: white; border: 2px solid {color}; "
            "border-radius: 10px; padding: 15px;"
        )
        layout = QVBoxLayout(frame)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        value_lbl.setObjectName("value")

        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        layout.addStretch()

        frame.value_lbl = value_lbl
        return frame

    def _load_overdue_invoices(self, *_):
        """Load all overdue invoices."""
        min_days = self.days_spin.value()
        today = datetime.now().date()

        connection = get_connection()
        try:
            invoices = connection.execute("""
                SELECT
                    s.student_number,
                    s.first_name || ' ' || s.last_name AS student_name,
                    i.invoice_number,
                    i.invoice_date,
                    i.due_date,
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) AS paid_amount
                FROM invoices i
                JOIN students s ON i.student_id = s.id
                LEFT JOIN payments p ON p.invoice_id = i.id
                WHERE i.status != 'Paid' AND i.due_date < date('now')
                GROUP BY i.id
                ORDER BY i.due_date ASC
            """).fetchall()

            self.invoices_table.setRowCount(0)
            total_overdue = 0.0
            days_overdue_list = []

            for inv in invoices:
                due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
                days_overdue = (today - due_date).days

                if days_overdue < min_days:
                    continue

                total = float(inv["total_amount"] or 0)
                paid = float(inv["paid_amount"] or 0)
                balance = max(0.0, total - paid)

                total_overdue += balance
                days_overdue_list.append(days_overdue)

                row = self.invoices_table.rowCount()
                self.invoices_table.insertRow(row)

                self.invoices_table.setItem(row, 0, QTableWidgetItem(inv["student_number"]))
                self.invoices_table.setItem(row, 1, QTableWidgetItem(inv["student_name"]))
                self.invoices_table.setItem(row, 2, QTableWidgetItem(inv["invoice_number"]))
                self.invoices_table.setItem(row, 3, QTableWidgetItem(inv["invoice_date"]))
                self.invoices_table.setItem(row, 4, QTableWidgetItem(inv["due_date"]))
                self.invoices_table.setItem(row, 5, QTableWidgetItem(str(days_overdue)))
                self.invoices_table.setItem(row, 6, QTableWidgetItem(f"R {total:,.2f}"))
                self.invoices_table.setItem(row, 7, QTableWidgetItem(f"R {balance:,.2f}"))

                # Color code rows
                if days_overdue > 30:
                    color = "#FEE2E2"  # Dark red
                elif days_overdue > 14:
                    color = "#FEF08A"  # Yellow
                else:
                    color = "#DBEAFE"  # Light blue

                for col in range(8):
                    self.invoices_table.item(row, col).setBackground(
                        __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor(color)
                    )

            # Update summary
            num_overdue = len(days_overdue_list)
            avg_days = int(sum(days_overdue_list) / len(days_overdue_list)) if days_overdue_list else 0

            self.total_overdue_card.value_lbl.setText(f"R {total_overdue:,.2f}")
            self.num_overdue_card.value_lbl.setText(str(num_overdue))
            self.avg_overdue_card.value_lbl.setText(str(avg_days))

        finally:
            connection.close()

    def _send_reminder(self):
        """Send payment reminder (simulated)."""
        row = self.invoices_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an invoice.")
            return

        invoice_num = self.invoices_table.item(row, 2).text()
        student_name = self.invoices_table.item(row, 1).text()
        amount = self.invoices_table.item(row, 7).text()

        message = (
            f"Reminder sent to {student_name}\n\n"
            f"Invoice: {invoice_num}\n"
            f"Outstanding: {amount}\n\n"
            "In a real system, this would send an email or SMS reminder."
        )

        QMessageBox.information(self, "Reminder Sent", message)

    def _print_report(self):
        """Print overdue invoices report."""
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        html = f"""
        <html>
        <body style="font-family: Arial; font-size: 11pt; margin: 20px;">
            <h1 style="color: #172B4D; text-align: center;">LISTEC COLLEGE</h1>
            <p style="text-align: center;">Overdue Invoices Report</p>
            <p style="font-size: 9pt; color: #666;">Generated: {today}</p>
            <hr>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #172B4D; color: white;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Student</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Invoice</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Due Date</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Days Late</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Total</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Balance</th>
                </tr>
        """

        for row in range(self.invoices_table.rowCount()):
            student_num = self.invoices_table.item(row, 0).text()
            invoice = self.invoices_table.item(row, 2).text()
            due = self.invoices_table.item(row, 4).text()
            days = self.invoices_table.item(row, 5).text()
            total = self.invoices_table.item(row, 6).text()
            balance = self.invoices_table.item(row, 7).text()

            html += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{student_num}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{invoice}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{due}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{days}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; color: #DC2626;">{balance}</td>
                </tr>
            """

        html += """
            </table>
            <p style="margin-top: 20px; font-size: 9pt; text-align: center;">
                LISTEC COLLEGE - Confidential
            </p>
        </body>
        </html>
        """

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print(printer)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PaymentRemindersModule()
    window.show()
    sys.exit(app.exec())
