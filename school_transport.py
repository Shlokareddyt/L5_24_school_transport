"""School transport roster management utilities.

Provides functions to enroll riders, build route rosters, export a
roster to a file, dispatch a route alert, and total fees collected
for a route.
"""

import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE riders (id INTEGER PRIMARY KEY, student TEXT, route TEXT, stop TEXT, fee INTEGER)")


def enroll_rider(student, route, stop, fee):
    """Insert a new rider into the riders table."""
    conn.execute(
        "INSERT INTO riders (student, route, stop, fee) VALUES (?, ?, ?, ?)",
        (student, route, stop, fee),
    )
    conn.commit()


def route_roster(route):
    """Return the list of student names enrolled on the given route."""
    return [r[0] for r in conn.execute("SELECT student FROM riders WHERE route = ?", (route,))]


def export_roster(path, route):
    """Write the roster for a route to a text file, one name per line."""
    with open(path, "w", encoding="utf-8") as out:
        for name in route_roster(route):
            out.write(name + "\n")

def dispatch_alert(route):
    """Print a dispatch alert for the given route."""
    print(f"dispatching bus {route}")


def fee_collected(route):
    """Return the total fee collected for a route, or 0 if none found."""
    try:
        return conn.execute("SELECT SUM(fee) FROM riders WHERE route = ?", (route,)).fetchone()[0]
    except sqlite3.Error:
        return 0


def main():
    """Run a small demo of the school transport roster functions."""
    enroll_rider("Tara", "R1", "Lake Road", 1800)
    enroll_rider("Kabir", "R1", "Mill Street", 1800)
    enroll_rider("Zoya", "R2", "Fort Gate", 2100)
    total = fee_collected("R1")
    if total != 3600:
        raise ValueError(f"Unexpected fee total for R1: {total}")
    export_roster("route_r1.txt", "R1")
    dispatch_alert("R1")
    print(route_roster("R2"))


if __name__ == "__main__":
    main()
