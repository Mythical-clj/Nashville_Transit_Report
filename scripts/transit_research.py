"""
This script is designed to analyze and visualize transit data. It includes graphs, tables, and statistical analyses to understand transit patterns and performance. It includes bus routes and stops, as well as possible train routes based on the provided data. It also includes traffic patterns on all streets in Nashville. 
"""
# import necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import plotly.express as px
import os
import matplotlib.ticker as ticker
from matplotlib import animation

# change directory to the directory where the script is located
os.chdir('c:/users/cavin/Documents/NSS_Projects/Capstone/Nashville_Transit_Report/scripts')

print(f'Current working directory is {os.getcwd()}')

# Load the transit data
full_traffic_df = pd.read_csv('../data/full_traffic_data.csv')
# Load traffic 2024 data only
traffic_2024_df = pd.read_csv('../data/traffic_2024.csv')
# Load the bus routes and stops data
bus_stops_df = pd.read_csv('../data/stops_df.csv')
# Load the bus transit centers data
transit_centers_df = pd.read_csv('../data/transit_centers.csv')
# Load AADT total data
all_years_aadt_total = pd.read_csv('../data/aadt_SUM_all_years.csv')

# Load in street centerlines data
street_centerlines = gpd.read_file('../data/Street_Centerlines_view.gpkg')
street_centerlines = street_centerlines['geometry'].to_crs(epsg=4326)

# Load in raliroads data
railroads = gpd.read_file('../data/railroad.gpkg')
railroads = railroads['geometry'].to_crs(epsg=4326) 

# Create a GeoDataFrame for the transit centers
transit_centers_gdf = gpd.GeoDataFrame(transit_centers_df, geometry=gpd.points_from_xy(transit_centers_df['Long'], transit_centers_df['Lat']))
transit_centers_gdf.crs = 'EPSG:4326'

# Create a GeoDataFrame for the bus stops
bus_stops_gdf = gpd.GeoDataFrame(bus_stops_df, geometry=gpd.points_from_xy(bus_stops_df['stop_lon'], bus_stops_df['stop_lat']))
bus_stops_gdf.crs = 'EPSG:4326'

'''
Plot showing the sum of the annual average daily total of cars entering and exiting the highways of Nashville between 1991 and 2024.
This bar graph shows the change in the number of cars over the years, indicating trends in traffic volume. The total is in millions.
'''
plt.figure(figsize=(10, 6))
plt.bar(all_years_aadt_total['AADT_YEAR'], all_years_aadt_total['sum'], edgecolor='black', facecolor='grey', alpha=0.7)

plt.xlabel('Years recorded (1991-2024)')
plt.ylabel('Total annual average daily total of cars')
plt.xticks(rotation=45)
plt.title('Total number of cars entering and exiting highways in Nashville (1991-2024)')

def y_format(x, pos):
    return f"{int(x):,}"

plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(y_format))

plt.tight_layout()

# plt.savefig('../images/aadt_total_cars_nashville.png', dpi=600)
plt.show()


# Create a buffer (e.g., 500 meters) around the first transit center
buffer = transit_centers_gdf.geometry.iloc[2].buffer(0.260)  # ~0.005 degrees is roughly 500m, adjust as needed

# Filter stops within the buffer
gdf_within_boundary = bus_stops_gdf[bus_stops_gdf.geometry.within(buffer)]

# Filter stops that intersect the buffer
gdf_intersecting_boundary = bus_stops_gdf[bus_stops_gdf.geometry.intersects(buffer)]

# Clip stops to the buffer (returns only the part of geometry within the buffer, but for points it's just a filter)
bus_stops_gdf_clipped = bus_stops_gdf[bus_stops_gdf.geometry.within(buffer)]

# Create a buffer (e.g., 500 meters) around the first transit center
rail_road_buffer = transit_centers_gdf.geometry.iloc[2].buffer(0.310)  # ~0.005 degrees is roughly 500m, adjust as needed

# Filter stops within the buffer
railroad_within_boundary = railroads[railroads.geometry.within(rail_road_buffer)]

# Filter stops that intersect the buffer
railroad_intersecting_boundary = railroads[railroads.geometry.intersects(rail_road_buffer)]

# Clip stops to the buffer (returns only the part of geometry within the buffer, but for points it's just a filter)
railroad_gdf_clipped = railroads[railroads.geometry.within(rail_road_buffer)]

# Plotting the transit centers, stops, and street centerlines
fig, ax = plt.subplots(figsize=(14, 14))

base = transit_centers_gdf.plot(ax=ax, color='red', markersize=30, zorder=2,label='Transit Centers')

street_centerlines.plot(ax=base, edgecolor='black', zorder=0, linewidth=0.2, label='Street Centerlines')

bus_stops_gdf_clipped.plot(ax=base, color='blue', markersize=1, zorder=1, label='Transit Stops')

railroad_gdf_clipped.plot(ax=base, edgecolor='green', zorder=0, linewidth=1.5, label='Railroads')

ax.set_title('Transit Centers and Stops in Nashville', fontsize=16)
ax.set_axis_off()
ax.set_facecolor('none')
fig.patch.set_facecolor('none')
plt.legend()
plt.show()
# plt.savefig('../images/transit_centers_and_stops_nashville.png', bbox_inches='tight', dpi=600)

'''
This next section creates an animated heatmap of traffic patterns in Nashville for the year 2024.
'''

useful_traffic_data = full_traffic_data[full_traffic_data['H01_1'] >= 0]
traffic_2024 = useful_traffic_data[useful_traffic_data['ST_DATE'].str.contains('2024')]#[useful_traffic_data['DIR'].str.contains('1') | useful_traffic_data['DIR'].str.contains('2')]

traffic_2024 = traffic_2024.drop('AADT' , axis=1, inplace=False)
traffic_2024 = traffic_2024.drop_duplicates()

traffic_2024_gpd = gpd.GeoDataFrame(traffic_2024, geometry=gpd.points_from_xy(traffic_2024['LONGITUDE'], traffic_2024['LATITUDE']))
traffic_2024_gpd.crs = 'EPSG:4326'  # Set the coordinate reference system

num_columns = 96
start_column_index = 6
end_column_index = start_column_index + num_columns
heatmap_columns = list(traffic_2024_gpd.columns[start_column_index:end_column_index])

fig, ax = plt.subplots(figsize=(14, 14))

# --- 4. Define the animation function ---
def animate(i):
    ax.cla()  # Clear the previous frame

    # Plot base layers first
    streets_gdf.plot(
        ax=ax, 
        edgecolor='black', 
        linewidth=0.2, 
        label='Street Centerlines'
    )

    # Select the current column for the heatmap
    current_column = heatmap_columns[i]

    # Create the heatmap based on the current column's values
    traffic_2024_gpd.plot(
        column=current_column,
        ax=ax,
        legend=False,
        cmap='YlOrRd',
        vmin=10,
        vmax=1000
    )

    # Add a title to indicate the time interval or column index
    ax.set_title(f'15 min interval: {i+1}')

    # Customize plot appearance
    ax.set_axis_off()

ani = animation.FuncAnimation(fig, animate, frames=num_columns, repeat=False) # 
#ani.save('../images/animated_heatmap.gif', writer='imagemagick', fps=4)
plt.show() 

