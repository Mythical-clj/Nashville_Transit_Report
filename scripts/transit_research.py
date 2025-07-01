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

useful_traffic_data = full_traffic_df[full_traffic_df['H01_1'] >= 0]
traffic_2024 = useful_traffic_data[useful_traffic_data['ST_DATE'].str.contains('2024')]#[useful_traffic_data['DIR'].str.contains('1') | useful_traffic_data['DIR'].str.contains('2')]

traffic_2024 = traffic_2024.drop('AADT' , axis=1, inplace=False)
traffic_2024 = traffic_2024.drop_duplicates()

traffic_2024_gpd = gpd.GeoDataFrame(traffic_2024, geometry=gpd.points_from_xy(traffic_2024['LONGITUDE'], traffic_2024['LATITUDE']))
traffic_2024_gpd.crs = 'EPSG:4326'  # Set the coordinate reference system

num_columns = 96
start_column_index = 6
end_column_index = start_column_index + num_columns
# Use the actual column names for the 15-min interval data
heatmap_columns = list(traffic_2024_gpd.columns[start_column_index:end_column_index])

start_time = datetime.strptime("00:00:00", "%H:%M:%S")

fig, ax = plt.subplots(figsize=(14, 14))
time_text = ax.text(0.5, 1.02, '', transform=ax.transAxes, ha='center', va='bottom', fontsize=16)

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
    # Add time text
    current_time = (start_time + timedelta(minutes=15 * i)).time()
    time_str = current_time.strftime("%H:%M:%S")
    time_text = ax.text(0.5, 1.02, f"Time: {time_str}", transform=ax.transAxes, ha='center', va='bottom', fontsize=16)

    ax.set_axis_off()

ani = animation.FuncAnimation(fig, animate, frames=num_columns, repeat=False)

# --- 6. Save or Display the animation ---
# To save the animation to a file (e.g., GIF or MP4)
#ani.save('../images/animated_heatmap_2024.gif', writer='imagemagick', fps=4) 

plt.show() 

'''
This next section creates an animated heatmap of traffic patterns in Nashville for the year 2014.
'''

traffic_2014 = useful_traffic_data[useful_traffic_data['ST_DATE'].str.contains('2014')]

traffic_2014 = traffic_2014.drop('AADT' , axis=1, inplace=False)
traffic_2014 = traffic_2014.drop_duplicates()

traffic_2014_gpd = gpd.GeoDataFrame(traffic_2014, geometry=gpd.points_from_xy(traffic_2014['LONGITUDE'], traffic_2014['LATITUDE']))
traffic_2014_gpd.crs = 'EPSG:4326'  # Set the coordinate reference system

num_columns = 96
start_column_index = 6
end_column_index = start_column_index + num_columns
# Use the actual column names for the 15-min interval data
heatmap_columns = list(traffic_2024_gpd.columns[start_column_index:end_column_index])

start_time = datetime.strptime("00:00:00", "%H:%M:%S")

fig, ax = plt.subplots(figsize=(14, 14))
time_text = ax.text(0.5, 1.02, '', transform=ax.transAxes, ha='center', va='bottom', fontsize=16)

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
    traffic_2014_gpd.plot(
        column=current_column,
        ax=ax,
        legend=False,
        cmap='YlOrRd',
        vmin=10,
        vmax=1000
    )
    # Add time text
    current_time = (start_time + timedelta(minutes=15 * i)).time()
    time_str = current_time.strftime("%H:%M:%S")
    time_text = ax.text(0.5, 1.02, f"Time: {time_str}", transform=ax.transAxes, ha='center', va='bottom', fontsize=16)

    ax.set_axis_off()

ani = animation.FuncAnimation(fig, animate, frames=num_columns, repeat=False)

# --- 6. Save or Display the animation ---
# To save the animation to a file (e.g., GIF or MP4)
#ani.save('../images/animated_heatmap_2014.gif', writer='imagemagick', fps=4) 

plt.show()

# repeat graph for multiple bus routes based on trip_id
stops_df_gdf = gpd.GeoDataFrame(bus_stops_df, geometry=gpd.points_from_xy(bus_stops_df['stop_lon'], bus_stops_df['stop_lat']))
stops_df_gdf.crs = 'EPSG:4326'

if not stops_df_gdf.empty:
    #trip_id = stops_df_gdf['trip_id'] # Or pick a specific trip_id
    trip_stops = stops_df_gdf[stops_df_gdf['trip_id'] == 352985].sort_values('stop_sequence')

    # Extract coordinates
    x = trip_stops.geometry.x.values
    y = trip_stops.geometry.y.values

    num_frames = min(len(x), len(y))

    print(f"num_frames: {num_frames}, x shape: {x.shape}, y shape: {y.shape}")

    if num_frames == 0:
        print("No stops found for the selected trip_id.")
    else:
        fig, ax = plt.subplots(figsize=(10, 8))

        streets_gdf.plot(ax=ax, edgecolor='black', linewidth=0.2, zorder=0, label='Street Centerlines')
        ax.plot(x, y, 'o-', color='blue', markersize=1, label='Stop Sequence Path', zorder=1)

        point, = ax.plot([], [], 'ro', markersize=6, label='Bus Location', zorder=2)

        ax.set_title(f'Animated Bus Along Stop Sequence (trip_id={trip_id})')
        ax.set_axis_off()
        plt.legend()

        def animate(i):
            point.set_data([x[i]], [y[i]])  # Wrap in list to make it a sequence
            return [point]


        if num_frames > 0:
            ani = animation.FuncAnimation(
                fig, animate, frames=range(num_frames), interval=600, repeat=False
            )

        
#ani.save('../images/bus_animation_3.gif', writer='pillow', fps=4)
plt.show()

'''
Calculate the average trip duration for all the trip ids in the bus stops data.
tweak code to look at min and max as well as median.
'''

trip_avg_df = stops_df_gdf.copy()
trip_avg_df['departure_time_parsed'] = trip_avg_df['departure_time'].apply(lambda x: pd.to_datetime(x, format='%H:%M:%S', errors='coerce'))

first_last = (
    trip_avg_df.sort_values(['trip_id', 'stop_sequence'])
      .groupby('trip_id')
      .agg(
          first_stop_sequence=('stop_sequence', 'first'),
          last_stop_sequence=('stop_sequence', 'last'),
          first_departure=('departure_time_parsed', 'first'),
          last_departure=('departure_time_parsed', 'last')
      )
)

first_last['duration_min'] = (first_last['last_departure'] - first_last['first_departure']).dt.total_seconds() / 60

average_duration = first_last['duration_min'].mean()
print(f"Average trip duration (min): {average_duration:.2f}")

median_duration = first_last['duration_min'].median()
print(f"Median trip duration (min): {median_duration:.2f}")

max_duration = first_last['duration_min'].max()
print(f"Max trip duration (min): {max_duration:.2f}")

min_duration = first_last['duration_min'].min()
print(f"Min trip duration (min): {min_duration:.2f}")

'''
Setting up graph to show intersections of each Pike in Nashville with street centerlines.
'''

pike_data = full_traffic_df[full_traffic_df['AT_ROAD'].str.contains('PIKE' or 'PK', na=False)]

pike_data_gdf = gpd.GeoDataFrame(pike_data, geometry=gpd.points_from_xy(pike_data['LONGITUDE'], pike_data['LATITUDE']))
pike_data_gdf.crs = 'EPSG:4326'

streets_gdf = gpd.GeoDataFrame(streets_gdf, geometry=streets_gdf.geometry.to_crs(epsg=4326))

# Plot street centerlines and highlight intersections with Pike data

fig, ax = plt.subplots(figsize=(10, 8))

# Plot all streets
streets_gdf.plot(ax=ax, edgecolor='black', linewidth=0.2, zorder=0, label='Street Centerlines')

# Plot Pike data points
pike_data_gdf.plot(ax=ax, color='green', markersize=8, zorder=1, label='Pike Data Points')

# Find intersections: buffer Pike points slightly and spatial join with streets
pike_buffer = pike_data_gdf.copy()
pike_buffer = pike_buffer.to_crs(epsg=4326)
intersections = gpd.sjoin(streets_gdf, pike_buffer, how='inner', predicate='intersects')

# Plot intersections
intersections.plot(ax=ax, color='red', linewidth=2, zorder=2, label='Intersections')

ax.set_title('Street Centerlines and Pike Data Intersections')
ax.set_axis_off()
plt.legend()
plt.show()