import pytest
import json
import report


@pytest.fixture(scope="session")
def report_json():
    # run the geneate report function
    data = {
        "name": "John Doe",
        "age": 30,
        "city": "New York"
    }
    report.generate_report(data)
    # now open the report make it a dictionary
    with open("report.json", "r") as f:
        report_data = json.load(f)
    return report_data


def test_report_type(report_json):
    assert type(report_json) == dict


def test_fields(report_json):
    assert "name" in report_json
    assert "age" in report_json
