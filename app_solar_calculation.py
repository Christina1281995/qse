import pvlib
from datetime import date
import app_functions
import pandas as pd  # for db wrangling


def run(lat_in, long_in, rotate_in, surface_type, year):

    # Convert strings to numerics
    lat = float(lat_in)
    long = float(long_in)
    rotation = float(rotate_in)

    # Calculate ideal panel tilts based on latitude
    tilts = app_functions.tilt(lat)

    # Print for check
    # print(lat_in, long_in, rotate_in)
    # print(lat, long, rotation)
    # print(f"Tilts: {str(tilts)}")

    # -------------------------- SET LOCATION OBJECT AND TIMES FOR SOLAR CALCULATION ---------------------------

    # Get elevation at the point the user has chosen
    elev = app_functions.elevation(lat, long)

    # Get a name for the location via reverse geocoding
    location_name = app_functions.location_name(lat, long)

    # Determine time zone for the location
    timezone = app_functions.timezones(lat, long)

    # Create a location object in pvlib
    loc = pvlib.location.Location(lat, long, timezone, elev, location_name)

    # Define time range using pandas
    # TODO: dynamically set times
    historical_year = int(year)
    start_time = str(historical_year) + '-01-01'
    end_time = str(historical_year + 1) + '-01-01'
    times = pd.date_range(start=start_time, end=end_time, freq='12h', tz=loc.tz)

    # --------------------- CLEARSKY AND TOTAL IRRADIANCE BASED ON LOC AND PVLIB -------------------------------

    # generic function for extraterrestrial radiation
    # functions.extraterrestrial_radiation()

    # Calculate solar positions and clear sky irradiance values
    ephem_data, irradiance_data = app_functions.solar_position_and_clearsky(loc, times)

    # Calculate irradiance values for each tilt (dictionary with key tilt)
    # tilt_irradiances = functions.total_irradiance(loc, times, rotation, tilts, ephem_data,
    # irradiance_data, surface_type)
    app_functions.total_irradiance(loc, times, rotation, tilts, ephem_data, irradiance_data, surface_type)

    # ----------------------------- PVGIS TMY ACQUISITION AND CALCULATIONS------------------------------------

    # get DF for TMY from PVLIB
    app_functions.tmy(lat, long, loc, rotation, tilts)

    # -------------------------- ADDITIONAL PARAMETERS TO SEND TO RESULTS PAGE -------------------------------

    # Today's date for the output PDF
    today = date.today()

    # Pvlib Version for PDF output
    version = str(pvlib.__version__)

    # Round tilts and send to the results for PDF
    rounded_tilts = {}
    for tilt in tilts:
        rounded_tilts[tilt] = round(tilts[tilt], 2)

    return location_name, today, version, loc, surface_type, rotation, rounded_tilts, historical_year
