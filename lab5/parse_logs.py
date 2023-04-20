

import re
import json
import pandas as pd
from typing import Union

LOG_FILEPATH = "simulation_2023_4_16_22_45_24_READABLE.txt"
OUTPUT_JSON_FILEPATH = "logs_output.json"
OUTPUT_CSV_FILEPATH = "logs_output.csv"


if __name__ == "__main__":
    
    with open(LOG_FILEPATH,"r") as f:
        log_data = f.readlines()

    log_data = "".join(log_data)

    output_data_list = []

    for match in re.finditer(r'={15}\s+([A-Za-z]+):([0-9a-fA-F]+)\s+LOG\s+={15}(.+?)(?=(={15}\s+[A-Za-z]+:[0-9a-fA-F]+\s+LOG\s+={15}|$))', log_data, re.DOTALL):
        animal = match.group(1)
        animal_id = match.group(2)
        log_entries_text = match.group(3).strip()
        
        log_entries = []
        
        for entry_match in re.finditer(r'-- Timestamp: (\d+\.\d+)\s+(.+?)(?=(-- Timestamp: \d+\.\d+|$))', log_entries_text, re.DOTALL):
            timestamp = float(entry_match.group(1))
            entry_text = entry_match.group(2).strip()
            
            entry = {}
            
            for line_match in re.finditer(r'"(.+?)":\s+([\d\.\-\[\],]+)', entry_text):
                key = line_match.group(1)
                value = line_match.group(2)
                if '[' in value:
                    value = list(map(float, re.findall(r'[-\d.]+', value)))
                else:
                    value = float(value.replace(",","").strip())
                entry[key] = value
            
            log_entries.append({"timestamp": timestamp, "sensor_data": entry})
        
        data = {"animal": animal, "animal_id": f"{str(animal)}:{str(animal_id)}", "log_entries": log_entries}
        output_data_list.append(data)
    
    # Save json list to file
    with open(OUTPUT_JSON_FILEPATH,"w") as f:
        json.dump(output_data_list, f, indent=4)
    
    # Create a CSV output via a Pandas dataframe for easier analysis later

    # Normalize the log_entries data into a flat table
    df = pd.json_normalize(output_data_list, record_path="log_entries", meta=["animal", "animal_id"], record_prefix="", errors="ignore")
    
    # Split the location column into two separate columns
    df[["latitude", "longitude"]] = pd.DataFrame(df["sensor_data.location"].tolist(), index=df.index)

    # Drop the original location column and the sensor_data_ prefix from the remaining columns
    df.drop(["sensor_data.location"], axis=1, inplace=True)
    df.columns = [col.replace("sensor_data.", "") for col in df.columns]

    # Reorder the columns as desired
    df = df[["animal", "animal_id", "timestamp", "latitude", "longitude", "humidity", "temperature", "oxygen_saturation", "heart_rate"]]

    df.to_csv(OUTPUT_CSV_FILEPATH)

