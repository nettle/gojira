"""
Gerrit REST API
"""

import argparse
import datetime
import json
import logging
import netrc
import urllib.parse
import urllib.request


DEFAULT_SERVERS = ["https://gerrit.company.com"]  # Replace with your server list
DEFAULT_TEAM = ["YOUR", "TEAM", "MEMBERS"]  # Replace with your team members


def request(url):
    """Fetches a URL using credentials found in ~/.netrc using standard libraries."""

    # 1. Extract the hostname from the URL
    parsed_url = urllib.parse.urlparse(url)
    host = parsed_url.hostname

    if not host:
        print(f"Error: Could not determine host from URL: {url}")
        return ""

    # 2. Set up an HTTP password manager that reads from .netrc
    # The HTTPPasswordMgrWithPriorAuth will read the credentials but urllib's
    # handlers are slightly complex to configure to use the .netrc automatically like 'curl --netrc'
    # The most robust way is often to let urllib handlers manage the auth *dialogue*

    # Alternatively, we can let the system's .netrc configuration handle it automatically
    # if we configure the opener correctly.

    # We can create a simple password manager for this specific host
    try:
        info = netrc.netrc()
        auth_info = info.hosts.get(host)
        if auth_info:
            login, account, password = auth_info

            # Create a password manager and add the credentials
            pass_manager = urllib.request.HTTPPasswordMgrWithPriorAuth()
            pass_manager.add_password(None, host, login, password, is_authenticated=True)

            # Create an authentication handler
            auth_handler = urllib.request.HTTPBasicAuthHandler(pass_manager)

            # Build the opener with the auth handler
            opener = urllib.request.build_opener(auth_handler)
            # Install it globally for subsequent calls (simpler)
            urllib.request.install_opener(opener)

            # print(f"Using .netrc credentials for host: {host}")

        else:
            print(f"Warning: No .netrc entry found for {host}. Attempting request without auth.")
            # If no .netrc entry exists, just use the default opener
            urllib.request.install_opener(urllib.request.build_opener())

    except FileNotFoundError:
        print(f"Warning: ~/.netrc file not found. Attempting request without auth.")
        urllib.request.install_opener(urllib.request.build_opener())
    except Exception as e:
        print(f"Warning: Error reading .netrc file: {e}. Proceeding without explicit auth handler.")
        urllib.request.install_opener(urllib.request.build_opener())


    # 3. Make the request using the configured opener
    try:
        with urllib.request.urlopen(url) as response:
            # print(f"\nRequest successful! Status Code: {response.status}")

            # Read and decode the response
            content = response.read().decode("utf-8")
            # print("Response Snippet:")
            # print(content[:500] + ("..." if len(content) > 500 else ""))
            return content

    except urllib.error.HTTPError as e:
        print(f"\nRequest failed: HTTP Error {e.code} - {e.reason}")
        print(e.read().decode("utf-8")[:200] + "...")
        return ""
    except urllib.error.URLError as e:
        print(f"\nRequest failed: URL Error {e.reason}")
        return ""


def get_data(url, name, year):
    """ """
    # --- Example Usage ---
    # Replace with the URL you want to fetch that requires authentication via .netrc
    gerrit_name = name.replace(" ", "+")
    target_url = f"{url}/a/changes/?q=after:{year}-01-01+before:{year+1}-01-01+owner:\"{gerrit_name}\""
    response = request(target_url)
    commits = {}
    if response:
        if response.startswith(")]}'"):
            data = json.loads(response[4:])
            # print(json.dumps(data, indent=4))
            for commit in data:
                # print(commit["status"])
                if commit["status"] in commits:
                    commits[commit["status"]] += 1
                else:
                    commits[commit["status"]] = 1
            # print(name, year, str(commits))
    return commits


def collect(url, names, year, none="."):
    """ """
    print("Gerrit commit statistics")
    print("Server:", url)
    print("%20s   %5s %5s %5s" % ("Name", "Merged", "New", "Abandoned"))
    for name in names:
        commits = get_data(url, name, year)
        merged = commits["MERGED"] if "MERGED" in commits else none
        new = commits["NEW"] if "NEW" in commits else none
        abandoned = commits["ABANDONED"] if "ABANDONED" in commits else none
        print("%20s   %5s %5s %5s" % (name, merged, new, abandoned))


def add_arguments(parser):
    """ Parse command line arguments or show help """
    parser.add_argument("--url",
                        nargs="*",
                        type=str,
                        default=DEFAULT_SERVERS,
                        help=f"Server URLs (default: {DEFAULT_SERVERS})")
    parser.add_argument("--team",
                        nargs="*",
                        type=str,
                        default=DEFAULT_TEAM,
                        help=f"Team members (default: {DEFAULT_TEAM})")
    return parser


def run(options):
    """
    Run function
    """
    year = datetime.date.today().year
    for url in options.url:
        collect(url, options.team, year)


def parse_args():
    """ Parse command line arguments or show help """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__)
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
    main()
