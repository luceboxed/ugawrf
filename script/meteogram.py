# This module generates our meteograms.

import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from wrf import getvar, ll_to_xy, to_np
import numpy as np
import os

def plot_meteogram(wrf_file, airport, coords, output_path, forecast_times, wrfhours, run_time):
    x, y = ll_to_xy(wrf_file, coords[0], coords[1])
    hours = np.arange(1, wrfhours)
    times = [forecast_times[t].strftime('%H UTC') for t in hours]
    u_wind = [to_np(getvar(wrf_file, "U10", timeidx=t)[y, x]) for t in hours]
    v_wind = [to_np(getvar(wrf_file, "V10", timeidx=t)[y, x]) for t in hours]
    temperatures = []
    dewpoints = []
    pressures = []
    for t in hours:
        t_data = getvar(wrf_file, "T2", timeidx=t)[y, x].values
        td_data = getvar(wrf_file, "td2", timeidx=t)[y, x].values
        pressure_data = getvar(wrf_file, "AFWA_MSLP", timeidx=t)[y, x].values
        t_f = (t_data - 273.15) * 9/5 + 32
        td_f = to_np(td_data) * 9/5 + 32
        pressure_mb = to_np(pressure_data) / 100
        temperatures.append(t_f)
        dewpoints.append(td_f)
        pressures.append(pressure_mb)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    maxtemp_x = np.argmax(temperatures)
    mintemp_x = np.argmin(temperatures)
    maxdew_x = np.argmax(dewpoints)
    mindew_x = np.argmin(dewpoints)
    max_temp = temperatures[maxtemp_x]
    min_temp = temperatures[mintemp_x]
    max_dew = dewpoints[maxdew_x]
    min_dew = dewpoints[mindew_x] 
    ax1.plot(hours, temperatures, color='red', label='Temperature (°F)')
    ax1.plot(hours, dewpoints, color='green', label='Dewpoint (°F)')
    if any(t <= 32 for t in temperatures):
        ax1.axhline(
            y=32,
            color='blue',
            linestyle='--',
            linewidth=1.5,
            label='Freezing (32°F)'
        )
    ax1.barbs(hours, ax1.get_ylim()[0] * 1.07, u_wind, v_wind, length=6, barb_increments={'half': 2.57222, 'full': 5.14444, 'flag': 25.7222}) 
    ax1.set_ylabel('Temperature / Dewpoint (°F)')
    ax1.set_xlabel('Forecast Hour') 
    ax1.set_xticks(hours)
    ax1.set_xticklabels(times, rotation=45)
    ax1.annotate(f"{max_temp:.1f} F", xy=(maxtemp_x, max_temp), xytext=(maxtemp_x + 1, max_temp), color='red', fontsize=14, ha='center', path_effects=[path_effects.withStroke(linewidth=1, foreground="black")],)
    ax1.annotate(f"{min_temp:.1f} F", xy=(mintemp_x, min_temp), xytext=(mintemp_x + 1, min_temp), color='red', fontsize=14, ha='center', path_effects=[path_effects.withStroke(linewidth=1, foreground="black")],)
    ax1.annotate(f"{max_dew:.1f} F", xy=(maxdew_x, max_dew), xytext=(maxdew_x + 1, max_dew), color='green', fontsize=14, ha='center', path_effects=[path_effects.withStroke(linewidth=1, foreground="black")],)
    ax1.annotate(f"{min_dew:.1f} F", xy=(mindew_x, min_dew), xytext=(mindew_x + 1, min_dew), color='green', fontsize=14, ha='center', path_effects=[path_effects.withStroke(linewidth=1, foreground="black")],)
    ax2 = ax1.twinx()
    maxpressure_x = np.argmax(pressures)
    minpressure_x = np.argmin(pressures)
    max_pressure = pressures[maxpressure_x]
    min_pressure = pressures[minpressure_x]
    ax2.plot(hours, pressures, color='blue', label='Pressure (mb)')
    ax2.set_ylabel('Pressure (mb)')
    ax2.annotate(f"{max_pressure:.1f} mb", xy=(maxpressure_x, max_pressure), xytext=(maxpressure_x + 1, max_pressure), color='blue', fontsize=14, ha='center', path_effects=[path_effects.withStroke(linewidth=1, foreground="black")],)
    ax2.annotate(f"{min_pressure:.1f} mb", xy=(minpressure_x, min_pressure), xytext=(minpressure_x + 1, min_pressure), color='blue', fontsize=14, ha='center', path_effects=[path_effects.withStroke(linewidth=1, foreground="black")],)
    lines_ax1, labels_ax1 = ax1.get_legend_handles_labels()
    lines_ax2, labels_ax2 = ax2.get_legend_handles_labels()
    all_lines = lines_ax1 + lines_ax2
    all_labels = labels_ax1 + labels_ax2
    ax1.legend(all_lines, all_labels, loc="upper left", fancybox=True, framealpha=0.5)
    ax2.legend(all_lines, all_labels, loc="upper left", fancybox=True, framealpha=0.5)
    plt.title(f"UGA-WRF Meteogram for {airport.upper()} starting at {forecast_times[1]} UTC - Init: {forecast_times[0]}")
    plt.grid(True)
    plt.tight_layout()
    plt.annotate(f"UGA-WRF Run {run_time}", xy=(0.01, 0.01), xycoords='figure fraction', fontsize=8, color='black')
    os.makedirs(output_path, exist_ok=True)
    plt.savefig(os.path.join(output_path, "meteogram.png"))
    plt.close()
