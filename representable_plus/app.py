from flask import Flask, request, jsonify, send_from_directory, abort
import os
from utils import with_user_info, Database

app = Flask(__name__, static_folder='vue-project/dist', static_url_path='')
db = Database()

@app.route("/api/")
@with_user_info
def hello_world(user_name, user_id, org_name, org_id): # get user info from django proxy headers
    return {
        "user_name": user_name,
        "user_id": user_id,
        "org_name": org_name,
        "org_id": org_id
    }

# Endpoints to get, post, put, delete turfs 
@app.route("/api/edit", methods=['GET', 'POST', 'PUT', 'DELETE'])
@with_user_info
def edit_turf(user_name, user_id, org_name, org_id):
    allowed_org_id = db.has_permissions_to_access_org(org_id, user_id)
    
    if allowed_org_id is False:
        return jsonify({"error": "Access denied"}), 403

    org_id = allowed_org_id

    if request.method == 'GET':
        # Fetch and return all records for the specified organization
        records = db.get_records(org_id)
        return jsonify(records)

    elif request.method == 'POST':
        # Create a new record
        data = request.json
        tracts = data.get('tracts', [])
        description = data.get('description', {'name': '', 'details': ''})
        
        new_record = db.add_record(tracts, description, org_id)
        return jsonify(new_record), 201

    elif request.method == 'PUT':
        # Edit an existing record
        data = request.json
        record_id = data.get('id')
        tracts = data.get('tracts', [])
        description = data.get('description', {'name': '', 'description': ''})
        
        updated_record = db.edit_record(record_id, tracts, description)
        if updated_record:
            return jsonify(updated_record)
        else:
            return jsonify({"error": "Record not found"}), 404

    elif request.method == 'DELETE':
        # Delete a record
        record_id = request.args.get('id')  # Assuming the record ID is passed as a query parameter
        
        if db.delete_record(record_id):
            return jsonify({"message": "Record deleted successfully"}), 200
        else:
            return jsonify({"error": "Record not found"}), 404
        
@app.route("/api/demographics", methods=['GET', 'POST'])
@with_user_info
def get_demographics(user_name, user_id, org_name, org_id):
    allowed_org_id = db.has_permissions_to_access_org(org_id, user_id)
    
    if allowed_org_id is False:
        return jsonify({"error": "Access denied"}), 403

    org_id = allowed_org_id
    
    if request.method == 'GET':
        # GET method for record_id queries
        record_id = request.args.get('record_id')
        
        if not record_id:
            return jsonify({"error": "record_id parameter is required for GET requests"}), 400
        
        # Fetch the record to get its tracts
        records = db.get_records(org_id)
        record = next((r for r in records if r['id'] == int(record_id)), None)
        
        if not record:
            return jsonify({"error": "Record not found"}), 404
        
        tracts = record.get('tracts', [])
        
    elif request.method == 'POST':
        # POST method for both record_id and tracts
        data = request.json
        record_id = data.get('record_id')
        tracts = data.get('tracts')
        
        if record_id:
            # Fetch the record to get its tracts
            records = db.get_records(org_id)
            record = next((r for r in records if r['id'] == int(record_id)), None)
            
            if not record:
                return jsonify({"error": "Record not found"}), 404
            
            tracts = record.get('tracts', [])
        elif tracts:
            # Use provided tracts list
            if not isinstance(tracts, list):
                return jsonify({"error": "tracts must be an array"}), 400
        else:
            return jsonify({"error": "Either record_id or tracts is required"}), 400
    
    demographics = db.get_demographics(tracts)
    return jsonify(demographics)


@app.route("/api/suggestions/<int:record_id>", methods=['GET'])
@with_user_info
def get_suggestions(record_id, user_name, user_id, org_name, org_id):
    """
    Docstring for get_suggestions
    
    :param record_id: Description
    :param user_name: Description
    :param user_id: Description
    :param org_name: Description
    :param org_id: Description


    Response = {
        "record_id": 42,
        "current_tracts": ["06001400100", "06001400200"],
        "suggestions": [
            {
            "type": "neighboring_tracts",
            "description": "Tracts that share a boundary with your selected tracts",
            "tracts": [
                {
                "neighbor_geoid": "06001400300",
                "neighbor_name": "Census Tract 4003",
                "shared_boundary_pct": 45.23
                }
            ]
            }
        ]
    }
    """

    allowed_org_id = db.has_permissions_to_access_org(org_id, user_id)
    
    if allowed_org_id is False:
        return jsonify({"error": "Access denied"}), 403

    org_id = allowed_org_id
    
    # Fetch the record to get its tracts
    records = db.get_records(org_id)
    record = next((r for r in records if r['id'] == record_id), None)
    
    if not record:
        return jsonify({"error": "Record not found"}), 404
    
    tracts = record.get('tracts', [])
    
    if not tracts:
        return jsonify({"error": "Record has no tracts"}), 400
    
    # Get suggested tract groupings
    suggestions = db.get_suggested_tract_groupings(tracts) 
    
    return jsonify({
        "record_id": record_id,
        "current_tracts": tracts,
        "suggestions": suggestions
    }), 200

# serve Vue static files, keep at the end
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue(path):
    print(path)
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)