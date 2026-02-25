import cv2
import os

# --- CONFIGURATION ---
IMG_DIR = "../Dataset/Images"
LBL_DIR = "../Dataset/labels"

# Your EXACT Class List
CLASSES = [
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

# State variables
current_boxes = [] 
drawing = False
ix, iy = -1, -1

def mouse_callback(event, x, y, flags, param):
    global ix, iy, drawing, current_boxes
    h, w, _ = param.shape

    # --- LEFT CLICK: DRAW ---
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        # Calculate YOLO format
        x_min, x_max = min(ix, x), max(ix, x)
        y_min, y_max = min(iy, y), max(iy, y)
        
        # Don't create tiny noise boxes (smaller than 5 pixels)
        if (x_max - x_min) < 5 or (y_max - y_min) < 5:
            return

        bw = (x_max - x_min) / w
        bh = (y_max - y_min) / h
        xc = (x_min + (x_max - x_min)/2) / w
        yc = (y_min + (y_max - y_min)/2) / h
        
        current_boxes.append([-1, xc, yc, bw, bh])

    # --- RIGHT CLICK: DELETE ---
    elif event == cv2.EVENT_RBUTTONDOWN:
        # Find which box was clicked and remove it
        # We iterate backwards to delete the "top" box first if they overlap
        for idx in range(len(current_boxes) - 1, -1, -1):
            cls, xc, yc, bw, bh = current_boxes[idx]
            
            # Convert to pixels
            x1 = int((xc - bw/2) * w)
            y1 = int((yc - bh/2) * h)
            x2 = int((xc + bw/2) * w)
            y2 = int((yc + bh/2) * h)
            
            # Check collision
            if x1 <= x <= x2 and y1 <= y <= y2:
                print(f"Deleted Box {idx}")
                current_boxes.pop(idx)
                break # Only delete one at a time

def rescue_labeler():
    print("--- RESCUE LABELER v2 ---")
    print("  [Left Drag]  : Draw Box")
    print("  [Right Click]: DELETE Box")
    print("  [0-9]        : Label the RED box")
    print("  [t]          : Label Trailer (10)")
    print("  [d]          : Next Image")
    print("  [a]          : Previous Image")

    images = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg', '.png'))]
    if not images:
        print("ERROR: No images found.")
        return

    cv2.namedWindow('Rescue Labeler', cv2.WINDOW_NORMAL)
    
    i = 0
    while i < len(images):
        filename = images[i]
        img_path = os.path.join(IMG_DIR, filename)
        lbl_path = os.path.join(LBL_DIR, os.path.splitext(filename)[0] + ".txt")
        
        img = cv2.imread(img_path)
        if img is None: 
            i += 1
            continue

        # Load existing labels
        global current_boxes
        current_boxes = []
        if os.path.exists(lbl_path):
            with open(lbl_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        current_boxes.append([int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])

        cv2.setMouseCallback('Rescue Labeler', mouse_callback, img)

        while True:
            display = img.copy()
            h, w, _ = display.shape
            
            for idx, box in enumerate(current_boxes):
                cls, xc, yc, bw, bh = box
                
                x1 = int((xc - bw/2) * w)
                y1 = int((yc - bh/2) * h)
                x2 = int((xc + bw/2) * w)
                y2 = int((yc + bh/2) * h)
                
                # Green = Done, Red = Needs Label
                color = (0, 255, 0)
                if cls == -1: color = (0, 0, 255)
                
                # Highlight if it's the active one to be labeled
                thickness = 2
                if idx == len(current_boxes) - 1 and cls == -1:
                    thickness = 4

                cv2.rectangle(display, (x1, y1), (x2, y2), color, thickness)
                
                label_txt = "???" if cls == -1 else CLASSES[int(cls)]
                cv2.putText(display, label_txt, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # UI Bar
            cv2.rectangle(display, (0, 0), (w, 40), (0, 0, 0), -1)
            cv2.putText(display, f"{i+1}/{len(images)}: {filename} | Right-Click to Delete | Keys: 0-9 for Class", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow('Rescue Labeler', display)
            key = cv2.waitKey(20) & 0xFF

            if key == ord('d'): # Next
                with open(lbl_path, 'w') as f:
                    for b in current_boxes:
                        if b[0] != -1: 
                            f.write(f"{int(b[0])} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f} {b[4]:.6f}\n")
                i += 1
                break
            
            if key == ord('a'): # Prev
                i = max(0, i-1)
                break
            
            if key == 27: # Esc
                cv2.destroyAllWindows()
                return

            # Class Assignment
            if 48 <= key <= 57: # 0-9
                cls_id = key - 48
                for b in reversed(current_boxes):
                    if b[0] == -1:
                        b[0] = cls_id
                        break
            if key == ord('t'): # Trailer
                for b in reversed(current_boxes):
                    if b[0] == -1: b[0] = 10; break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    rescue_labeler()