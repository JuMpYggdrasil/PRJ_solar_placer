import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pvlib.solarposition import get_solarposition

def plot_solar_analemma(lat, lon, start_date, end_date, timezone='Asia/Bangkok'):
    times = pd.date_range(start_date, end_date, freq='H', tz=timezone)
    solpos = get_solarposition(times, lat, lon)
    solpos = solpos.loc[solpos['apparent_elevation'] > 0, :]

    ax = plt.subplot(1, 1, 1, projection='polar')

    # draw the analemma loops
    points = ax.scatter(np.radians(solpos.azimuth), solpos.apparent_zenith,
                        s=2, label=None, c=solpos.index.dayofyear)
    ax.figure.colorbar(points)

    # draw hour labels
    for hour in np.unique(solpos.index.hour):
        subset = solpos.loc[solpos.index.hour == hour, :]
        r = subset.apparent_zenith
        pos = solpos.loc[r.idxmin(), :]
        ax.text(np.radians(pos['azimuth']), pos['apparent_zenith'], str(hour))

    # draw individual days
    date_range = pd.date_range(start_date, end_date, freq='3MS') + pd.DateOffset(months=2) # Monthly intervals
    for date in date_range:
        times = pd.date_range(date, date + pd.Timedelta('24h'), freq='5min', tz=timezone)
        solpos = get_solarposition(times, lat, lon)
        solpos = solpos.loc[solpos['apparent_elevation'] > 0, :]
        label = date.strftime('%Y-%m-%d')
        ax.plot(np.radians(solpos.azimuth), solpos.apparent_zenith, label=label)

    ax.figure.legend(loc='upper left')

    # change coordinates to be like a compass
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_rmax(90)

    plt.show()

# Example usage
if __name__ == "__main__":
    plot_solar_analemma(lat=13.765733827940576, lon=100.50257304756634,
                        start_date='2019-01-01 00:00:00', end_date='2020-01-01', timezone='Asia/Bangkok')
