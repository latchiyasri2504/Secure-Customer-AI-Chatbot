
from app.db.database import SessionLocal
from app.db.models import Customer, Invoice
from datetime import datetime
from decimal import Decimal


db = SessionLocal()

try:
    customers_data = [
        ("Arun", "9876543210"),
        ("Deepa", "9123456780"),
    ]

    customers = {}

    for name, phone in customers_data:
        customer = db.query(Customer).filter_by(phone=phone).first()

        if not customer:
            customer = Customer(name=name, phone=phone)
            db.add(customer)
            db.flush()

        customers[name] = customer

    invoices_data = [
        ("Arun", "INV-100", "2026-10-01", "1500.00", "INR", "unpaid"),
        ("Arun", "INV-101", "2026-10-03", "2500.00", "INR", "paid"),
        ("Arun", "INV-102", "2026-10-05", "900.00", "INR", "unpaid"),
        ("Arun", "INV-103", "2026-10-08", "1200.00", "INR", "paid"),
        ("Arun", "INV-104", "2026-10-10", "750.00", "INR", "unpaid"),
        ("Deepa", "INV-200", "2026-10-02", "1800.00", "INR", "unpaid"),
        ("Deepa", "INV-201", "2026-10-04", "2200.00", "INR", "paid"),
        ("Deepa", "INV-202", "2026-10-06", "650.00", "INR", "unpaid"),
        ("Deepa", "INV-203", "2026-10-09", "1400.00", "INR", "paid"),
        ("Deepa", "INV-204", "2026-10-11", "950.00", "INR", "unpaid"),
    ]

    for name, number, date, amount, currency, status in invoices_data:
        customer = customers[name]
        existing = db.query(Invoice).filter_by(
            customer_id=customer.id,
            invoice_number=number,
        ).first()

        if not existing:
            invoice = Invoice(
                customer_id=customer.id,
                invoice_number=number,
                invoice_date=datetime.strptime(date, "%Y-%m-%d"),
                amount=Decimal(amount),
                currency=currency,
                payment_status=status,
            )
            db.add(invoice)

    db.commit()
    print("Sample customers and invoices added successfully!")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
