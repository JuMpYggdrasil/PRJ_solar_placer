import numpy as np
import pandas as pd
from scipy.stats import weibull_min
import matplotlib.pyplot as plt

# Load the CSV file into a DataFrame
file_path = 'sattahip_wind.csv'  # Replace with the actual path to your CSV file
df = pd.read_csv(file_path)

# Extract the 'windspeed' column from the DataFrame
windspeed_data = df['windspeed'].dropna()

# Fit the data to a Weibull distribution
params = weibull_min.fit(windspeed_data)

# Extract the scaling factor (c) and form factor (k) from the fitted parameters
c, k = params[1], params[2]

# Plot the histogram and fitted distribution
hist_values, bins, _ = plt.hist(windspeed_data, bins=30, density=True, alpha=0.6, color='g')
xmin, xmax = plt.xlim()
x = np.linspace(xmin, xmax, 100)
p = weibull_min.pdf(x, *params)
plt.plot(x, p, 'k', linewidth=2)
plt.title('Fitted Weibull Distribution to Windspeed Data')
plt.xlabel('Windspeed')
plt.ylabel('Probability Density')
plt.show()

# Calculate and print histogram values in percentage
bin_width = bins[1] - bins[0]
hist_percentage = hist_values[:20] /np.sum(hist_values[:20])* 100
print("Histogram Values (in percentage):", hist_percentage)

# Calculate and print the sum of histogram values
sum_hist_percentage = np.sum(hist_percentage)
print("Sum of Histogram Values:", sum_hist_percentage)

# Print the Weibull scaling factor and form factor
print("Weibull Scaling Factor (c):", c)
print("Weibull Form Factor (k):", k)

#  To find A,k optional use
# https://wind-data.ch/tools/weibull.php
