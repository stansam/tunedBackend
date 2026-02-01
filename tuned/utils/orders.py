"""
Order utility functions.

Provides helper functions for order-related operations.
"""
from datetime import datetime, timezone
from tuned.extensions import db


def generate_public_order_number(connection):
    """
    Generate a unique public order number in format: ORD-YYYYMM-XXXXX
    
    Uses SQLAlchemy ORM for database-agnostic implementation.
    Compatible with both SQLite (development) and PostgreSQL (production).
    
    Args:
        connection: SQLAlchemy connection from event listener
        
    Returns:
        str: Formatted order number (e.g., 'ORD-202602-00001')
    """
    from tuned.models.order import OrderSequence
    
    now = datetime.now(timezone.utc)
    year = now.year
    month = now.month
    
    # Use a manual transaction since we're in an event listener
    # Query for existing sequence for this month
    from sqlalchemy import select, update
    
    # Try to get existing sequence
    stmt = select(OrderSequence).where(
        OrderSequence.year == year,
        OrderSequence.month == month
    ).with_for_update()
    
    result = connection.execute(stmt)
    sequence = result.fetchone()
    
    if sequence:
        # Increment existing sequence
        new_value = sequence.value + 1
        update_stmt = update(OrderSequence).where(
            OrderSequence.year == year,
            OrderSequence.month == month
        ).values(value=new_value)
        connection.execute(update_stmt)
        counter = new_value
    else:
        # Create new sequence for this month
        from sqlalchemy import insert
        insert_stmt = insert(OrderSequence).values(
            year=year,
            month=month,
            value=1
        )
        connection.execute(insert_stmt)
        counter = 1
    
    # Format: ORD-YYYYMM-XXXXX (5 digits with leading zeros)
    return f"ORD-{year}{month:02d}-{counter:05d}"