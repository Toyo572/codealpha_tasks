from datetime import datetime, timedelta
from django.utils import timezone


def _get_conflicting_table_ids(date, time, duration_minutes, exclude_reservation_id=None):
    """
    Returns a set of table IDs that are blocked on a given date+time window.
    Checks both Reservation and TableOccupancy. Adds a 10-minute buffer after each slot.
    """
    from .models import Reservation, TableOccupancy

    BUFFER = timedelta(minutes=10)
    start_dt = timezone.make_aware(datetime.combine(date, time))
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    conflicting_ids = set()

    # --- Check Reservations ---
    reservations = Reservation.objects.filter(
        reserved_date=date,
        status__in=[
            Reservation.Status.PENDING,
            Reservation.Status.CONFIRMED,
            Reservation.Status.SEATED,
        ],
    ).exclude(pk=exclude_reservation_id)

    for r in reservations:
        r_start = timezone.make_aware(datetime.combine(r.reserved_date, r.reserved_time))
        r_end = r_start + timedelta(minutes=r.duration_minutes) + BUFFER
        if not (end_dt <= r_start or start_dt >= r_end):
            conflicting_ids.add(r.table_id)

    occupancies = TableOccupancy.objects.filter(occupied_date=date)
    for o in occupancies:
        o_start = timezone.make_aware(datetime.combine(o.occupied_date, o.occupied_time))
        o_end = o_start + timedelta(minutes=o.duration_minutes) + BUFFER
        if not (end_dt <= o_start or start_dt >= o_end):
            conflicting_ids.add(o.table_id)

    return conflicting_ids


def get_available_tables(date, time, party_size, duration_minutes=90, exclude_reservation_id=None):
    from .models import Table

    conflicting_ids = _get_conflicting_table_ids(
        date, time, duration_minutes, exclude_reservation_id
    )

    return Table.objects.filter(
        capacity__gte=party_size,
        status__in=[Table.Status.AVAILABLE, Table.Status.RESERVED],
    ).exclude(id__in=conflicting_ids)


def get_available_tables_by_date(date, party_size):
    """
    Customer-facing: returns all tables that have at least one free slot on a given date.
    A table is considered 'potentially available' if it's not fully blocked all day.
    Returns each table with its blocked windows so the customer knows what's taken.
    """
    from .models import Table, Reservation, TableOccupancy
    from datetime import timedelta

    BUFFER = timedelta(minutes=10)

    tables = Table.objects.filter(
        capacity__gte=party_size,
        status__in=[Table.Status.AVAILABLE, Table.Status.RESERVED],
    )

    result = []
    for table in tables:
        blocked_windows = []

        reservations = Reservation.objects.filter(
            table=table,
            reserved_date=date,
            status__in=[
                Reservation.Status.PENDING,
                Reservation.Status.CONFIRMED,
                Reservation.Status.SEATED,
            ],
        )
        for r in reservations:
            start = datetime.combine(date, r.reserved_time)
            end = start + timedelta(minutes=r.duration_minutes) + BUFFER
            blocked_windows.append({
                "from": r.reserved_time.strftime("%H:%M"),
                "until": end.strftime("%H:%M"),
                "reason": "reserved",
            })

        occupancies = TableOccupancy.objects.filter(table=table, occupied_date=date)
        for o in occupancies:
            start = datetime.combine(date, o.occupied_time)
            end = start + timedelta(minutes=o.duration_minutes) + BUFFER
            blocked_windows.append({
                "from": o.occupied_time.strftime("%H:%M"),
                "until": end.strftime("%H:%M"),
                "reason": "occupied",
            })

        result.append({
            "id": table.id,
            "number": table.number,
            "capacity": table.capacity,
            "location": table.location,
            "blocked_windows": sorted(blocked_windows, key=lambda x: x["from"]),
        })

    return result


def check_table_availability(table, date, time, duration_minutes=90, exclude_reservation_id=None):
    conflicting_ids = _get_conflicting_table_ids(
        date, time, duration_minutes, exclude_reservation_id
    )
    if table.pk in conflicting_ids:
        return False, f"Table {table.number} is not available at the requested time."
    return True, None