import json

import requests
from datetime import datetime, timedelta
from flask import Flask, Response


def contains_any_substring(text, substrings):
  """
  Checks if a string contains any of the substrings in a list.

  Args:
    text: The string to search in.
    substrings: A list of substrings to search for.

  Returns:
    True if the string contains at least one of the substrings, False otherwise.
  """
  for substring in substrings:
    if substring in text:
      return True
  return False

app = Flask(__name__)

@app.route('/stream')
def obs_stream():
    # Coordinates for Arlington, MA
    latitude = 42.4154
    longitude = -71.1565

    # Radius in kilometers (20 miles ≈ 32.19 km)
    radius_km = 32.19

    # Date range: last 24 hours
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
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

    # API call
    response = requests.get(url, params=params)
    place_terms = ['Arlington', 'Horn Pond', 'Concord']
    data = response.json()
    filtered_data = [x for x in data['results'] if x['species_guess'] and contains_any_substring(x['place_guess'], place_terms) ]
    # Output results
    print(f"Found {len(filtered_data)} observations with a species guess in the last 24 hours:")

    result_obs = []
    for obs in filtered_data:
        print(f"{obs['observed_on']} - {obs['species_guess']} ({obs['place_guess']})")
        data = {"obs_date": obs['observed_on'], "obs_species_guess": obs['species_guess'], "obs_place_guess": obs['place_guess']}
        result_obs.append(data)
    return Response(json.dumps(result_obs), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)