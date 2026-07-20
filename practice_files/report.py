import json


def generate_report(data):
    filename = "report.json"
    with open(filename, "w") as f:
        json.dump(data, f)
