import os
import shutil
import random

# --- CONFIGURATION ---
# Input (Where your stuff is now)
SRC_IMG = "../Dataset/Images"
SRC_LBL = "../Dataset/labels"

# Output (Where we will build the clean YOLO dataset)
DST_DIR = "../Dataset_Final"

def prepare_dataset():
    # 1. Create structure: images/train, images/val, labels/train, labels/val
    for split in ['train', 'val']:
        os.makedirs(f"{DST_DIR}/images/{split}", exist_ok=True)
        os.makedirs(f"{DST_DIR}/labels/{split}", exist_ok=True)

    # 2. Get list of valid pairs (Image + Label)
    images = [f for f in os.listdir(SRC_IMG) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    valid_pairs = []

    print(f"Scanning {len(images)} images...")
    
    for img_file in images:
        name = os.path.splitext(img_file)[0]
        lbl_file = name + ".txt"
        
        # Check if label exists
        if os.path.exists(os.path.join(SRC_LBL, lbl_file)):
            valid_pairs.append((img_file, lbl_file))
        else:
            print(f"  [SKIP] Missing label for: {img_file}")

    # 3. Shuffle and Split (80% Train, 20% Val)
    random.shuffle(valid_pairs)
    split_idx = int(len(valid_pairs) * 0.8)
    train_set = valid_pairs[:split_idx]
    val_set = valid_pairs[split_idx:]

    print(f"Moving {len(train_set)} items to TRAIN and {len(val_set)} to VAL...")

    # 4. Copy files
    def copy_files(file_list, split_name):
        for img, lbl in file_list:
            # Copy Image
            shutil.copy(os.path.join(SRC_IMG, img), os.path.join(DST_DIR, 'images', split_name, img))
            # Copy Label
            shutil.copy(os.path.join(SRC_LBL, lbl), os.path.join(DST_DIR, 'labels', split_name, lbl))

    copy_files(train_set, 'train')
    copy_files(val_set, 'val')
    
    print("SUCCESS! Your data is ready in '../Dataset_Final'")

if __name__ == "__main__":
    prepare_dataset()