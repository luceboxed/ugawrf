# This module generates our text forecasts.

from wrf import getvar, to_np, ll_to_xy
import numpy as np

def get_text_data(wrf_file, airport, coords, hours, forecast_times, run_time):
    forecast_time = forecast_times[1].strftime("%Y-%m-%d %H:%M UTC")
    x, y = ll_to_xy(wrf_file, coords[0], coords[1])
    output_lines = []
    output_lines.append(f"UGA-WRF {run_time} - Init: {forecast_times[0]} - Text Forecast for {airport.upper()}")
    output_lines.append(f"Forecast Start Time: {forecast_time}")
    output_lines.append(f"UTC (Fcst) Hr | Temp | Dewp | Wind (dir) | Pressure")
    for t in range(1, hours):
        t_data = getvar(wrf_file, "T2", timeidx=t)[y, x].values
        td_data = getvar(wrf_file, "td2", timeidx=t)[y, x].values
        wspd_data = getvar(wrf_file, "wspd_wdir10", timeidx=t, units="mph")
        pressure_data = getvar(wrf_file, "AFWA_MSLP", timeidx=t)[y, x].values
        t_f = (t_data - 273.15) * 9/5 + 32
        td = td_data * 9/5 + 32
        wspd = to_np(wspd_data[0][y, x])
        wdir = to_np(wspd_data[1][y, x])
        pressure_mb = to_np(pressure_data) / 100
        output_lines.append(f"{forecast_times[t].strftime('%H UTC')} ({str(t).zfill(2)}) | {t_f:.1f} F | {td:.1f} F | {wspd:.1f} mph {deg_to_cardinal(wdir)} | {pressure_mb:.1f} mb")
    return output_lines

def deg_to_cardinal(deg):
    # N, NNE NE, etc
    if deg >= 348.75 or deg < 11.25:
        return 'N'
    elif 11.25 <= deg < 33.75:
        return 'NNE'
    elif 33.75 <= deg < 56.25:
        return 'NE'
    elif 56.25 <= deg < 78.75:
        return 'ENE'
    elif 78.75 <= deg < 101.25:
        return 'E'
    elif 101.25 <= deg < 123.75:
        return 'ESE'
    elif 123.75 <= deg < 146.25:
        return 'SE'
    elif 146.25 <= deg < 168.75:
        return 'SSE'
    elif 168.75 <= deg < 191.25:
        return 'S'
    elif 191.25 <= deg < 213.75:
        return 'SSW'
    elif 213.75 <= deg < 236.25:
        return 'SW'
    elif 236.25 <= deg < 258.75:
        return 'WSW'
    elif 258.75 <= deg < 281.25:
        return 'W'
    elif 281.25 <= deg < 303.75:
        return 'WNW'
    elif 303.75 <= deg < 326.25:
        return 'NW'
    else:
        return 'NNW'
