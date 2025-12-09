"""
Jira REST API
"""

import json
import http.cookiejar
import logging
import urllib


def get_list(data, name):
    """
    Helper: return list by name
    """
    if data and name in data and isinstance(data[name], list):
        return data[name]
    return []


def get_dict(data, name):
    """
    Helper: return dict by name
    """
    if data and name in data and isinstance(data[name], dict):
        return data[name]
    return {}


class Jira:
    """
    Class for Jira REST API
    """
    def __init__(self, base_url, username, password):
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies))
        self.base_url = base_url
        self.login_data = json.dumps(
            {"username": username, "password": password}).encode("utf-8")

    def open(self):
        """
        Connect to Jira instance and create session
        """
        session_url = f"{self.base_url}/rest/auth/1/session"
        logging.debug("Session URL:   %s", session_url)
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(
            session_url, data=self.login_data, headers=headers)
        try:
            with self.opener.open(req) as response:
                response_data = response.read().decode("utf-8")
                logging.debug("Response:      %s", str(response_data))
                session_info = json.loads(response_data)
                if "session" in session_info:
                    logging.info("Jira session created successfully!")
                    logging.debug("Session Name:  %s", session_info["session"]["name"])
                    logging.debug("Session Value: %s", session_info["session"]["value"])
                    return True
                logging.error("Failed to create Jira session.")
                logging.error("Response: %s", response_data)
        except urllib.error.HTTPError as error:
            logging.error("HTTP Error: %s - %s", error.code, error)
            error_response = error.read().decode("utf-8")
            logging.error("Error details: %s", error_response)
        except urllib.error.URLError as error:
            logging.error("URL Error: %s", error.reason)
        except Exception as error:  # pylint: disable=broad-except
            logging.error("An unexpected error occurred: %s", error)
        logging.error("Failed to create Jira session")
        return False

    def request(self, rest):
        """
        Run Jira REST API request
        """
        url = f"{self.base_url}/{rest}"
        logging.debug("Request  URL: %s", url)
        req = urllib.request.Request(url)
        logging.debug("Request data: %s", str(req))
        try:
            with self.opener.open(req) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            logging.error("HTTP Error during subsequent request: %s - %s",
                          error.code, error.reason)
            error_response = error.read().decode("utf-8")
            logging.error("Error details: %s", error_response)
        except urllib.error.URLError as error:
            logging.error("URL Error during subsequent request: %s", error.reason)
        except Exception as error:  # pylint: disable=broad-except
            logging.error("An unexpected error occurred during subsequent request: %s", error)
        return None

    def jql(self, query, start_at=0, max_results=50,
            fields="summary,status,issuetype,assignee,created"):
        """
        Run Jira JQL request
        """
        logging.debug("JQL: %s", query)
        params = {
            "jql": query,
            "startAt": start_at,        # Starting index of the results
            "maxResults": max_results,  # Maximum number of issues to return
            "fields": fields,           # Comma-separated list of fields to retrieve
        }
        rest = f"rest/api/2/search?{urllib.parse.urlencode(params)}"
        return self.request(rest)

    def count(self, query):
        """
        Return total from Jira JQL request
        """
        data = self.jql(query, start_at=0, max_results=0, fields="")
        data = json.loads(data)
        logging.debug("Data: %s", str(data))
        if data and "total" in data:
            return data["total"]
        logging.error("Invalid result: %s", str(data))
        return 0

    def get_project_id(self, project_key):
        """
        Return Jira Project ID by Project key
        """
        data = self.request("rest/api/2/project")
        data = json.loads(data)
        if data and isinstance(data, list):
            for project in data:
                if "key" in project and "id" in project:
                    if project["key"] == project_key:
                        return project["id"]
            logging.error("Project '%s' not found", project_key)
        else:
            logging.error("Invalid result: %s...", str(data)[:2000])
        return ""

    def get_labels(self, project_id):
        """
        Return list of Labels by Project ID
        """
        data = self.request(f"rest/gadget/1.0/labels/gadget/project-{project_id}/labels")
        if not data:
            logging.error("Invalid response: %s", str(data))
            return []
        data = json.loads(data)
        labels = []
        for group in get_list(data, "groups"):
            for label in get_list(group, "labels"):
                labels.append(label["label"])
        return labels

    def get_component_labels(self, project_key, component):
        """
        Return list of Labels by Project and Component
        """
        query = f"project = '{project_key}'"
        query += f" AND component in ('{component}')"
        query += f" AND labels is not empty"
        data = self.jql(query, start_at=0, max_results=9999, fields="labels")
        if not data:
            logging.error("Invalid response to %s", query)
            return []
        data = json.loads(data)
        labels = set()
        for issue in get_list(data, "issues"):
            fields = get_dict(issue, "fields")
            issue_labels = get_list(fields, "labels")
            labels.update(issue_labels)
        return list(labels)
