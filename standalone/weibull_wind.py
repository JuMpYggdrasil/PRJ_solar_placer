import numpy as np
import pandas as pd
from scipy.stats import weibull_min
import matplotlib.pyplot as plt


def run_weibull_analysis(filepath="sattahip_wind.csv"):
    df = pd.read_csv(filepath)
    windspeed_data = df["windspeed"].dropna()
    params = weibull_min.fit(windspeed_data)
    c, k = params[1], params[2]

    hist_values, bins, _ = plt.hist(windspeed_data, bins=30, density=True, alpha=0.6, color="g")
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = weibull_min.pdf(x, *params)
    plt.plot(x, p, "k", linewidth=2)
    plt.title("Fitted Weibull Distribution to Windspeed Data")
    plt.xlabel("Windspeed")
    plt.ylabel("Probability Density")
    plt.show()

    bin_width = bins[1] - bins[0]
    hist_percentage = hist_values[:20] / np.sum(hist_values[:20]) * 100
    print("Histogram Values (in percentage):", hist_percentage)
    print("Sum of Histogram Values:", np.sum(hist_percentage))
    print("Weibull Scaling Factor (c):", c)
    print("Weibull Form Factor (k):", k)


if __name__ == "__main__":
    run_weibull_analysis()
