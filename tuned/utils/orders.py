from datetime import datetime, timezone
from sqlalchemy import select, update, insert
from sqlalchemy.orm import Session

def generate_public_order_number(connection: Session) -> str:
    from tuned.models.order import OrderSequence
    
    now = datetime.now(timezone.utc)
    year = now.year
    month = now.month
    
    stmt = select(OrderSequence).where(
        OrderSequence.year == year,
        OrderSequence.month == month
    ).with_for_update()
    
    result = connection.execute(stmt)
    sequence = result.fetchone()
    
    if sequence:
        new_value = sequence.value + 1
        update_stmt = update(OrderSequence).where(
            OrderSequence.year == year,
            OrderSequence.month == month
        ).values(value=new_value)
        connection.execute(update_stmt)
        counter = new_value
    else:
        insert_stmt = insert(OrderSequence).values(
            year=year,
            month=month,
            value=1
        )
        connection.execute(insert_stmt)
        counter = 1

    return f"ORD-{year}{month:02d}-{counter:05d}"