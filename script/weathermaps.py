# This module plots our maps.

from wrf import getvar, to_np, latlon_coords, smooth2d, ll_to_xy, interplevel
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import datetime as dt
import cartopy.crs as ccrs
from metpy.plots import ctables, USCOUNTIES
import cartopy.feature as cfeature
from matplotlib import colors
import numpy as np

def plot_variable(product, variable, timestep, output_path, forecast_times, airports, loc, extent, run_time, init_dt, init_str, wrf_file, level=None, partial_bool=False):
    data = getvar(wrf_file, variable, timeidx=timestep)
    data_copy = data.copy()
    if level:
        pressure = getvar(wrf_file, "pressure", timeidx=timestep)
        data_copy = to_np(interplevel(data, pressure, level))
    valid_time = forecast_times[timestep]
    f_hour = int(round((valid_time - init_dt).total_seconds() / 3600))
    valid_time_str = valid_time.strftime("%Y-%m-%d %H:%M UTC")
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection=ccrs.PlateCarree()))
    if extent is not None:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(USCOUNTIES.with_scale('20m'), alpha=0.05)
    lats, lons = latlon_coords(data)
    if product == 'temperature':
        data_copy = (data_copy - 273.15) * 9/5 + 32
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='nipy_spectral', levels=np.arange(-10, 110, 5), extend='both')
        smooth_temp = smooth2d(data_copy, 4)
        ax.contour(to_np(lons), to_np(lats), to_np(smooth_temp), levels=[32], linestyles='dashed')
        plot_title = f"2m Temperature (°F) (32°F Dashed) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Temp (°F)"
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
    elif product == '1hr_temp_c':
        if partial_bool:
            print(f'-> skipping {product} {timestep} due to partial flag being enabled')
            return
        if timestep > 0:
            temp_now = getvar(wrf_file, "T2", timeidx=timestep)
            temp_prev = getvar(wrf_file, "T2", timeidx=timestep - 1)
            temp_change_1hr = (temp_now - temp_prev) * 9/5
            data_copy = temp_change_1hr.copy()
        else:
            ax.annotate("This product starts on hour 1.", xy=(0.5, 0.5), xycoords='figure fraction', fontsize=8, color='black', ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
            temp_change_1hr = data_copy * 0
            data_copy = data_copy * 0
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(temp_change_1hr), cmap="coolwarm", vmin=-10, vmax=10, extend='both')
        plot_title = f"1 Hour 2m Temp Change (°F) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Temperature Change (°F)'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
    elif product == 'dewp':
        data_copy = data_copy * 9/5 + 32
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='BrBG', levels=np.arange(10, 85, 5), extend='both')
        plot_title = f"2m Dewpoint (°F) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Dewpoint (°F)"
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
    elif product == '1hr_dewp_c':
        if partial_bool:
            print(f'-> skipping {product} {timestep} due to partial flag being enabled')
            return
        if timestep > 0:
            dewp_now = getvar(wrf_file, "td2", timeidx=timestep)
            dewp_prev = getvar(wrf_file, "td2", timeidx=timestep - 1)
            dewp_change_1hr = (dewp_now - dewp_prev) * 9/5
            data_copy = dewp_change_1hr.copy()
        else:
            ax.annotate("This product starts on hour 1.", xy=(0.5, 0.5), xycoords='figure fraction', fontsize=8, color='black', ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
            dewp_change_1hr = data_copy * 0
            data_copy = data_copy * 0
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(dewp_change_1hr), cmap="BrBG", vmin=-20, vmax=20, extend='both')
        plot_title = f"1 Hour 2m Dewpoint Change (°F) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Dewpoint Change (°F)'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
    elif product == 'rh':
        levels = np.arange(0, 100, 5)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='BrBG', levels=levels, extend="max")
        plot_title = f"2m Relative Humidity (%) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Relative Humidity (%)"
    elif product == 'wind':
        data_copy = data[0].copy()
        data_copy = data_copy * 2.23694
        divnorm = colors.TwoSlopeNorm(vmin=0, vcenter=30, vmax=90)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='YlOrRd', norm=divnorm)
        plot_title = f"10m Wind Speed (mph) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = "Wind Speed (mph)"
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
        plot_streamlines(ax, wrf_file, timestep, lons, lats)
    elif product == 'wind_gust':
        data_copy = data_copy * 2.23694
        divnorm = colors.TwoSlopeNorm(vmin=0, vcenter=50, vmax=110)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='YlOrRd', norm=divnorm)
        plot_title = f"10m Wind Gust (mph) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Wind Max (mph)"
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
        plot_streamlines(ax, wrf_file, timestep, lons, lats)
    elif product == 'comp_reflectivity':
        refl_cmap = ctables.registry.get_colortable('NWSReflectivity')
        data_masked = np.ma.masked_less(data_copy, 2)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_masked), cmap=refl_cmap, levels=np.arange(0, 75, 5), extend='max')
        plot_title = f"Composite Reflectivity (dbZ) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Composite Reflectivity (dbZ)"
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
    elif product == 'total_precip':
        data_copy = data_copy / 25.4
        precip_cmap = ctables.registry.get_colortable('precipitation')
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap=precip_cmap, levels=np.arange(0, 20, 0.25), extend='max')
        plot_title = f"Total Precipitation (in) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Precipitation (in)"
    elif product == 'afwarain':
        data_copy = data_copy / 25.4
        data_copy = np.ma.masked_where(data_copy <= 0.01, data_copy)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap=get_truncated_cmap('Greens', min_val=0.2), levels=np.arange(0, 10, 0.25), extend='max')
        plot_title = f"Total Rainfall (in) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Rainfall (in)"
    elif product == 'afwasnow':
        snow_ratio = 10.0
        data_copy = (data_copy / 25.4) * snow_ratio
        data_copy = np.ma.masked_where(data_copy <= 0.01, data_copy)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap=get_truncated_cmap('Blues', min_val=0.2), levels=np.arange(0, 15, 0.25), extend='max')
        plot_title = f"Total Snowfall (in) (10:1 ratio) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Snowfall (in)"
    elif product == 'afwasnow_k':
        temp = getvar(wrf_file, "tk", timeidx=timestep) - 273.15
        pressure = getvar(wrf_file, "pressure", timeidx=timestep)
        snow_ratio = kuchera_ratio(temp, pressure)
        data_copy = (data_copy / 25.4) * snow_ratio
        data_copy = np.ma.masked_where(data_copy <= 0.01, data_copy)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap=get_truncated_cmap('Blues', min_val=0.2), levels=np.arange(0, 15, 0.25), extend='max')
        plot_title = f"Total Snowfall (in) (Kuchera ratio) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        ax.annotate(
            f'Kuchera ratio is a work in progress and unfinished, with one big caveat:\n The Kuchera ratio for the *entire* total snowfall is recalculated at each step,\nmeaning values may not be fully indicative of actual snowfall.', xy=(0.01, 0.1), xycoords='axes fraction', fontsize=8, color='red', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
        label = f"Snowfall (in)"
    elif product == 'afwafrz':
        data_copy = data_copy / 25.4
        data_copy = np.ma.masked_where(data_copy <= 0.01, data_copy)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap=get_truncated_cmap('RdPu', min_val=0.2), levels=np.arange(0, 3, 0.1), extend='max')
        plot_title = f"Total Freezing Rain (in) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Freezing Rain (in)"
    elif product == 'afwaslt':
        data_copy = data_copy / 25.4
        data_copy = np.ma.masked_where(data_copy <= 0.01, data_copy)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap=get_truncated_cmap('Oranges', min_val=0.2), levels=np.arange(0, 3, 0.1), extend='max')
        plot_title = f"Total Ice Fall (in) (liquid equiv.) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Ice Fall (in)"
    elif product == '1hr_precip':
        if partial_bool:
            print(f'-> skipping {product} {timestep} due to partial flag being enabled')
            return
        rain_now = getvar(wrf_file, "AFWA_TOTPRECIP", timeidx=timestep)
        rain_prev = getvar(wrf_file, "AFWA_TOTPRECIP", timeidx=timestep - 1) if timestep > 0 else rain_now * 0
        precip_1hr = (rain_now - rain_prev) / 25.4
        data_copy = precip_1hr.copy()
        precip_cmap = ctables.registry.get_colortable('precipitation')
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(precip_1hr), cmap=precip_cmap, levels=np.arange(0, 5, 0.1), extend='max')
        plot_title = f"1 Hour Precipitation (in) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'1 Hour Rainfall (in)'
    elif product == 'snowfall':
        data_copy = data_copy / 25.4
        divnorm = colors.TwoSlopeNorm(vmin=0, vcenter=1, vmax=10)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='Blues', norm=divnorm, extend='max')
        plot_title = f"Total Accumulated Snowfall (in) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Accumulated Snowfall (in)"
    elif product == '1hr_snowfall':
        if partial_bool:
            print(f'-> skipping {product} {timestep} due to partial flag being enabled')
            return
        snow_now = getvar(wrf_file, "SNOWNC", timeidx=timestep)
        snow_prev = getvar(wrf_file, "SNOWNC", timeidx=timestep - 1) if timestep > 0 else snow_now * 0
        snow_1hr = (snow_now - snow_prev) / 25.4
        data_copy = snow_1hr.copy()
        divnorm = colors.TwoSlopeNorm(vmin=0, vcenter=0.3, vmax=3)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(snow_1hr), cmap='Blues', norm=divnorm, extend='max')
        plot_title = f"1 Hour Accumulated Snowfall (in) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Accumulated Snowfall'
    elif product == 'pressure':
        data_copy = data_copy / 100
        divnorm = colors.TwoSlopeNorm(vmin=970, vcenter=1013, vmax=1050)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='bwr_r', norm=divnorm, extend='both')
        smooth_slp = smooth2d(data_copy, 8, cenweight=6)
        ax.contour(to_np(lons), to_np(lats), to_np(smooth_slp), colors="black", transform=ccrs.PlateCarree(), levels=np.arange(960, 1060, 4))
        plot_title = f"MSLP (mb) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"MSLP (mb)"
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
    elif product == 'echo_tops':
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data), cmap='cividis_r', vmin=0, vmax=50000, extend='max')
        plot_title = f"Echo Tops (m) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"Echo Tops (m)"
    elif product == 'helicity':
        helicity_sum = 0
        for t in range(timestep + 1):  
            helicity = getvar(wrf_file, "UP_HELI_MAX", timeidx=t)
            helicity_sum += to_np(helicity)
        reflectivity = getvar(wrf_file, "REFD_COM", timeidx=timestep)
        reflectivity_masked = np.ma.masked_less(reflectivity, 2)
        refl_cmap = ctables.registry.get_colortable("NWSReflectivity")
        ax.contourf(to_np(lons), to_np(lats), to_np(reflectivity_masked), cmap=refl_cmap, levels=np.arange(0, 75, 5), alpha=0.3)
        contour = ax.contourf(to_np(lons), to_np(lats), helicity_sum, levels=[50, 100, 200, 300, 400, 500], colors=['green', 'cyan', 'blue', 'purple', 'red', 'black'], alpha=0.7)
        ax.contour(to_np(lons), to_np(lats), helicity_sum, levels=[50, 100, 200, 300, 400, 500], colors=['green', 'cyan', 'blue', 'purple', 'red', 'black'], linestyles='dashed')
        plot_title = f"Helicity Tracks (m^2/s^2) + Comp. Reflectivity (dbZ, transparent) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Helicity m^2/s^2'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats)
    elif product == 'cloudcover':
        low_cloud_frac = to_np(data_copy[0]) * 100 
        mid_cloud_frac = to_np(data_copy[1]) * 100
        high_cloud_frac = to_np(data_copy[2]) * 100
        total_cloud_frac = low_cloud_frac + mid_cloud_frac + high_cloud_frac
        data_copy = total_cloud_frac
        contour = ax.pcolormesh(to_np(lons), to_np(lats), total_cloud_frac, cmap="Blues_r", norm=plt.Normalize(0, 100), transform=ccrs.PlateCarree())
        plot_title = f"Cloud Cover - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Cloud Fraction (%)'
    elif product == 'mcape':
        data_copy = data[0].copy()
        label = f'CAPE (J/kg)'
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='magma_r', vmin=0, vmax=6000)
        plot_title = f"Max CAPE (MU 500m Parcel) (J/kg) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
    elif product == 'mcin':
        data_copy = data[1].copy()
        label = f'CIN (J/kg)'
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='magma_r', vmin=0, vmax=6000)
        plot_title = f"Max CIN (MU 500m Parcel) (J/kg) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
    elif product.startswith("temp") and level != None:
        cmax, cmin = None, None
        contour_freezing = False
        if level == 925:
            cmax, cmin = 40, -20
            contour_freezing = True
        elif level == 850:
            cmax, cmin = 40, -20
            contour_freezing = True
        elif level == 700:
            cmax, cmin = 30, -30
        elif level == 500:
            cmax, cmin = 20, -50
        elif level == 300:
            cmax, cmin = 0, -70
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='nipy_spectral', levels=np.arange(cmin, cmax, 2), extend='both')
        if contour_freezing:
            smooth_temp = smooth2d(data_copy, 4)
            ax.contour(to_np(lons), to_np(lats), to_np(smooth_temp), levels=[0], linestyles='dashed')
            plot_title = f"{level}mb Temp (°C) (0°C Dashed) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        else:
            plot_title = f"{level}mb Temp (°C) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Temp (°C)'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats, level)
    elif product.startswith("td") and level != None:
        cmax, cmin = None, None
        if level == 850:
            cmax, cmin = 30, -20
        elif level == 700:
            cmax, cmin = 10, -30
        elif level == 500:
            cmax, cmin = 0, -50
        elif level == 300:
            cmax, cmin = -30, -70
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='BrBG', levels=np.arange(cmin, cmax, 2), extend='both')
        plot_title = f"{level}mb Dew Point (°C) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Dew Point (°C)'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats, level)
    elif product.startswith("rh") and level != None:
        levels = np.arange(0, 100, 5)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='BrBG', levels=levels, extend='max')
        plot_title = f"{level}mb Relative Humidity (%) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Relative Humidity (%)'
    elif product.startswith("te") and level != None:
        if level == 925:
            levels = np.arange(270, 330, 2)
        elif level == 850:
            levels = np.arange(270, 330, 2)
        elif level == 700:
            levels = np.arange(290, 350, 2)
        else:
            levels = np.linspace(np.nanmin(data_copy), np.nanmax(data_copy), 20)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='turbo', levels=levels, extend='both')
        plot_title = f"{level}mb Theta E (K) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats, level)
        label = f'Theta E (K)'
    elif product.startswith("wind") and level != None:
        va = interplevel(getvar(wrf_file, "va", timeidx=timestep), pressure, level)
        ws = np.sqrt(to_np(data_copy)**2 + to_np(va)**2) * 1.944
        data_copy = ws
        cmax = None
        cmax = 135
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(ws), cmap="plasma", vmax=cmax)
        plot_title = f"{level}mb Wind Speed (kt) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Wind Speed (kt)'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats, level)
        plot_streamlines(ax, wrf_file, timestep, lons, lats, level)
    elif product.startswith("height") and level != None:
        cmax, cmin = None, None
        data_copy = data_copy / 10
        if level == 700:
            cmax, cmin = 350, 250
        elif level == 500:
            cmax, cmin = 600, 500
        smooth_z = smooth2d(data_copy, 40, cenweight=6)
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='coolwarm', vmax=cmax, vmin=cmin)
        ax.contour(to_np(lons), to_np(lats), to_np(smooth_z), colors="black", transform=ccrs.PlateCarree(), levels=np.arange(100, 1000, 5))
        plot_title = f"{level}mb Height (dam) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Height (dam)'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats, level)
    elif product.startswith('1hr_temp_c') and level != None:
        if partial_bool:
            print(f'-> skipping {product} {timestep} due to partial flag being enabled')
            return
        if timestep > 0:
            temp_now = getvar(wrf_file, "tc", timeidx=timestep)
            temp_prev = getvar(wrf_file, "tc", timeidx=timestep - 1)
            upper_temp_now = interplevel(temp_now, pressure, level)
            upper_temp_prev = interplevel(temp_prev, pressure, level)
            temp_change_1hr = (upper_temp_now - upper_temp_prev)
            data_copy = temp_change_1hr.copy()
        else:
            ax.annotate("This product starts on hour 1.", xy=(0.5, 0.5), xycoords='figure fraction', fontsize=8, color='black', ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
            temp_change_1hr = data_copy * 0
            data_copy = data_copy * 0
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(temp_change_1hr), cmap="coolwarm", vmin=-15, vmax=15)
        plot_title = f"1-Hour {level}mb Temp Change (°C) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Temperature Change (°C)'
        plot_wind_barbs(ax, wrf_file, timestep, lons, lats, level)
    elif product == 'stargazing':
        #wip
        low_clear_frac = 1.0 - to_np(data_copy[0])
        mid_clear_frac = 1.0 - to_np(data_copy[1])
        high_clear_frac = 1.0 - to_np(data_copy[2])
        total_cloud_frac = 1.0 - (low_clear_frac * mid_clear_frac * high_clear_frac)
        clear_sky_score = 1.0 - (total_cloud_frac)
        pwat = getvar(wrf_file, "AFWA_PWAT", timeidx=timestep)
        transparency_score = np.clip(1.0 - (to_np(pwat) / 30.0), 0.0, 1.0)
        u_300 = interplevel(getvar(wrf_file, "ua", timeidx=timestep), getvar(wrf_file, "pressure", timeidx=timestep), 300)
        v_300 = interplevel(getvar(wrf_file, "va", timeidx=timestep), getvar(wrf_file, "pressure", timeidx=timestep), 300)
        wind_speed_300 = np.sqrt(to_np(u_300)**2 + to_np(v_300)**2)
        seeing_score = np.clip(1.0 - (wind_speed_300 / 70.0), 0.0, 1.0)
        wind_10m = getvar(wrf_file, "wspd_wdir10", timeidx=timestep)[0]
        wind_10m_penalty = np.where(to_np(wind_10m) > 8.0, 0.7, 1.0)
        rh2 = getvar(wrf_file, "rh2", timeidx=timestep)
        rh2_penalty = np.where(to_np(rh2) > 85.0, 0.7, 1.0)
        index = (clear_sky_score * 75) + (transparency_score * 15) + (seeing_score * 10)
        index = np.clip(index * wind_10m_penalty * rh2_penalty, 0, 100)
        contour = ax.contourf(to_np(lons), to_np(lats), index, cmap="RdYlGn", levels=np.arange(0, 105, 5), extend='both')
        data_copy = index
        plot_title = f"Lobdell Stargazing Index (0-100) - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        ax.annotate(f'Index Explanation:\n75% Clear Sky\n15% Atmospheric Transparency\n10% Seeing Conditions\nPenalties for High Sfc. RH and Wind', xy=(0.01, 0.1), xycoords='axes fraction', fontsize=6, color='black', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
        label = f'Index (100=Clear/Dry)'
    elif product == 'ptype':
        if partial_bool:
            print(f'-> skipping {product} {timestep} due to partial flag being enabled')
            return
        if timestep > 0:
            rain = getvar(wrf_file, "AFWA_RAIN", timeidx=timestep) - getvar(wrf_file, "AFWA_RAIN", timeidx=timestep - 1)
            snow = getvar(wrf_file, "AFWA_SNOW", timeidx=timestep) - getvar(wrf_file, "AFWA_SNOW", timeidx=timestep - 1)
            ice  = getvar(wrf_file, "AFWA_ICE",  timeidx=timestep) - getvar(wrf_file, "AFWA_ICE",  timeidx=timestep - 1)
            fzra = getvar(wrf_file, "AFWA_FZRA", timeidx=timestep) - getvar(wrf_file, "AFWA_FZRA", timeidx=timestep - 1)
        else:
            rain = getvar(wrf_file, "AFWA_RAIN", timeidx=timestep)
            snow = getvar(wrf_file, "AFWA_SNOW", timeidx=timestep)
            ice  = getvar(wrf_file, "AFWA_ICE",  timeidx=timestep)
            fzra = getvar(wrf_file, "AFWA_FZRA", timeidx=timestep)
        precip_types = np.array([to_np(snow), to_np(ice), to_np(fzra), to_np(rain)])
        type_id = np.argmax(precip_types, axis=0)
        total_rate = np.sum(precip_types, axis=0)
        intensity = np.zeros(total_rate.shape, dtype=int)
        intensity[total_rate >= 2.5] = 1
        intensity[total_rate >= 7.6] = 2
        ptype_data = (type_id * 3) + intensity + 1  
        ptype_data[total_rate < 0.1] = 0
        data_copy = ptype_data.copy()
        cmap = colors.ListedColormap(['white', 'skyblue', 'deepskyblue', 'blue', 'peachpuff', 'orange', 'darkorange', 'lightpink', 'hotpink', 'deeppink', 'lightgreen', 'green', 'darkgreen'])
        bounds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        mesh = ax.pcolormesh(to_np(lons), to_np(lats), ptype_data, cmap=cmap, norm=norm, transform=ccrs.PlateCarree())
        plot_title = f"Potential Precipitation Type and Intensity - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f'Precipitation Type'
        cbar = fig.colorbar(mesh, ax=ax, location="right", fraction=0.035, pad=0.02, shrink=0.85, aspect=25, ticks=[0, 1, 2, 3, 4])
        cbar.ax.set_yticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5], labels=['None', '--', 'Snow', '+', '--', 'Ice', '+', '--', 'FzRa', '+', '--', 'Rain', '+'])
        ax.annotate(f'P-TYPE IS A WORK IN PROGRESS!\nIntensity Breakpoints (Liquid Eq.):\nHeavy - 7.6mm/hr\nModerate - 2.5mm/hr\nLight - <2.5mm/hr', xy=(0.01, 0.1), xycoords='axes fraction', fontsize=8, color='red', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
    else:
        contour = ax.contourf(to_np(lons), to_np(lats), to_np(data_copy), cmap='coolwarm')
        plot_title = f"Unconfigured product: {data.description} - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}"
        label = f"{data.description}"
    if product != ("ptype"):
        cbar = fig.colorbar(contour, ax=ax, location="right", fraction=0.035, pad=0.02, shrink=0.85, aspect=25)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False; gl.right_labels = False
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.STATES.with_scale('50m'))
    if product != ("cloudcover") and product != ("ptype"):
        try:
            west, east, north, south = extent
            for airport, (lat, lon) in airports.items():
                if not (west <= lon <= east and south <= lat <= north):
                    continue
                idx_x, idx_y = ll_to_xy(wrf_file, lat, lon)
                value = to_np(data_copy)[idx_y, idx_x]
                ax.text(lon, lat, f"{value:.1f}", color='black', fontsize=14, ha='center', va='bottom', bbox=dict(facecolor='white', alpha=0.2, edgecolor='none', boxstyle='round'))
        except:
            try:
                for airport, (lat, lon) in airports.items():
                    idx_x, idx_y = ll_to_xy(wrf_file, lat, lon)
                    value = to_np(data_copy)[idx_y, idx_x]
                    ax.text(lon, lat, f"{value:.1f}", color='black', fontsize=12, ha='center', va='bottom', bbox=dict(facecolor='white', alpha=0.2, edgecolor='none', boxstyle='round'))
            except:
                pass
    if product != ("cloudcover") and product != ("ptype"):
        maxmin = ""
        max_value = to_np(data_copy).max()
        min_value = to_np(data_copy).min()
        if max_value != 0:
            maxmin += f"Max: {max_value:.1f}"
            if min_value != 0:
                maxmin += f"\nMin: {min_value:.1f}"
        ax.annotate(maxmin, xy=(0.98, 0.03), xycoords='axes fraction', fontsize=12, color='black', ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
    ax.set_title(plot_title, fontweight='bold', loc='left')
    ax.annotate(f"UGA-WRF Run {run_time}", xy=(0.01, 0.01), xycoords='axes fraction', fontsize=8, color='black')
    os.makedirs(output_path, exist_ok=True)
    if loc is None:
        fig.savefig(os.path.join(output_path, f"hour_{f_hour}.png"), bbox_inches='tight', dpi=125)
    else:
        fig.savefig(os.path.join(output_path, f"hour_{f_hour}_{loc}.png"), bbox_inches='tight', dpi=125)
    plt.close(fig)
    print(f'-> {product} hr {f_hour} with {extent}')

def plot_wind_barbs(ax, wrf_file, timestep, lons, lats, pressure_level=None):
    if pressure_level:
        u = getvar(wrf_file, "ua", timeidx=timestep)
        v = getvar(wrf_file, "va", timeidx=timestep)
        pressure = getvar(wrf_file, "pressure", timeidx=timestep)
        u_interp = interplevel(u, pressure, pressure_level)
        v_interp = interplevel(v, pressure, pressure_level)
    else:
        u_interp = getvar(wrf_file, "U10", timeidx=timestep)
        v_interp = getvar(wrf_file, "V10", timeidx=timestep)
    stride = 40
    ax.barbs(to_np(lons[::stride, ::stride]), to_np(lats[::stride, ::stride]),
             to_np(u_interp[::stride, ::stride]), to_np(v_interp[::stride, ::stride]),
             length=6, color='black', pivot='middle',
             barb_increments={'half': 2.57222, 'full': 5.14444, 'flag': 25.7222})

def plot_streamlines(ax, wrf_file, timestep, lons, lats, pressure_level=None):
    if pressure_level:
        u = getvar(wrf_file, "ua", timeidx=timestep)
        v = getvar(wrf_file, "va", timeidx=timestep)
        pressure = getvar(wrf_file, "pressure", timeidx=timestep)
        u_interp = interplevel(u, pressure, pressure_level)
        v_interp = interplevel(v, pressure, pressure_level)
    else:
        u_interp = getvar(wrf_file, "U10", timeidx=timestep)
        v_interp = getvar(wrf_file, "V10", timeidx=timestep)
    ds = 4
    lon2 = to_np(lons)[::ds, ::ds]
    lat2 = to_np(lats)[::ds, ::ds]
    u2 = to_np(u_interp)[::ds, ::ds]
    v2 = to_np(v_interp)[::ds, ::ds]
    ax.streamplot(lon2, lat2, u2, v2, density=0.75, color='k', linewidth=1)

def kuchera_ratio(temp, pres):
    #thanks random website on the internet for giving me what i think is the kuchera ratio formula
    temp_below_500 = np.where(pres >= 500, temp, -999)
    t_max = np.nanmax(temp_below_500, axis=0)
    threshold = -1.99
    ratio = np.where(t_max > threshold, 12 + (2 * (threshold - t_max)), 12 + (threshold - t_max))
    return np.clip(ratio, 0, 30)

def get_truncated_cmap(cmap_name, min_val=0.2, max_val=1.0):
    cmap = plt.get_cmap(cmap_name)
    color = cmap(np.linspace(min_val, max_val, 256))
    return colors.LinearSegmentedColormap.from_list(f'trunc_{cmap_name}', color)
