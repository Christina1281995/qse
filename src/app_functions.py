import pvlib  # solar calculations
import pandas as pd  # for db wrangling
import matplotlib.pyplot as plt  # for visualization
import requests
import json
import geocoder
import tzwhere as tzwhere
from tzwhere import tzwhere

geocodeAPI = "uTxP90JzA0grdbfUKUlo76J2EG0PAqKE"
googleElevAPI = "AIzaSyAwdmhP9nIFlTPVHNE3h6iu7kD85xmHTBs"


def elevation(lat, long):
    """uses latitude and longitude from user input to find the according elevation
    value through Google elevation API"""

    # TODO: restrict API key

    latitude = str(lat)
    longitude = str(long)
    url = "https://maps.googleapis.com/maps/api/elevation/json?locations=" + latitude + "%2C" + longitude + \
          "&outputFormat=json&key=" + googleElevAPI

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    # print(f"Elevation at {str(lat)}, {str(long)} = {str(response.text)}")

    # Parse as JSON object to access elevation
    parsed = json.loads(response.text)
    elev = parsed['results'][0]['elevation']

    # cast to integer to drop the decimal places
    # print(int(elev))

    return int(elev)


def location_name(lat, long):
    """ Using mapQuest and a reverse geocoding process, a location name is generated
    for the pvlib object and to be used in the result presentation"""

    g = geocoder.mapquest([lat, long], method='reverse', key=geocodeAPI)
    # print(g.json['city'])
    # print(g.json['address'])
    # print(g.json['country'])
    try:
        name = g.json['address'] + ", " + g.json['city']
        # print(name)
    except:
        name = "n/a"

    return name


def timezones(lat, long):
    """gets timezone information for given location using tzwhere and pytz"""

    tz = tzwhere.tzwhere()
    timezone_str = tz.tzNameAt(lat, long)
    # print(timezone_str)

    return timezone_str


def tilt(lat):
    """Takes the latitude from user input and calculates optimal tilt for summer, winter and year-round.
    Summer and winter tilts are based on:
    https://sinovoltaics.com/learning-center/system-design/solar-panel-angle-tilt-calculation/#targetText=Calculation%20method%20one,34%20%2B%2015%20%3D%2049%C2%B0

    winter: multiplying the latitude by 0.9 and then adding 29°
    summer: multiplying the latitude by 0.9 and subtracting 23.5°
    spring and fall: 2.5° is subtracted from the latitude
    year-round: tilt angle that is equal to the latitude
    https://unboundsolar.com/blog/solar-panel-azimuth-angle#:~:text=To%20optimize%20overall%20production%20year,latitude%20plus%2010%2D15%C2%B0
    """

    # create dictionary for various tilt angles
    tilts = {'winter': abs((lat * 0.9) + 29), 'summer': abs((lat * 0.9) - 23.5), 'spring and fall': abs(lat - 2.5),
             'year round': abs(lat)}

    return tilts


def extraterrestrial_radiation():
    """ general extra terrestrial radiation
    Many solar power algorithms start with the irradiance incident on the top of the Earth's atmosphere,
    often known as the extraterrestrial radiation. pvlib has four different algorithms to calculate the
    yearly cycle of the extraterrestrial radiation given the solar constant. As of pvlib 0.4, each method can
    accept many input types (day of year, arrays of day of year, date-times, DatetimeIndex, etc.)
    and will consistently return the appropriate output type."""

    # DatetimeIndex in yields a TimeSeries out
    times = pd.date_range('2014-01-01', '2015-01-01', freq='1h')

    spencer = pvlib.irradiance.get_extra_radiation(times, method='spencer')
    asce = pvlib.irradiance.get_extra_radiation(times, method='asce')
    # ephem = pvlib.irradiance.get_extra_radiation(times, method='pyephem')
    nrel = pvlib.irradiance.get_extra_radiation(times, method='nrel')


def solar_position_and_clearsky(loc, times):
    """ Calculate the solar position and clear sky estimates of GHI, DNI, and/or DHI
    at this location. See the online documentation for clear sky modeling examples
    http://pvlib-python.readthedocs.io/en/stable/user_guide/clearsky.html
    Here we only generate db for the functions below."""

    # pvlib function to calculate the solar zenith, azimuth etc. at this location
    # loc is a location object that includes lat, long, timezone, elevation and a name
    # RETURNS 'apparent_zenith', 'zenith', 'apparent_elevation', 'elevation',
    # 'azimuth', 'equation_of_time'
    ephem_data = loc.get_solarposition(times)

    # Calculates the clear sky estimates of GHI, DNI, and/or DHI at the given location
    # RETURNS 'ghi', 'dni', 'dhi'
    irradiance_data = loc.get_clearsky(times, solar_position=ephem_data)
    # print(f"Clear Sky: {str(list(irradiance_data))}")

    return ephem_data, irradiance_data


def total_irradiance(loc, times, surface_azimuth, tilts, ephem_data, irrad_data, surface_type):
    # Calculate air-mass
    sun_zen = ephem_data['apparent_zenith']
    air_mass = pvlib.atmosphere.get_relative_airmass(sun_zen)

    # Determine extraterrestrial radiation from the day of year
    dni_et = pvlib.irradiance.get_extra_radiation(times.dayofyear)

    # Logic for handling the 4 different tilts
    results = {}
    irradiance = {}
    # Iterate over each tilt angle
    # Results[tilt] = 'poa_global', 'poa_direct', 'poa_diffuse', 'poa_sky_diffuse', 'poa_ground_diffuse'
    for panel_tilt in tilts:
        results[panel_tilt] = pvlib.irradiance.get_total_irradiance(
            tilts[panel_tilt], surface_azimuth, ephem_data['apparent_zenith'], ephem_data['azimuth'],
            dni=irrad_data['dni'], ghi=irrad_data['ghi'], dhi=irrad_data['dhi'],
            dni_extra=dni_et, airmass=air_mass,
            model='klucher',
            surface_type=surface_type)

    # New dataframe with only every 2nd row, since the rows alternate between 0:00 and 12:00
    for panel_tilt in tilts:
        irradiance[panel_tilt] = results[panel_tilt].iloc[1::2]

    # maxvalue = max(irradiance, key=irradiance.get)
    # print("maxvalue")
    # print(maxvalue)

    # Generate a result plot for each
    for panel_tilt in tilts:
        # Round actual tilt to two decimal places for plot title
        angle = round(tilts[panel_tilt], 2)

        irradiance[panel_tilt].plot()
        plt.title(f"Total irradiance with an optimal {str(panel_tilt)} tilt: {str(angle)}°")
        plt.ylim(-50, 1100)
        plt.ylabel('Irradiance (W/m^2)')
        plt.savefig(f"static/figures/{str(panel_tilt)}.png")
        # plt.show()

    # for panel_tilt in tilts:
    #     print(f"{str(panel_tilt)}")
    #     print(list(irradiance[panel_tilt]))
    #     print(irradiance[panel_tilt])

    # Return dict with irradiance db for each tilt
    return results


def tmy(lat, long, loc, rotation, tilts):
    """Get typical meteorological year db from PVGIS via io tools in pvlib"""

    # Get PVGIS tmy db
    # TODO: Dynamically set start and end year?
    df_tmy, months_selected, inputs, metadata = pvlib.iotools.get_pvgis_tmy(lat, long, outputformat='json',
                                                                            usehorizon=True, userhorizon=None,
                                                                            startyear=2005, endyear=2015,
                                                                            url=pvlib.iotools.pvgis.URL,
                                                                            map_variables=True, timeout=60)

    # Check TMY db
    # print("df_tmy")
    # print(list(df_tmy))
    # print("df_tmy['ghi']")
    # print(df_tmy['ghi'].head(30))

    # Save figures based on TMY
    # df_tmy['ghi'].plot()
    # plt.title("Global Horizontal Irradiance in a Typical Meteorological Year")
    # plt.ylim(-50, 1100)
    # plt.ylabel('Irradiance Watt/m^2')
    # plt.savefig(f"static/figures/tmy_ghi.png")
    # # plt.show()

    # df_tmy['dhi'].plot()
    # plt.title("Diffuse Horizontal Irradiance in a Typical Meteorological Year")
    # plt.ylim(-50, 1100)
    # plt.ylabel('Irradiance Watt/m^2')
    # plt.savefig(f"static/figures/tmy_dhi.png")
    # # plt.show()

    # Filter TMY db for only GHI DNI and DHI
    df_tmy_filtered = df_tmy[['ghi', 'dni', 'dhi']]

    t_start_summer = -4656
    t_end_summer = -4632

    t_start_winter = -264
    t_end_winter = -240

    t_start_spring = -6864
    t_end_spring = -6840

    t_start_fall = -2448
    t_end_fall = -2424

    if long < -70:
        t_start_summer = t_start_summer + 6
        t_end_summer = t_end_summer + 6

        t_start_winter = t_start_winter + 6
        t_end_winter = t_end_winter + 6

        t_start_spring = t_start_spring + 6
        t_end_spring = t_end_spring + 6

        t_start_fall = t_start_fall + 6
        t_end_fall = t_end_fall + 6

    if long > 70:
        t_start_summer = t_start_summer - 6
        t_end_summer = t_end_summer - 6

        t_start_winter = t_start_winter - 6
        t_end_winter = t_end_winter - 6

        t_start_spring = t_start_spring - 6
        t_end_spring = t_end_spring - 6

        t_start_fall = t_start_fall - 6
        t_end_fall = t_end_fall - 6

    # Plot irradiance db at location (not yet considering panel tilt etc.)
    df_tmy_filtered.iloc[t_start_summer:t_end_summer].plot()
    plt.title("Summer Solstice: DNI, DHI, and GHI in a Typical Meteorological Year")
    plt.ylim(-50, 1100)
    plt.ylabel('Irradiance Watt/m^2')
    plt.savefig(f"static/figures/tmy_summer.png")

    # # Plot irraidiance db at location (not yet considering panel tilt etc.)
    # df_tmy_filtered.iloc[-4656:-4632].plot()
    # # plt.rcParams["figure.figsize"] = (20, 10)
    # plt.title("Summer Solstice: DNI, DHI, and GHI in a Typical Meteorological Year")
    # plt.ylim(-50, 1100)
    # plt.ylabel('Irradiance Watt/m^2')
    # plt.savefig(f"static/figures/tmy_summer.png")

    df_tmy_filtered.iloc[t_start_winter:t_end_winter].plot()
    plt.title("Winter Solstice: DNI, DHI, and GHI in a Typical Meteorological Year")
    plt.ylim(-50, 1100)
    plt.ylabel('Irradiance Watt/m^2')
    plt.savefig(f"static/figures/tmy_winter.png")

    df_tmy_filtered.iloc[t_start_spring:t_end_spring].plot()
    plt.title("Spring Equinox: DNI, DHI, and GHI in a Typical Meteorological Year")
    plt.ylim(-50, 1100)
    plt.ylabel('Irradiance Watt/m^2')
    plt.savefig(f"static/figures/tmy_spring.png")

    df_tmy_filtered.iloc[t_start_fall:t_end_fall].plot()
    plt.title("Fall Equinox: DNI, DHI, and GHI in a Typical Meteorological Year")
    plt.ylim(-50, 1100)
    plt.ylabel('Irradiance Watt/m^2')
    plt.savefig(f"static/figures/tmy_fall.png")

    # print("months_selected")
    # print(months_selected)
    # print("inputs")
    # print(inputs)
    # print("metadata")
    # print(metadata)

    # ------------------------- READ TMY AND COERCE ----------------------------------

    # PVGIS TMY read and coerce into one year only works with US db (i.e. includes states etc)
    # Luckily, since its open source, I can apply the year coercion to this df

    times = df_tmy.index - pd.Timedelta('30min')

    data_ymd = pd.to_datetime(df_tmy.index, format='%m/%d/%Y')
    # shift the time column so that midnite is 00:00 instead of 24:00
    # shifted_hour = df_tmy['Time (HH:MM)'].str[:2].astype(int) % 24
    # # shift the dates at midnite so they correspond to the next day
    # data_ymd[shifted_hour == 0] += datetime.timedelta(days=1)
    data_index = pd.DatetimeIndex(data_ymd)
    data_ymd = data_ymd.map(lambda dt: dt.replace(year=2015))
    # data_ymd.iloc[-1] = data_ymd.iloc[-1].replace(year=2015 + 1)
    # NOTE: as of pvlib-0.6.3, min req is pandas-0.18.1, so pd.to_timedelta
    # unit must be in (D,h,m,s,ms,us,ns), but pandas>=0.24 allows unit='hour'
    df_tmy.index = data_ymd
    # print(df_tmy.head(30))

    # df_tmy.plot()
    # plt.title("Hypothetical Year")
    # plt.ylim(-50, 1100)
    # plt.ylabel('Irradiance Watt/m^2')
    # plt.savefig(f"static/figures/tmy_hypo.png")
    # plt.show()

    df_tmy_ghi = df_tmy[['ghi']]
    df_tmy_dni = df_tmy[['dni']]
    df_tmy_dhi = df_tmy[['dhi']]
    df_tmy_ghi.plot()
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    plt.title("Hypothetical Year: Global Horizontal Irradiance")
    plt.ylim(-50, 1100)
    plt.ylabel('Irradiance Watt/m^2')
    plt.savefig(f"static/figures/tmy_hypo_ghi.png")
    # plt.show()

    df_tmy_dni.plot()
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    plt.title("Hypothetical Year: Direct Normal Irradiance")
    plt.ylim(-50, 1100)
    plt.ylabel('Irradiance Watt/m^2')
    plt.savefig(f"static/figures/tmy_hypo_dni.png")

    df_tmy_dhi.plot()
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    plt.title("Hypothetical Year: Direct Horizontal Irradiance")
    plt.ylim(-50, 1100)
    plt.ylabel('Irradiance Watt/m^2')
    plt.savefig(f"static/figures/tmy_hypo_dhi.png")

    solar_position = loc.get_solarposition(times)

    solar_position.index += pd.Timedelta('30min')

    # Fixed Tilt POA total irradiance
    for panel_tilt in tilts:
        df_poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilts[panel_tilt],
            surface_azimuth=rotation,
            dni=df_tmy['dni'],
            ghi=df_tmy['ghi'],
            dhi=df_tmy['dhi'],
            solar_zenith=solar_position['apparent_zenith'],
            solar_azimuth=solar_position['azimuth'],
            model='isotropic')

        df_poa_filtered = df_poa[['poa_global', 'poa_direct', 'poa_diffuse']]

        df_poa_filtered.plot()
        plt.title("Global, Direct, and Diffuse Irradiance at Plane Of Array")
        plt.ylim(-50, 1100)
        plt.ylabel('Irradiance Watts( m^2')
        plt.savefig(f"static/figures/poa_tmy_{str(panel_tilt)}.png")
        # plt.show()

        # df_poa['poa_direct'].plot()
        # plt.title("Direct Irradiance at Plane Of Array")
        # plt.ylim(-50, 1100)
        # plt.ylabel('??')
        # plt.savefig(f"static/figures/poa_direct.png")
        # # plt.show()
        #
        # df_poa['poa_diffuse'].plot()
        # plt.title("Diffuse Irradiance at Plane Of Array")
        # plt.ylim(-50, 1100)
        # plt.ylabel('??')
        # plt.savefig(f"static/figures/poa_diffuse.png")
        # # plt.show()
