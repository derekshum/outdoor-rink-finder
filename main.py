import requests
import json


def parse_coordinates_text(text: str) -> list:
    """Returns a tuple of (a, b) from a provided text of 'a, b' or '"a, b"'."""
    text = text.strip('\"').strip(' ')
    text_parts = text.split(',')
    if len(text_parts) > 2:
        raise Exception('Invalid input: more than one comma')
    elif len(text_parts) < 2:
        raise Exception('Invalid input: no comma')
    values: list[float] = []
    for text_part in text_parts:
        try:
            values.append(float(text_part))
        except:
            raise Exception(f'Unable to parse "{text_part}" into a numerical value')
    return values


def get_outdoor_rinks() -> list[dict]:
    """Returns the latest list of outdoor ice rinks in Toronto from the PFR Opn Data API."""
    # Toronto Open Data is stored in a CKAN instance. It's APIs are documented here:
    # https://docs.ckan.org/en/latest/api/

    # To hit our API, you'll be making requests to:
    base_url = 'https://ckan0.cf.opendata.inter.prod-toronto.ca'

    # Datasets are called 'packages'. Each package can contain many 'resources'
    # To retrieve the metadata for this package and its resources, use the package name in this page's URL:
    url = base_url + '/api/3/action/package_show'
    params = { 'id': 'outdoor-artificial-ice-rinks'}
    package = requests.get(url, params = params).json()

    # To get resource data:
    for idx, resource in enumerate(package['result']['resources']):

           # for datastore_active resources:
           if resource['datastore_active']:

               # To selectively pull records and attribute-level metadata:
               url = base_url + '/api/3/action/datastore_search'
               p = { 'id': resource['id'] }
               return requests.get(url, params = p).json()['result']['records']
               # This API call has many parameters. They're documented here:
               # https://docs.ckan.org/en/latest/maintaining/datastore.html


def get_distance(coordinates_1: list[float], coordinates_2: list[float]):
    """Returns the distance between two sets of coordinates using pythag."""
    return ((coordinates_1[0] - coordinates_2[0])**2 + (coordinates_1[1] - coordinates_2[1])**2)**0.5


def get_rink_values(coordinates: list[float], rink: dict) -> tuple[dict, float]:
    """Returns a rink object modified to have its geomtery set as object values, and the distance from the input
    coordinates to the rink."""
    rink["geometry"] = json.loads(rink["geometry"])
    return (rink, get_distance(coordinates, [rink["geometry"]["coordinates"][1], rink["geometry"]["coordinates"][0]]))


def get_rink_closest_to_coordinates(coordinates: list[float]) -> None:
    """Returns the closest rink to a set of coordinates."""
    rinks: list[dict] = get_outdoor_rinks() # this gets the latest data, even if locations are not likely to change very often
    (closest_rink, closest_distance) = get_rink_values(coordinates, rinks[0])
    for i in range(1, len(rinks)):
        rink = rinks[i]
        (rink, rink_distance) = get_rink_values(coordinates, rink)
        if rink_distance < closest_distance:
            closest_rink = rink
            closest_distance = rink_distance
    print(f'The closest rink to the input coordinates is {closest_rink["Public Name"]}. It is {closest_distance} away. Its full information is:\n{closest_rink}')




print('Enter your coordinates as "latitude, longitude".')
coordinates_text = input()
coordinates = parse_coordinates_text(coordinates_text)
get_rink_closest_to_coordinates(coordinates)

