import requests
import json
from geopy import distance
from flask import Flask, render_template, flash, request

app = Flask(__name__)
app.secret_key = "ice, ice, maybe"


def parse_to_float(text: str) -> float:
    """Try to parse text to a float and raise an error if not possible."""
    try:
        return float(text)
    except:
        raise Exception(f'Unable to parse "{text}" into a numerical value.')


def parse_coordinates_text(text: str) -> tuple[float, float]:
    """Returns a tuple of (a, b) from a provided text of 'a, b' or '"a, b"'."""
    text = text.strip('\"').strip(' ')
    text_parts = text.split(',')
    if len(text_parts) > 2:
        raise Exception('Invalid input: more than one comma')
    elif len(text_parts) < 2:
        raise Exception('Invalid input: no comma')
    return parse_to_float(text_parts[0]), parse_to_float(text_parts[1])


def get_outdoor_rinks() -> list[dict]:
    """Returns the latest list of outdoor ice rinks in Toronto from the PFR Opn Data API."""
    # Toronto Open Data is stored in a CKAN instance. It's APIs are documented here:
    # https://docs.ckan.org/en/latest/api/

    # To hit our API, you'll be making requests to:
    base_url = 'https://ckan0.cf.opendata.inter.prod-toronto.ca'

    # Datasets are called 'packages'. Each package can contain many 'resources'
    # To retrieve the metadata for this package and its resources, use the package name in this page's URL:
    url = base_url + '/api/3/action/package_show'
    params = {'id': 'outdoor-artificial-ice-rinks'}
    package = requests.get(url, params=params).json()

    # To get resource data:
    for idx, resource in enumerate(package['result']['resources']):

        # for datastore_active resources:
        if resource['datastore_active']:
            # To selectively pull records and attribute-level metadata:
            url = base_url + '/api/3/action/datastore_search'
            p = {'id': resource['id']}
            return requests.get(url, params=p).json()['result']['records']
            # This API call has many parameters. They're documented here:
            # https://docs.ckan.org/en/latest/maintaining/datastore.html


def get_rink_values(coordinates: tuple[float, float], rink: dict) -> tuple[dict, float]:
    """Returns a rink object modified to have its geomtery set as object values, and the distance from the input
    coordinates to the rink."""
    rink["geometry"] = json.loads(rink["geometry"])
    return rink, distance.distance(coordinates,
                                   (rink["geometry"]["coordinates"][1], rink["geometry"]["coordinates"][0])).km


def get_rink_closest_to_coordinates(coordinates: tuple[float, float]) -> str:
    """Returns the closest rink to a set of coordinates."""
    rinks: list[dict] = get_outdoor_rinks()  # get the latest data, even if locations are not likely to change often
    (closest_rink, closest_distance) = get_rink_values(coordinates, rinks[0])
    for i in range(1, len(rinks)):
        rink = rinks[i]
        (rink, rink_distance) = get_rink_values(coordinates, rink)
        if rink_distance < closest_distance:
            closest_rink = rink
            closest_distance = rink_distance
    return (
        f'The closest rink to the input coordinates is {closest_rink["Public Name"]}.\nIt is {closest_distance} km '
        f'away at {closest_rink['geometry']['coordinates']}.'
    )


@app.route("/")
def index():
    flash('Enter your coordinates as "latitude, longitude".')
    return render_template("index.html")


@app.route("/closest_rink", methods=["POST", "GET"])
def closest_rink():
    coordinates = parse_coordinates_text(request.form['coordinates_input'])
    flash(get_rink_closest_to_coordinates(coordinates))
    return render_template("index.html")


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)
