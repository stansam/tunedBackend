from sqlalchemy import text
from datetime import datetime, timezone

def generate_public_order_number(connection):
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month

    result = connection.execute(
        text("""
        INSERT INTO order_sequences (year, month, value)
        VALUES (:year, :month, 1)
        ON CONFLICT (year, month)
        DO UPDATE SET value = order_sequences.value + 1
        RETURNING value
        """),
        {"year": year, "month": month}
    )

    counter = result.scalar_one()
    return f"ORD-{year}{month:02d}-{counter:05d}"