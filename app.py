import sqlite3
from shapely.geometry import Point
from shapely.wkt import loads
from flask import Flask, request, render_template, redirect, url_for, jsonify
import requests

app = Flask(__name__)
DB_NAME = "data/districts.db"

# Helper function to connect to the database
def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Return results as dict-like objects
    return conn

# Helper function to get districts by coordinate
def get_districts_by_coordinate(lat, lon):
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch all districts with their geometries
    cursor.execute("SELECT id, name, chamber, district, party, geometry, committee, notes FROM districts")
    districts = cursor.fetchall()

    point = Point(lon, lat)  # Create a Shapely Point object for the coordinate
    matching_districts = []

    for district in districts:
        geometry = district["geometry"]
        if geometry:  # Ensure geometry is not null
            polygon = loads(geometry)  # Convert WKT geometry to Shapely Polygon
            if polygon.contains(point):  # Check if the point is inside the polygon
                matching_districts.append({
                    "id": district["id"],
                    "name": district["name"],
                    "chamber": district["chamber"],
                    "district": district["district"],
                    "party": district["party"],
                    "committee": district["committee"],
                    "notes": district["notes"],
                })

    conn.close()
    return matching_districts

# Homepage route to render map
@app.route("/")
def index():
    return render_template("map.html")

@app.route("/process-coordinate", methods=["POST"])
def process_coordinate():
    data = request.json
    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        return jsonify({"error": "Invalid coordinates"}), 400

    redirect_url = url_for("legislators", lat=lat, lon=lon)
    return jsonify({"redirect_url": redirect_url})

@app.route("/legislators/<lat>/<lon>", methods=["GET", "POST"])
def legislators(lat, lon):
    try:
        # Fetch districts for the given latitude and longitude
        districts = get_districts_by_coordinate(lat, lon)
        
        if request.method == "POST":
            # Get the district ID and the updated notes from the form
            district_id = request.form['district_id']
            notes = request.form['notes']
            # Update the notes in the database
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE districts SET notes = ? WHERE id = ?", (notes, district_id))
            conn.commit()
            conn.close()

            # Redirect to the same page with the updated data
            return redirect(url_for('legislators', lat=lat, lon=lon))

        return render_template("legislators.html", districts=districts, lat=lat, lon=lon)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
