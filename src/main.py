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


def get_configs(config_file_path: str) -> dict:
    try:
        with open(config_file_path, 'r') as f:
            custom_config = json.load(f)
        logging.info(custom_config)
        return custom_config
    except FileNotFoundError:
        print(f"Error: Custom config file not found at {config_file_path}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {config_file_path}")


file_path = './configs/config.json'
app.config.update(get_configs(file_path))


def contains_any_substring(text: str, substrings: list[str]) -> bool:
    print([substring for substring in substrings])
    print(text)
    return any(
        text.find(substring) > -1
        for substring
        in substrings
    )


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


def get_response(url: str, params: dict) -> json:
    try:
        response: Response = requests.get(url, params=params)
        return response.json()
    except ConnectionError as e:
        print(f"encountered connection error {e}")
        exit(1)
    except HTTPError as e:
        print(f"encountered http error {e}")
        exit(1)
    except TimeoutError as e:
        print(f"timeout error {e}")
        exit(1)
    except TooManyRedirects as e:
        print(f"too many redirects {e}")
        exit(1)


def summarize_places(data: list[json]):
    print(f"obtained data for these places")
    [
        print(f"{place_name}: {count}")
        for (place_name, count)
        in Counter([item['place_guess']
                    for item in data['results']]
                   ).items()
    ]


def build_formatted_observations(filtered_data: list[json]) -> list[dict]:
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
        except TypeError as e:
            print(f"encountered an exception {e}")
        result_obs.append(data)
    return result_obs


def build_params() -> dict:
    # Coordinates to search around
    latitude = app.config["latitude"]
    longitude = app.config["longitude"]
    # Radius in kilometers
    radius_km = app.config["radius_in_kms"]
    # Date range
    now = datetime.utcnow()
    yesterday = now - timedelta(days=app.config["delta_in_days"])
    d1 = yesterday.strftime('%Y-%m-%dT%H:%M:%S')
    d2 = now.strftime('%Y-%m-%dT%H:%M:%S')
    # iNaturalist API endpoint
    # Request parameters
    return {
        'lat': latitude,
        'lng': longitude,
        'radius': radius_km,
        'd1': d1,
        'd2': d2,
        'order_by': 'created_at',
        'order': 'desc',
        'per_page': 100
    }

@app.route('/stream')
def obs_stream() -> Response:
    params = build_params()
    url = app.config["endpoint_url"]
    filtered_data = []
    data = get_response(url, params)
    try:
        summarize_places(data)
        # filter the data by places and having a species guess
        place_terms = app.config["location_filter_by"]
        filtered_data: list[dict] = [
            result for result in data['results']
            if result['species_guess'] and contains_any_substring(result['place_guess'], place_terms)
        ]
    except TypeError as e:
        logging.error(f"issue outputting or filtering results {e}")
    # Output results
    print(f"Found {len(filtered_data)} observations in filtered places with a species guess in the last 24 hours:")
    result_obs = build_formatted_observations(filtered_data)
    return Response(stream_with_context(generate_data(result_obs)), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)
