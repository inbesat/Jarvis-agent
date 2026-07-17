from jarvis_ui import get_accessibility_tree, capture_screen, execute_hybrid_action
from pywinauto import Application
import pyautogui
import time

# --- SAFETY FIRST ---
# If the mouse goes rogue, slam your cursor into any corner of your screen to abort!
pyautogui.FAILSAFE = True

# --- TEST 1: FAST LANE (Notepad) ---
def run_fast_lane_test():
    print("\n[ TEST 1 ] Testing Fast Lane...")
    try:
        app = Application(backend="uia").start("notepad.exe")
        time.sleep(2) # Give Notepad time to open
        
        # Test accessibility tree visibility
        print("\n--- OS ACCESSIBILITY TREE OUTPUT ---")
        print(get_accessibility_tree()) 
        print("------------------------------------\n")
        
        app.UntitledNotepad.Edit.type_keys("Hello World", with_spaces=True)
        print("[ SUCCESS ] Fast Lane Test Complete.\n")
    except Exception as e:
        print(f"[ ERROR ] Fast Lane Failed: {e}\n")

# --- TEST 2: VISION TEST (Start Button) ---
def run_vision_test():
    print("[ TEST 2 ] Testing Vision Routing...")
    # Capture screen and let the agent decide how to click the Start button
    img = capture_screen()
    
    if not img:
        print("[ ERROR ] Failed to capture screen.")
        return

    result = execute_hybrid_action("Click the Windows Start button", img)
    print(f"\n[ RESULT ] Vision Test Output: {result}")

if __name__ == "__main__":
    print("Initiating Agentic Systems Test...\n")
    
    # 1. Run the native OS test
    run_fast_lane_test()
    
    # Pause for 2 seconds to let you see what happened
    time.sleep(2) 
    
    # 2. Run the Vision coordinate test
    run_vision_test()