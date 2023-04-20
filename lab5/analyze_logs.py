

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_CSV_FILEPATH = "logs_output.csv"
VISUALS_DIR = "./visualizations/"

# Define a function to calculate the Euclidean distance
def calc_euclid_dist(x1: float, y1: float, x2: float, y2: float) -> float:
        distance = ((x1 - x2)**2 + (y1 - y2)**2)**0.5

        return distance

if __name__ == "__main__":
    
    df_logs = pd.read_csv(INPUT_CSV_FILEPATH, index_col=0)

    # Select only the zebras
    zebra_mask = df_logs["animal_id"].str.contains("Zebra")
    df_logs = df_logs[zebra_mask]

    # Group the data by animal_id
    groups = df_logs.groupby("animal_id")

    # Initialize an empty DataFrame to store combined data
    combined_df = pd.DataFrame()


    ##########################################################################################################################################################################
    # CDF plot
    ##########################################################################################################################################################################
    for name, group in groups:

        # Sort by timestamp
        group = group.sort_values("timestamp", ascending=True)

        # Time difference between consecutive rows now the data are sorted
        group["time_diff_sec"] = group["timestamp"].diff()
        group["latitude_shift"] = group["latitude"].shift(1)
        group["longitude_shift"] = group["longitude"].shift(1)
        group["distance_m"] = group.apply(lambda row: calc_euclid_dist(row["latitude"], row["longitude"],
                                                row["latitude_shift"], row["longitude_shift"]), axis=1)
        group["speed"] = group["distance_m"]/group["time_diff_sec"]
        group["speed"] = group["speed"].fillna(0)

        # Append group data to combined_df
        combined_df = pd.concat([combined_df, group], ignore_index=True)


    # Calculate the PDF (histogram) of the speed Series with 100 bins
    pdf, bin_edges = np.histogram(combined_df["speed"], bins=100, density=True)

    # Calculate the CDF by cumulatively summing the PDF values
    cdf = np.cumsum(pdf * np.diff(bin_edges))

    # Plot the CDF of speeds
    plt.plot(bin_edges[1:], cdf)

    plt.xlabel("Speed")
    plt.ylabel("Cumulative Probability")
    plt.title("Speed CDFs For Zebras")
    plt.savefig(f"{VISUALS_DIR}zebra_speed_cdf.png")
    plt.close()

    ##########################################################################################################################################################################
    # Location plot
    ##########################################################################################################################################################################

    # Create a new figure and 3D axes
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Plot the longitude, latitude, and timestamp coordinates for each animal_id
    for name, group in groups:
        ax.scatter(group["longitude"], group["latitude"], group["timestamp"], label=name)

    # Add axis labels and a legend
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_zlabel("Timestamp")
    ax.legend()

    # Save the plot
    plt.savefig(f"{VISUALS_DIR}zebra_coordinates.png")
    plt.close()

    ##########################################################################################################################################################################
    # Speed vs Heart Rate
    ##########################################################################################################################################################################

    fig, ax = plt.subplots()
    for name, group in groups:
        # Time difference between consecutive rows now the data are sorted
        group["time_diff_sec"] = group["timestamp"].diff()
        group["latitude_shift"] = group["latitude"].shift(1)
        group["longitude_shift"] = group["longitude"].shift(1)
        group["distance_m"] = group.apply(lambda row: calc_euclid_dist(row["latitude"], row["longitude"],
                                                row["latitude_shift"], row["longitude_shift"]), axis=1)
        group["speed"] = group["distance_m"]/group["time_diff_sec"]
        group["speed"] = group["speed"].fillna(0)
        
        ax.scatter(group["speed"], group["heart_rate"], label=name)
        
    ax.set_xlabel("Speed")
    ax.set_ylabel("Heart Rate")
    ax.legend(title="Animal Name")
    # Save the plot
    plt.savefig(f"{VISUALS_DIR}zebra_speed_heartrate.png")
    plt.close()

    ##########################################################################################################################################################################
    # Location vs Temp
    ##########################################################################################################################################################################

    fig, ax = plt.subplots()

    # Plot the data using the temperature as a color map
    scatter = ax.scatter(df_logs["longitude"], df_logs["latitude"], c=df_logs["temperature"], cmap="coolwarm", alpha=0.7)

    # Add a color bar to show the temperature scale
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Temperature")

    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    plt.title("Temperature Distribution by Location")
    # Save the plot
    plt.savefig(f"{VISUALS_DIR}zebra_temp_location.png")
    plt.close()