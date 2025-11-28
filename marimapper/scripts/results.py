import glob
import csv
import sys
import os

def log(msg):
    sys.stderr.write(msg + "\n")

def load_3d_map(filename):
    data = {}
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[int(row['index'])] = row
    return data

def scan_2d_indices():
    files = glob.glob("./led_map_2d_*.csv")
    detection_log = {} 
    
    for fname in files:
        with open(fname, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'index' in row:
                    idx = int(row['index'])
                    if idx not in detection_log:
                        detection_log[idx] = []
                    detection_log[idx].append(os.path.basename(fname))
                
    return detection_log, files

def main():
    map_file = "led_map_3d.csv"
    
    map_data = load_3d_map(map_file)
    data_2d_log, files_2d = scan_2d_indices()
    
    all_2d_indices = set(data_2d_log.keys())
    existing_3d_indices = set(map_data.keys())
    
    # Identify Missing
    missing_indices = sorted(list(all_2d_indices - existing_3d_indices))
    
    log(f"2D Indices Found: {len(all_2d_indices)} across {len(files_2d)} scans")
    log(f"3D Indices Mapped: {len(existing_3d_indices)}")
    
    if not missing_indices:
        log("Status: COMPLETE")
    else:
        log(f"Status: INCOMPLETE ({len(missing_indices)} missing)")
        log("-" * 40)
        log(f"{'Index':<8} | {'# Views':<8}")
        log("-" * 40)
        for idx in missing_indices:
            count = len(data_2d_log[idx])
            log(f"{idx:<8} | {count:<8}")
        log("-" * 40)

    # 4. Output Final 3D List to Stdout
    if map_data:
        # Get fieldnames from the first entry
        first_key = next(iter(map_data))
        fieldnames = list(map_data[first_key].keys())
        
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx in sorted(map_data.keys()):
            writer.writerow(map_data[idx])

if __name__ == "__main__":
    main()