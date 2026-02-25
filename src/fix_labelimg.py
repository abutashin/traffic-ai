import os
import sys
import glob

def fix_file(filepath, fixes):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for bad_code, good_code in fixes.items():
            if bad_code in content:
                content = content.replace(bad_code, good_code)
                print(f"  [FIXED] Found and repaired bug in: {os.path.basename(filepath)}")
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            print(f"  [OK] No bugs found in: {os.path.basename(filepath)}")
            return False
    except Exception as e:
        print(f"  [ERROR] Could not process {filepath}: {e}")
        return False

def main():
    # 1. Locate the installed labelImg package
    # In your error screenshot, the path was in AppData/Roaming/.../site-packages
    # We use sys.path to find site-packages automatically
    site_packages = next(p for p in sys.path if 'site-packages' in p)
    
    labelimg_path = os.path.join(site_packages, 'labelImg')
    libs_path = os.path.join(site_packages, 'libs')
    
    print(f"Searching for LabelImg in: {site_packages}...")

    # --- DEFINING THE BUGS TO FIX ---
    
    # Bug 1: labelImg.py (The scroll bar crash)
    bug1 = {
        'bar.setValue(bar.value() + bar.singleStep() * units)': 
        'bar.setValue(int(bar.value() + bar.singleStep() * units))'
    }
    
    # Bug 2: canvas.py (The drawing line crash - Line 530)
    bug2 = {
        'p.drawLine(self.prev_point.x(), 0, self.prev_point.x(), self.pixmap.height())': 
        'p.drawLine(int(self.prev_point.x()), 0, int(self.prev_point.x()), int(self.pixmap.height()))',
        
        'p.drawLine(0, self.prev_point.y(), self.pixmap.width(), self.prev_point.y())': 
        'p.drawLine(0, int(self.prev_point.y()), int(self.pixmap.width()), int(self.prev_point.y()))'
    }

    # Bug 3: canvas.py (The rectangle crash - Line 526)
    bug3 = {
        'p.drawRect(left_top.x(), left_top.y(), rect_width, rect_height)':
        'p.drawRect(int(left_top.x()), int(left_top.y()), int(rect_width), int(rect_height))'
    }

    # --- APPLYING FIXES ---
    
    # Fix labelImg.py
    target_main = os.path.join(labelimg_path, 'labelImg.py')
    if os.path.exists(target_main):
        fix_file(target_main, bug1)
    else:
        # Sometimes it installs directly in site-packages
        fix_file(os.path.join(site_packages, 'labelImg.py'), bug1)

    # Fix canvas.py
    target_canvas = os.path.join(libs_path, 'canvas.py')
    if os.path.exists(target_canvas):
        # Apply both drawing bugs
        combined_fixes = {**bug2, **bug3}
        fix_file(target_canvas, combined_fixes)
    else:
        print("WARNING: Could not find canvas.py in libs folder.")

    print("\n Repairs complete. Try running 'labelImg' now!")

if __name__ == "__main__":
    main()