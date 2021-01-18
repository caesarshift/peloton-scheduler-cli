"""
Peloton Schedule: a CLI that allows a user to create stacks by date that can
                  be used to load into the Peloton's stack via a scheduled task.

Available commands:

    listclasses: shows available classes (filtered by bookmarked classes only)
    listschedule: shows created schedules
    showstack: shows current peloton stack
    loadschedule: loads stack from local file into peloton stack
    addschedule: adds a scheduled stack to the given date
"""
import argparse
from datetime import date, datetime, timedelta
import json
import os
import sys

from tabulate import tabulate

from peloton import PelotonSession
from peloton import PelotonStack

# Location of the schedule file
SCHEDULE_FILE = "schedule.json"

# Max number of days to print when calling listschedule and no value is entered
MAX_NUM_DAYS = 1000


################################################################################
# Argparse setup
################################################################################
parser = argparse.ArgumentParser(
    prog="peloton-scheduler-cli", description="Peloton Scheduler CLI"
)

parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.2")

subparsers = parser.add_subparsers(
    dest="command",
    title="subcommands",
    description="valid subcommands",
)

# listclasses subcommand
# TODO: max returned by class in PelotonStack is currently 18
subparsers.add_parser("listclasses", help="List bookmarked classes")

# addschedule subcommand
sp_addschedule = subparsers.add_parser(
    "addschedule", help="Add a new list of classes to the schedule"
)
sp_addschedule.add_argument(
    "--date",
    help="The scheduled stack date. Should be a date in the future",
    required=True,
)
sp_addschedule.add_argument(
    "--force",
    action="store_true",
    default=False,
    help="Overwrite an existing class schedule",
)
sp_addschedule.add_argument(
    "classes",
    nargs="+",
    help="A list of bookmarked class index. Run 'listclasses' first.",
)

# listschedule subcommand
sp_listschedule = subparsers.add_parser("listschedule")
sp_listschedule.add_argument(
    "--next", help="Show schedule for next N number of days", default=MAX_NUM_DAYS
)

# loadschedule subcommand
sp_loadschedule = subparsers.add_parser(
    "loadschedule", help="Loads the stack for the given date"
)
sp_loadschedule.add_argument("--date", help="Date to load (optional). Default is today")

# showstack subcommand
sp_showstack = subparsers.add_parser("showstack", help="Show the Peloton stack")


################################################################################
#
# Subcommand functions
#
################################################################################
def addschedule(schedule, schedule_date, classes, force=False):
    """
    Add a new scheduled stack to local schedule file.

    :param schedule: A dictionary of scheduled classes (each date is a key)
    :param schedule_date: A date string for the scheduled stack. Use YYYY-MM-DD format.
    :param force: If a schedule already exists for the schedule_date, overwrite it.
    :return: returns nothing
    """
    try:
        datetime.strptime(schedule_date, "%Y-%m-%d")
    except Exception:
        print(f"Unable to parse date (Expected YYYY-MM-DD): {schedule_date}")
        sys.exit(1)

    ps = PelotonSession(os.environ["PELOTON_USERNAME"], os.environ["PELOTON_PASSWORD"])
    bc = ps.get_bookmarked_classes()

    day_stack = [c for i, c in enumerate(bc) if str(i) in classes]

    if schedule_date in schedule and not force:
        print(
            "A schedule already exists for this date. Rerun with the --force flag to overwrite"
        )
        sys.exit(1)

    schedule[schedule_date] = day_stack
    with open(SCHEDULE_FILE, "w") as f:
        f.write(json.dumps(schedule, indent=4, sort_keys=True))
    print(f"Successfully saved {len(day_stack)} classes for {schedule_date}")


def listclasses():
    """
    Print bookmarked classes.

    :return: returns nothing
    """
    ps = PelotonSession(os.environ["PELOTON_USERNAME"], os.environ["PELOTON_PASSWORD"])
    columns = ["Title", "Class Type", "Difficulty", "Instructor"]
    to_tabulate(ps.get_bookmarked_classes(), columns)


def listschedule(schedule, next_num_days):
    """
    Print upcoming stack schedule.

    :param schedule: A dictionary of scheduled classes (each date is a key)
    :param next_num_days: An integer that limits how many days will be printed.
                          Use 0 if only wanting today's schedule.
                          Use 6 if wanting today + next 6 days.
    :return: returns nothing
    """
    start = date.today()
    end = start + timedelta(days=int(next_num_days))

    columns = ["Title", "Class Type", "Difficulty", "Instructor"]
    for d, s in schedule.items():
        dd = datetime.strptime(d, "%Y-%m-%d").date()
        if dd >= start and dd <= end:
            print(f"Date: {dd}")
            to_tabulate(s, columns)
            print("\n")


def loadschedule(schedule, load_date=None):
    """
    Load a list of classes into the Peloton stack.

    :param schedule: A dictionary of scheduled classes (each date is a key; each value is an array
                     of classes)
    :param load_date: A date string in format YYYY-MM-DD
    :return: returns nothing
    """
    if load_date:
        start = datetime.strptime(load_date, "%Y-%m-%d").date()
    else:
        start = date.today()

    load_date_str = str(start)

    if load_date_str not in schedule:
        print(f"Unable to find a scheduled stack for date: {start}")
        sys.exit(1)

    ps = PelotonSession(os.environ["PELOTON_USERNAME"], os.environ["PELOTON_PASSWORD"])
    stack = PelotonStack(ps.peloton_session)

    # Clear existing stack
    stack.clear_stack()

    # Add stacked classes in order
    for c in schedule[load_date_str]:
        stack.add_class_to_stack(c["Token"])
        # resp = stack.add_class_to_stack(c["Token"])
        # print(resp.json())

    print("The new stack:")
    columns = ["Title", "Class Type", "Difficulty", "Instructor"]
    to_tabulate(stack.get_stack(), columns)


def showstack():
    """
    List the current classes in the Peloton stack.

    :return: returns nothing
    """
    ps = PelotonSession(os.environ["PELOTON_USERNAME"], os.environ["PELOTON_PASSWORD"])
    stack = PelotonStack(ps.peloton_session)

    columns = ["Title", "Class Type", "Difficulty", "Instructor"]
    to_tabulate(stack.get_stack(), columns)


################################################################################
#
# Helper functions
#
################################################################################
def load_schedule_from_file():
    """
    Load the stack schedule from a local 'schedule.json' file.

    :return: a schedule dictionary
    """
    current_schedule = {}
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE) as f:
            current_schedule = json.load(f)
    return current_schedule


def to_tabulate(object_array, include_columns=None):
    """
    Print an object array as a nicely formatted table.

    :return: Nothing
    """
    table = []
    columns = []
    for o in object_array:
        if not include_columns:
            include_columns = o.keys()
        if not columns:
            columns = [oc for oc in o.keys() if oc in include_columns]
        val = []
        for k, v in o.items():
            if k in include_columns:
                val.append(v)
        table.append(val)
    print(tabulate(table, headers=columns, showindex="always", tablefmt="github"))


################################################################################
#
# MAIN
#
################################################################################
def main():
    if "PELOTON_USERNAME" not in os.environ:
        print("Unable to find environment variable PELOTON_USERNAME. Aborting...")
        sys.exit(1)
    if "PELOTON_PASSWORD" not in os.environ:
        print("Unable to find environment variable PELOTON_PASSWORD. Aborting...")
        sys.exit(1)

    args = parser.parse_args()
    if args.command == "listclasses":
        listclasses()
    elif args.command == "addschedule":
        schedule = load_schedule_from_file()
        addschedule(schedule, args.date, args.classes, args.force)
    elif args.command == "listschedule":
        schedule = load_schedule_from_file()
        listschedule(schedule, args.next)
    elif args.command == "showstack":
        showstack()
    elif args.command == "loadschedule":
        schedule = load_schedule_from_file()
        load_date = args.date
        loadschedule(schedule, load_date)


if __name__ == "__main__":
    main()
