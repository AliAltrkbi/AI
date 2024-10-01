from pyowm.owm import OWM

BOT_TOKEN = '5a38db36afbbae4aa06ddde8c4cc9d27'
owm = OWM(BOT_TOKEN)

mgr = owm.weather_manager()

def get_forecasts(lat, lon):
    mgr = owm.weather_manager()
    observation = mgr.forecast_at_coords(lat, lon, '3h')
    forecasts = observation.forecast

    location = forecasts.location
    loc_name = location.name
    loc_lat = location.lat
    loc_lon = location.lon

    results = []

    for forecast in forecasts:
        time = forecast.reference_time('iso')
        status = forecast.status
        detailed = forecast.detailed_status
        temperature = forecast.temperature('celsius')
        temp = temperature['temp']
        temp_min = temperature['temp_min']
        temp_max = temperature['temp_max']

        results.append("""
        Location : {} Lat : {} Lon {}
        Time : {}
        Status : {}
        Detailed : {}
        Temperature : {}
        Min Temperature : {}
        Max Temperature : {}
        """.format(loc_name, loc_lat, loc_lon, time,
                   status, detailed, temp, temp_min, temp_max))

    return "".join(results[:10])


if __name__ == "__main__":
    print(get_forecasts(35, 35))