import os

# --- CONFIG ---
LABEL_DIR = "../Dataset/labels"
CLASSES_FILE = "../Dataset/labels/classes.txt"

def clean_labels():
    print(f"Scanning {os.path.abspath(LABEL_DIR)}...")

    # 1. Load your valid classes
    if not os.path.exists(CLASSES_FILE):
        print("❌ ERROR: classes.txt NOT FOUND in Dataset/labels")
        print("Please copy your classes.txt there immediately.")
        return

    with open(CLASSES_FILE, 'r') as f:
        classes = [line.strip() for line in f.readlines() if line.strip()]
    
    max_valid_id = len(classes) - 1
    print(f"✅ Loaded {len(classes)} classes. Valid IDs are 0 to {max_valid_id}.")

    # 2. Fix the files
    files = [f for f in os.listdir(LABEL_DIR) if f.endswith(".txt") and f != "classes.txt"]
    fixed_count = 0

    for filename in files:
        path = os.path.join(LABEL_DIR, filename)
        
        with open(path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        file_dirty = False

        for line in lines:
            parts = line.strip().split()
            if not parts: continue
            
            # The first number is the Class ID
            try:
                class_id = int(parts[0])
            except ValueError:
                continue # Skip garbage lines

            # KILL COMMAND: If ID is bigger than 10, delete the line.
            if class_id > max_valid_id:
                print(f"   ⚠️ Found BAD Class ID {class_id} in {filename} -> DELETED.")
                file_dirty = True
            else:
                new_lines.append(line)
        
        # Save only if we changed something
        if file_dirty:
            with open(path, 'w') as f:
                f.writelines(new_lines)
            fixed_count += 1

    print("-" * 30)
    print(f"🎉 Cleanup Complete. Fixed {fixed_count} corrupted files.")
    print("You can run 'labelImg' now.")

if __name__ == "__main__":
    clean_labels()