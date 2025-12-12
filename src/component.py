"""
Jira JQL queries for given component
"""

import argparse
import datetime
import getpass
import json
import logging
import sys

from jira import Jira

PROGNAME = "component"
EXAMPLES = ""

DEFAULT_URL = "https://your-jira-instance.atlassian.net"  # Replace with your Jira base URL
DEFAULT_PROJECT = "YOUR_PROJECT_KEY"  # Replace with your project key
DEFAULT_COMPONENT = "YOUR_PROJECT_COMPONENT"  # Replace with your project component
DEFAULT_PREFIX = "YOUR_LABEL_PREFIX"  # Replace with your label prefix
DEFAULT_TEAM = ["YOUR", "TEAM", "MEMBERS"]  # Replace with your team members
DEFAULT_YEARS = 5  # Replace with your number of maximum years


def section(title):
    """
    Print out section separator
    """
    logging.info("*" * 60)
    logging.info("*** %s", title)
    logging.info("*" * 60)


def echo(result=None, limit=2000):
    """
    Print out request result
    """
    if result:
        result = str(result)
        logging.info("Result:\n%s", result[:limit])
    else:
        logging.error("NO RESULT!!!")


def connect(options):
    """
    Connect to Jira
    """
    section("Connecting to " + options.url)
    jira = Jira(options.url, options.username, options.password)
    if not jira.open():
        section("Fail")
        return None
    return jira


def get_labels(jira, options):
    """
    Return list of labels for the project and the component
    """
    all_labels = jira.get_component_labels(options.project, options.component)
    if options.prefix:
        valid_labels = []
        for label in all_labels:
            if label.startswith(options.prefix):
                valid_labels.append(label)
        return valid_labels
    return all_labels


def assignee_statistics(jira, options, assignee):
    """
    Collect assignee statistics
    """
    project_key = options.project
    component = options.component
    max_years = options.years
    current_year = datetime.date.today().year
    year = current_year
    data = []
    while year > current_year - max_years:
        common = f"project = '{project_key}'"
        # common += f" AND component in ('{component}')"
        created = f" AND created >= '{year}/01/01'"
        created += f" AND created <= '{year + 1}/01/01'"
        resolved = f" AND resolved >= '{year}/01/01'"
        resolved += f" AND resolved <= '{year + 1}/01/01'"
        assign = f" AND assignee='{assignee}'"
        issues_created = jira.count(common + created + assign)
        issues_resolved = jira.count(common + resolved + assign)
        data.append({
            "year": year,
            "created": issues_created,
            "resolved": issues_resolved,
        })
        year -= 1
    return data


def team_statistics(jira, options):
    """
    Collect creared/resolved assignee statistics
    """
    section("Created/Resolved annual statistics for assignees")
    assignees = options.team
    statistics = {}
    for assignee in assignees:
        data = assignee_statistics(jira, options, assignee)
        statistics[assignee] = data
    years = ""
    for assignee in statistics:
        for data in statistics[assignee]:
            year = data["year"]
            years += "%10s" % year
        break
    logging.info("%20s %s", "Name", years)
    for assignee in statistics:
        line = "%20s " % assignee
        for data in statistics[assignee]:
            created = data["created"]
            resolved = data["resolved"]
            line += "%10s" % f"{created}/{resolved}"
        logging.info(line)
    section("Done")


def label_statistics(jira, options, label):
    """
    Collect label statistics
    """
    project_key = options.project
    component = options.component
    max_years = options.years
    current_year = datetime.date.today().year
    year = current_year
    data = []
    while year > current_year - max_years:
        common = f"project = '{project_key}'"
        common += f" AND component in ('{component}')"
        created = f" AND created >= '{year}/01/01'"
        created += f" AND created <= '{year + 1}/01/01'"
        resolved = f" AND resolved >= '{year}/01/01'"
        resolved += f" AND resolved <= '{year + 1}/01/01'"
        labels = f" AND labels in ('{label}')"
        issues_created = jira.count(common + created + labels)
        issues_resolved = jira.count(common + resolved + labels)
        data.append({
            "year": year,
            "created": issues_created,
            "resolved": issues_resolved,
        })
        year -= 1
    return data


def all_statistics(jira, options):
    """
    Collect creared/resolved label statistics
    """
    section("Created/Resolved annual statistics for labels")
    labels = get_labels(jira, options)
    statistics = {}
    for label in labels:
        data = label_statistics(jira, options, label)
        statistics[label] = data
    years = ""
    for label in statistics:
        for data in statistics[label]:
            year = data["year"]
            years += "%10s" % year
        break
    logging.info("%20s %s", "Label", years)
    for label in statistics:
        line = "%20s " % label
        for data in statistics[label]:
            created = data["created"]
            resolved = data["resolved"]
            line += "%10s" % f"{created}/{resolved}"
        logging.info(line)
    section("Done")


def label_estimates(jira, options, label):
    """
    Effort estimates for given label
    """
    project_key = options.project
    component = options.component
    current_year = datetime.date.today().year
    year = current_year
    logging.debug("Estimates for %s in %d", label, year)
    query = f"project = '{project_key}'"
    query += f" AND component in ('{component}')"
    # query += f" AND created >= '{year}/01/01'"
    # query += f" AND created <= '{year + 1}/01/01'"
    query += f" AND labels in ('{label}')"
    data = jira.jql(query, max_results=500, fields="timetracking")
    data = json.loads(data)
    # logging.debug("Data: %s", str(data))
    total = 0
    count = 0
    if data and "issues" in data:
        for issue in data["issues"]:
            # logging.debug(str(issue))
            if "fields" in issue and "timetracking" in issue["fields"]:
                # logging.debug(str(issue["fields"]["timetracking"]))
                timetracking = issue["fields"]["timetracking"]
                if "originalEstimateSeconds" in timetracking:
                    seconds = int(timetracking["originalEstimateSeconds"])
                    hours = seconds / 60 / 60
                    total += hours
                    count += 1
    if total and count:
        logging.debug("Total: %d hours (%d days) in %d issues", total, total/8, count)
        logging.debug("Average: %.2f hours (%.3f days)", total/count, total/count/8)
    return {
        "hours": total,
        "issues": count,
    }


def all_estimates(jira, options):
    """
    Effort estimates for all labels
    """
    section("Effort estimates for labels")
    labels = get_labels(jira, options)
    estimates = {}
    for label in labels:
        estimate = label_estimates(jira, options, label)
        if estimate["hours"] and estimate["issues"]:
            estimates[label] = estimate
    logging.info("%20s %10s %21s %21s",
                 "Label", "Issues", "Total(hours, days)", "Average(hours, days)")
    for label in estimates:
        total = estimates[label]["hours"]
        count = estimates[label]["issues"]
        logging.info("%20s %10d %10d %10d %10.1f %10.1f",
                     label, count, total, total/8, total/count, total/count/8)


def test(jira, options):
    """
    Run basic test
    """
    section("Check session")
    echo(jira.request("rest/api/2/myself"))
    jql = f"project = '{options.project}' AND component = '{options.component}'"
    jql += " AND status != 'Closed'"
    section("Test JQL request")
    echo(jira.jql(jql, max_results=0))
    section("Test count function")
    echo(jira.count(jql))
    section("Return all project labels")
    project_id = jira.get_project_id(options.project)
    all_labels = jira.get_labels(project_id)
    echo(str(all_labels))
    section("Return oldest issue")
    query = f"project = '{options.project}'"
    query += f" AND component in ('{options.component}')"
    query += f" ORDER BY created ASC"
    data = jira.jql(query, start_at=0, max_results=1, fields="created")
    echo(str(data))
    section("Done")


def add_arguments(parser):
    """ Parse command line arguments or show help """
    parser.add_argument("--url",
                        default=DEFAULT_URL,
                        help=f"Jira base URL (default: {DEFAULT_URL})")
    parser.add_argument("--project",
                        default=DEFAULT_PROJECT,
                        help=f"Jira Project name (default: {DEFAULT_PROJECT})")
    parser.add_argument("--component",
                        default=DEFAULT_COMPONENT,
                        help=f"Project component (default: {DEFAULT_COMPONENT})")
    parser.add_argument("--prefix",
                        default=DEFAULT_PREFIX,
                        help=f"Label prefix (default: {DEFAULT_PREFIX})")
    parser.add_argument("--team",
                        nargs="*",
                        type=str,
                        default=DEFAULT_TEAM,
                        help=f"Team members (default: {DEFAULT_TEAM})")
    parser.add_argument("--years",
                        default=DEFAULT_YEARS,
                        help=f"Max years (default: {DEFAULT_YEARS})")
    parser.add_argument("-u", "--username",
                        help="username")
    parser.add_argument("-p", "--password",
                        help="password")
    parser.add_argument("--jql",
                        help="JQL to run")
    parser.add_argument("-t", "--test",
                        default=False,
                        action="store_true",
                        help="run basic test")
    return parser


def run(options):
    """
    Run function
    """
    if not options.username:
        options.username = getpass.getuser()
    if not options.password:
        print("Using Jira username:", options.username)
        options.password = getpass.getpass("Enter your Jira password: ")
    jira = connect(options)
    if not jira:
        return False
    if options.test:
        test(jira, options)
    else:
        team_statistics(jira, options)
        all_estimates(jira, options)
        all_statistics(jira, options)
    return True


def parse_args():
    """ Parse command line arguments or show help """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog=PROGNAME,
        description=__doc__,
        epilog=EXAMPLES)
    parser = add_arguments(parser)
    parser.add_argument("-v", "--verbosity",
                        default=0,
                        action="count",
                        help="increase verbosity (-v or -vv)")
    parser.add_argument("--log-format", default="%(message)s", help=argparse.SUPPRESS)
    options = parser.parse_args()

    if options.verbosity > 1:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format=options.log_format)

    return options


def main():
    """
    Main function
    """
    options = parse_args()
    return run(options)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
