from database import report_summary


def print_section(title, rows, key_name):
    print(f"\n--- {title} ---")
    if not rows:
        print("No data available.")
        return
    for row in rows:
        print(f'{row[key_name]}: {row["total"]}')


def show_reports():
    data = report_summary()
    print("\n================================")
    print("       HELP DESK REPORTS")
    print("================================")
    print(f'Total tickets: {data["total"]}')
    print(f'Resolved/closed tickets with resolution time: {data["resolved_count"]}')
    print(f'Unresolved tickets: {data["unresolved_count"]}')

    if data["average_resolution_hours"] is None:
        print("Average resolution time: Not available yet")
    else:
        print(f'Average resolution time: {data["average_resolution_hours"]:.2f} hours')

    print_section("TICKETS BY STATUS", data["by_status"], "status")
    print_section("TICKETS BY CATEGORY", data["by_category"], "category")
    print_section("TICKETS BY PRIORITY", data["by_priority"], "priority")
    print_section("TECHNICIAN WORKLOAD", data["workload"], "technician")
    print("================================")
