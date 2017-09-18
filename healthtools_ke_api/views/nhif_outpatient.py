from flask import Blueprint, request, jsonify, make_response, json, current_app
from bs4 import BeautifulSoup
from elastic_search import Elastic

from healthtools_ke_api.analytics import track_event

import requests

nhif_outpatient_api = Blueprint('nhif_outpatient_api', __name__)

@nhif_outpatient_api.route('/', methods=['GET'])
def index():
    '''
    Landing endpoint
    This function displays all the endpoints available
    in the NHIF inpatient registry.

    Returns:
    json.  The response ::

        {
            "name": "API to the NHIF inpatient registry",
            "authentication": [],
            "endpoints": {
                "/": {"methods": ["GET"]},
                "/nhif-outpatient/search.json": {
                    "methods": ["GET"],
                    "args": {
                        "q": {"required": True}
                    }
                },
            }
        }
    '''
    msg = {
        "name": "API to the NHIF inpatient registry",
        "authentication": [],
        "endpoints": {
            "/": {"methods": ["GET"]},
            "/nhif-outpatient/search.json": {
                "methods": ["GET"],
                "args": {
                    "q": {"required": True}
                }
            },
        }
    }
    return jsonify(msg)

@nhif_outpatient_api.route('/search.json', methods=['GET'])
def search():
    """This function searches through the Kenyan NHIF Outpatient facility registry API
    based on the search query supplied by user.

    Query string: 
         q (str):  The name of the NHIF Outpatient CS facility to lookup.
        
    
    Returns:
       json.  The response can be any of the following ::

          When no query string was supplied: 

          {
            "error": "A query is required.",
            "results": "",
            "data": {"nhif_outpatient": []}
          }

          When no NHIF Outpatient facility was found

          {
            "message" = "No NHIF Outpatient facility by that name found."
          }

          when NHIF Outpatient facilities was found

          {
            "data": {"nhif_outpatient": <nhif_outpatients>},
            "status": "success",
                
          }

          When an error occurs

          {
              "status": "error",
              "message": <error_message>,
              "data": {"nhif_outpatient": []}
          }
    """
    try:
        query = request.args.get('q')
        if not query or len(query) < 1:
            return jsonify({
                "error": "A query is required.",
                "results": "",
                "data": {"nhif_outpatient": []}
            })

        response = {}
        es = Elastic()
        nhif_outpatient = es.get_from_elasticsearch('nhif-outpatient', query)

        if not nhif_outpatient:
                response["message"] = "No NHIF Outpatient facility by that name found."

        track_event(current_app.config.get('GA_TRACKING_ID'), 'Nhif-Outpatient', 'search',
                        request.remote_addr, label=query, value=len(nhif_outpatient))

        response["data"] = {"nhif_outpatient": nhif_outpatient}
        response["status"] = "success"

        results = jsonify(response)
        return results

    except Exception as err:
        return jsonify({
            "status": "error",
            "message": str(err),
            "data": {"nhif_outpatient": []}
        })