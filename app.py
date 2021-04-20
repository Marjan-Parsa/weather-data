import csv
import logging
import os
from datetime import date, timedelta

from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

import exc
import gmap
import temperature


logger = logging.getLogger(__name__)

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db/db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db
db = SQLAlchemy(app)

# Init ma
ma = Marshmallow(app)


# City Class/Model
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)


# Temperature Class/Model
class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    date = db.Column(db.DateTime, nullable=False)
    max = db.Column(db.Float, nullable=False)
    min = db.Column(db.Float, nullable=False)


# City Schema
class CitySchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'lat', 'lon')


city_schema = CitySchema()


# Temperature Schema
class TemperatureSchema(ma.Schema):
    class Meta:
        fields = ('id', 'city_id', 'date', 'max', 'min')


temperature_schema = TemperatureSchema()
temperatures_schema = TemperatureSchema(many=True)


def _date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


@app.route('/map', methods=['GET'])
def get_map():
    lat, lon = 40.7127753, -74.0059728
    gmap.display_in_map(lat, lon, map_type='terrain', zoom=3)
    return jsonify({'success': True}), 200


@app.route('/table', methods=['GET'])
def get_table():
    gmap.display_in_table()
    return jsonify({'success': True}), 200


@app.route('/cities', methods=['POST'])
def add_cities():
    cities = request.json.get('cities')
    for city_name in cities:
        if not db.session.query(City).filter(City.name == city_name).first():
            # add city
            lat, lon = gmap.get_geo_data_by_name(city_name)
            city = City(name=city_name, lat=lat, lon=lon)
            db.session.add(city)
            db.session.commit()

            # Due to the bellow error (restriction) this loop sends the request for each day
            # {'error': 'Only 1 day per request is allowed with this key. Please break up into multiple requests, or upgrade your key.'}
            start_date = date(2020, 12, 1)
            end_date = date(2021, 2, 1)
            bulk_temperature = []
            for single_date in _date_range(start_date, end_date):
                try:
                    min, max = temperature.get_city_temperature_data(lat, lon, single_date,
                                                                     single_date + timedelta(days=1))
                except exc.GetTemperatureError:
                    break
                bulk_temperature.append(Temperature(city_id=city.id, date=single_date, max=max, min=min))
            db.session.bulk_save_objects(bulk_temperature)
            db.session.commit()

            logger.info('The data of %s inserted.', city_name)
        else:
            logger.info('The %s exists in DB.', city_name)

    return jsonify({'success': True}), 200


@app.route('/city', methods=['POST'])
def add_city():
    name = request.json.get('name')
    lat = request.json.get('lat')
    lon = request.json.get('lon')
    city = City(name=name, lat=lat, lon=lon)
    db.session.add(city)
    db.session.commit()
    return city_schema.jsonify(city)


@app.route('/temperature', methods=['POST'])
def add_temperature():
    date = request.json.get('date')
    max = request.json.get('max')
    min = request.json.get('min')
    city_name = request.json.get('city_name')
    city = db.session.query(City).filter(City.name == city_name).first()
    if not city:
        return jsonify({'error': 'City not found'}), 404
    temperature = Temperature(city=city, date=date, max=max, min=min)
    db.session.add(temperature)
    db.session.commit()
    return temperature_schema.jsonify(temperature)


@app.route('/export', methods=['GET'])
def export():
    outfile = open('output/city-temperature.cvs', 'w')
    outcsv = csv.writer(outfile)
    header = ['name', 'date', 'min', 'max', 'lat', 'lon']
    outcsv.writerow(header)
    records = db.session.query(City.name, Temperature.date, Temperature.min, Temperature.max, City.lat, City.lon).join(
        Temperature).all()
    [outcsv.writerow([getattr(curr, column) for column in header]) for curr in records]
    outfile.close()
    return jsonify({'success': True}), 200


# Run server
if __name__ == '__main__':
    app.run(debug=True)
