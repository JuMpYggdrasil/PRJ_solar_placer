import numpy as np
import pandas as pd
from scipy.stats import weibull_min
from tabulate import tabulate
import matplotlib.pyplot as plt

# Load the CSV file into a DataFrame
file_path = 'sattahip_wind.csv'  # Replace with the actual path to your CSV file
df = pd.read_csv(file_path)

# Extract the 'windspeed' column from the DataFrame
windspeed_data = df['windspeed'].dropna()

# Fit the data to a Weibull distribution
params = weibull_min.fit(windspeed_data)

# Print the fitted Weibull distribution parameters in a table
table = tabulate([['Shape (k)', 'Scale (λ)'], params], headers='firstrow', tablefmt='pretty')
print(table)

# Plot the histogram and fitted distribution
plt.hist(windspeed_data, bins=30, density=True, alpha=0.6, color='g')
xmin, xmax = plt.xlim()
x = np.linspace(xmin, xmax, 100)
p = weibull_min.pdf(x, *params)
plt.plot(x, p, 'k', linewidth=2)
plt.title('Fitted Weibull Distribution to Windspeed Data')
plt.xlabel('Windspeed')
plt.ylabel('Probability Density')
plt.show()
