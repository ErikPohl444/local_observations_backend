import json
import logging

import requests
from datetime import datetime, timedelta
from flask import Flask, Response, stream_with_context
from flask_cors import CORS
import time
from collections import Counter

from requests import HTTPError, TooManyRedirects

app = Flask(__name__)
CORS(app)


def contains_any_substring(text: str, substrings: list[str]):
    return any(text.index(substring) for substring in substrings)


@app.route('/stream')
def obs_stream() -> Response:
    def generate_data(observations: json):
        print("opening")
        for observation in observations:
            print(f"yielding {observation}")
            yield 'data: '
            yield json.dumps(observation)
            yield '\n\n'
            time.sleep(1)
        yield 'data: end\n\n'
        print("closing")

    # Coordinates for Arlington, MA
    latitude = 42.4154
    longitude = -71.1565

    # Radius in kilometers (20 miles ≈ 32.19 km)
    radius_km = 32.19

    # Date range: last 24 hours
    now = datetime.utcnow()
    yesterday = now - timedelta(days=3)
    d1 = yesterday.strftime('%Y-%m-%dT%H:%M:%S')
    d2 = now.strftime('%Y-%m-%dT%H:%M:%S')

    # iNaturalist API endpoint
    url = 'https://api.inaturalist.org/v1/observations'

    # Request parameters
    params = {
        'lat': latitude,
        'lng': longitude,
        'radius': radius_km,
        'd1': d1,
        'd2': d2,
        'order_by': 'created_at',
        'order': 'desc',
        'per_page': 100
    }

    filtered_data = []
    try:
        response: Response = requests.get(url, params=params)
        data: json = response.json()
    except ConnectionError:
        print("connection error")
        exit(1)
    except HTTPError:
        print("http error")
        exit(1)
    except TimeoutError:
        print("timeout error")
        exit(1)
    except TooManyRedirects:
        print("too many redirects")
        exit(1)
    try:
        print(f"obtained data for these places")
        [
            print(f"{place_name}: {count}")
            for (place_name, count)
            in Counter([item['place_guess']
                        for item in data['results']]
                       ).items()
        ]
        # filter the data by places and having a species guess
        place_terms = ['Arlington', 'Horn Pond', 'Concord']
        filtered_data: list[dict] = [
            result for result in data['results']
            if result['species_guess'] and contains_any_substring(result['place_guess'], place_terms)
        ]
    except TypeError:
        logging.error("issue outputting or filtering results ")

    # Output results
    print(f"Found {len(filtered_data)} observations in filtered places with a species guess in the last 24 hours:")

    result_obs = []
    for obs in filtered_data:
        print(f"{obs['observed_on']} - {obs['species_guess']} ({obs['place_guess']})")
        try:
            data = {
                "obs_date": obs['observed_on'],
                "obs_species_guess": obs['species_guess'],
                "obs_place_guess": obs['place_guess'],
                "obs_observed_on_string": obs['observed_on_string']
            }
        except TypeError:
            print("encountered an exception")
        result_obs.append(data)
    return Response(stream_with_context(generate_data(result_obs)), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)
