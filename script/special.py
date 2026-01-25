# This module is intended for special operations that require one-time code - such as 4-panel cloud cover.

from wrf import getvar, to_np, latlon_coords, ll_to_xy
from weathermaps import get_truncated_cmap, kuchera_ratio
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from metpy.plots import USCOUNTIES

def hr24_change(output_path, airports, hours, forecast_times, run_time, init_dt, init_str, wrf_file, partial=False):
    if partial:
        print("The partial flag is on. 24 hour temp change is skipped.")
        pass
    else:
        temp_24 = getvar(wrf_file, "T2", timeidx=hours)
        temp_now = getvar(wrf_file, "T2", timeidx=0)
        hr24_change = (temp_24 - temp_now) * 9/5
        plt.figure(figsize=(12, 10))
        ax = plt.axes(projection=ccrs.PlateCarree())
        lats, lons = latlon_coords(hr24_change)
        contour = plt.contourf(to_np(lons), to_np(lats), to_np(hr24_change), cmap="coolwarm", vmin=-35, vmax=35)
        try:
            for airport, coords in airports.items():
                    lat, lon = coords
                    idx_x, idx_y = ll_to_xy(wrf_file, lat, lon)
                    value = to_np(hr24_change)[idx_y, idx_x]
                    ax.text(lon, lat, f"{value:.1f}", color='black', fontsize=14, ha='center', va='bottom', bbox=dict(facecolor='white', alpha=0.2, edgecolor='none', boxstyle='round'))
        except:
            pass
        maxmin = ""
        max_value = to_np(hr24_change).max()
        min_value = to_np(hr24_change).min()
        if max_value != 0:
            maxmin += f"Max: {max_value:.1f}"
            if min_value != 0:
                maxmin += f"\nMin: {min_value:.1f}"
        ax.annotate(maxmin, xy=(0.98, 0.03), xycoords='axes fraction', fontsize=12, color='black', ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
        valid_time = forecast_times[hours]
        ax.set_title(f"Full Model/{hours} Hour 2m Temp Change (°F)\nValid: {valid_time}\nInit: {init_str}", fontweight='bold', fontsize=14, loc='left')
        plt.colorbar(contour, ax=ax, orientation='vertical', fraction=0.035, pad=0.02, shrink=0.85, aspect=25)
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.add_feature(cfeature.STATES.with_scale('50m'))
        ax.add_feature(USCOUNTIES.with_scale('20m'), alpha=0.2)
        plt.tight_layout()
        ax.annotate(f"UGA-WRF Run {run_time}", xy=(0.01, 0.02), xycoords='axes fraction', fontsize=8, color='black')
        os.makedirs(output_path, exist_ok=True)
        plt.savefig(os.path.join(output_path, f"24hr_change.png"))
        plt.close()

def generate_cloud_cover(t, output_path, forecast_times, run_time, init_dt, init_str, wrf_file):
    valid_time = forecast_times[t]
    f_hour = int(round((valid_time - init_dt).total_seconds() / 3600))
    valid_time_str = valid_time.strftime("%Y-%m-%d %H:%M UTC")
    cloud_fracs = getvar(wrf_file, "cloudfrac", timeidx=t)
    low_cloud_frac = to_np(cloud_fracs[0]) * 100 
    mid_cloud_frac = to_np(cloud_fracs[1]) * 100
    high_cloud_frac = to_np(cloud_fracs[2]) * 100
    total_cloud_frac = low_cloud_frac + mid_cloud_frac + high_cloud_frac
    lats, lons = latlon_coords(cloud_fracs)
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
    cloud_data = [total_cloud_frac, low_cloud_frac, mid_cloud_frac, high_cloud_frac]
    titles = ["Total Cloud Cover (%)", "Low (%)", "Mid (%)", "High (%)"]
    for ax, data, title in zip(axes.flat, cloud_data, titles):
        ax.set_title(title)
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.add_feature(cfeature.STATES, linewidth=0.5)
        cf = ax.pcolormesh(to_np(lons), to_np(lats), data, cmap="Blues_r", norm=plt.Normalize(0, 100), transform=ccrs.PlateCarree())
    cbar = plt.colorbar(cf, ax=axes[:,:], orientation='vertical', fraction=0.035, pad=0.02, shrink=0.85, aspect=25)
    plt.suptitle(f"Cloud Cover - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}", fontweight='bold', fontsize=14)
    plt.annotate(f"UGA-WRF Run {run_time}", xy=(0.01, 0.01), xycoords='figure fraction', fontsize=8, color='black')
    os.makedirs(output_path, exist_ok=True)
    plt.savefig(os.path.join(output_path, f"hour_{f_hour}.png"))
    plt.close(fig)

def plot_4panel_ptype(t, output_path, forecast_times, run_time, init_dt, init_str, wrf_file):
    valid_time = forecast_times[t]
    f_hour = int(round((valid_time - init_dt).total_seconds() / 3600))
    valid_time_str = valid_time.strftime("%Y-%m-%d %H:%M UTC")
    temp = getvar(wrf_file, "tk", timeidx=t) - 273.15
    pressure = getvar(wrf_file, "pressure", timeidx=t)
    snow = (getvar(wrf_file, "AFWA_SNOW", timeidx=t) / 25.4) * kuchera_ratio(temp, pressure)
    rain = getvar(wrf_file, "AFWA_RAIN", timeidx=t) / 25.4
    fzra = getvar(wrf_file, "AFWA_FZRA", timeidx=t) / 25.4
    ice = getvar(wrf_file, "AFWA_ICE", timeidx=t) / 25.4
    lats, lons = latlon_coords(snow)
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
    ptype_data = [to_np(rain), to_np(snow), to_np(fzra), to_np(ice)]
    titles = ["Rain Total (in)", "Snowfall Total (in, Kuchera)", "Freezing Rain Total (in)", "Ice Fall Total (in, liquid equiv.)"]
    cmaps = ['Greens', 'Blues', 'RdPu', 'Oranges']
    levels_list = [np.arange(0, 5.5, 0.25), np.arange(0, 15.25, 0.25), np.arange(0, 3.1, 0.1), np.arange(0, 3.1, 0.1)]
    for ax, data, title, cmap, levels in zip(axes.flat, ptype_data, titles, cmaps, levels_list):
        ax.set_title(title)
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.add_feature(cfeature.STATES, linewidth=0.5)
        ax.add_feature(USCOUNTIES.with_scale('20m'), alpha=0.05)
        data = np.ma.masked_where(data <= 0.01, data)
        cf = ax.contourf(to_np(lons), to_np(lats), data, cmap=get_truncated_cmap(cmap, min_val=0.2), levels=levels, extend='max', transform=ccrs.PlateCarree())
        cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
        max = to_np(data).max()
        if max != 0:
            ax.annotate(f"Max: {max:.1f}", xy=(0.98, 0.03), xycoords='axes fraction', fontsize=8, color='black', ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))
    plt.suptitle(f"Precipitation Types - Hour {f_hour}\nValid: {valid_time_str}\nInit: {init_str}", fontweight='bold', fontsize=14)
    plt.tight_layout()
    plt.annotate(f"UGA-WRF Run {run_time}", xy=(0.01, 0.01), xycoords='figure fraction', fontsize=8, color='black')
    os.makedirs(output_path, exist_ok=True)
    plt.savefig(os.path.join(output_path, f"hour_{f_hour}.png"))
    plt.close(fig)
