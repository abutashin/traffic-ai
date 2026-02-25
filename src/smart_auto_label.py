from ultralytics import YOLO
import os

# --- PATH CONFIGURATION (Matches your screenshot) ---
source_images = "../Dataset/Images"
output_labels = "../Dataset/labels"  # This folder will be created automatically

# --- MAPPING LOGIC ---
# We map standard AI detections (COCO) to YOUR specific Class IDs.
# Note: The AI will label all cars as "Private Sedan" (ID 9). 
# You can quickly change them to "Jeep" or "Microbus" in the manual step if needed.

smart_mapping = {
    2: 9,   # COCO "Car"        -> Your "Private Sedan Car" (ID 9)
    3: 7,   # COCO "Motorcycle" -> Your "Motorcycle" (ID 7)
    5: 3,   # COCO "Bus"        -> Your "Bus" (ID 3)
    7: 8    # COCO "Truck"      -> Your "Truck" (ID 8)
}

def auto_label_smart():
    print(f"Looking for images in: {os.path.abspath(source_images)}")
    
    # Load the heavy model for best accuracy
    print("Loading AI model (this might take a moment)...")
    model = YOLO('yolov8x.pt') 
    
    os.makedirs(output_labels, exist_ok=True)
    
    # Get all images
    try:
        files = [f for f in os.listdir(source_images) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    except FileNotFoundError:
        print("ERROR: Could not find the 'Dataset/Images' folder.")
        print("Make sure you are running this script from the 'src' folder!")
        return

    print(f"Found {len(files)} images. Starting auto-labeling...")

    for i, filename in enumerate(files):
        filepath = os.path.join(source_images, filename)
        
        # Run AI detection
        results = model(filepath, conf=0.4, verbose=False)
        
        labels = []
        for box in results[0].boxes:
            coco_id = int(box.cls[0])
            
            # Only save if it's a vehicle we can confidently identify
            if coco_id in smart_mapping:
                my_id = smart_mapping[coco_id]
                x, y, w, h = box.xywhn[0]
                labels.append(f"{my_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
        
        # Save the label file
        txt_name = os.path.splitext(filename)[0] + ".txt"
        with open(os.path.join(output_labels, txt_name), "w") as f:
            f.write("\n".join(labels))
            
        if i % 50 == 0 and i > 0:
            print(f"Processed {i} images...")

    print("Success! Standard vehicles labeled.")
    print("Now open LabelImg to fix the Jeeps and add the Rickshaws!")

if __name__ == "__main__":
    auto_label_smart()