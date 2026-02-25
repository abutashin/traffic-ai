import os

# --- CONFIG ---
LABEL_DIR = "../Dataset/labels"
CLASSES_FILE = "../Dataset/labels/classes.txt"

# HARDCODED CORRECT LIST (From your PDF)
CORRECT_CLASSES = [
    "Auto Rickshaw",      # 0
    "Cycle Rickshaw",     # 1
    "CNG / Tempo",        # 2
    "Bus",                # 3
    "Jeep / SUV",         # 4
    "Microbus",           # 5
    "Minibus",            # 6
    "Motorcycle",         # 7
    "Truck",              # 8
    "Private Sedan Car",  # 9
    "Trailer"             # 10
]

def force_fix():
    print("--- STARTING FORCE FIX ---")
    
    # 1. Force-write the correct classes.txt
    # This prevents LabelImg from using a corrupted list
    print(f"Overwriting {CLASSES_FILE} with correct list...")
    with open(CLASSES_FILE, 'w') as f:
        for name in CORRECT_CLASSES:
            f.write(f"{name}\n")
            
    # 2. Sanitize every single label file
    files = [f for f in os.listdir(LABEL_DIR) if f.endswith(".txt") and f != "classes.txt"]
    print(f"Scanning {len(files)} label files for 'Ghost IDs'...")
    
    fixed_count = 0
    max_id = len(CORRECT_CLASSES) - 1 # Max ID is 10

    for filename in files:
        path = os.path.join(LABEL_DIR, filename)
        
        with open(path, 'r') as f:
            lines = f.readlines()
        
        valid_lines = []
        dirty = False
        
        for line in lines:
            parts = line.strip().split()
            if not parts: continue
            
            try:
                class_id = int(parts[0])
                # CRITICAL CHECK: If ID is 11, 12, 15... DELETE IT.
                if 0 <= class_id <= max_id:
                    valid_lines.append(line)
                else:
                    print(f"  [DEL] {filename}: Removing invalid Class ID {class_id}")
                    dirty = True
            except ValueError:
                continue

        if dirty:
            with open(path, 'w') as f:
                f.writelines(valid_lines)
            fixed_count += 1

    print("-" * 30)
    print(f"DONE. Fixed {fixed_count} files.")
    print("classes.txt has been reset.")
    print("You may now open LabelImg.")

if __name__ == "__main__":
    force_fix()