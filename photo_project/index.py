import cv2
import os
import datetime
import time
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from threading import Thread

# Directories
CAPTURE_DIR = "captured_images"
MERGE_DIR = "merge"
BORDER_IMAGES = ["frame1.png", "frame2.png", "frame3.png", "frame4.png"]
os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(MERGE_DIR, exist_ok=True)

# Global variables
captured_frame = None
paused = False
selected_border_idx = -1
border_applied_frame = None
countdown_active = False
countdown_start_time = None
countdown_duration = 0
last_activity_time = time.time()

# Initialize Tkinter window
root = tk.Tk()
root.title("Project Photo")
root.attributes('-fullscreen', True)  # Make the window fullscreen

# Configure main layout
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Video display area (top 80% of the screen)
video_canvas = tk.Canvas(main_frame, bg="black")
video_canvas.pack(fill=tk.BOTH, expand=True)

# Text display area (above buttons)
text_display_area = tk.Label(main_frame, text="Select timer", font=("Arial", 16))
text_display_area.pack(pady=5)

# Button container (bottom 20% of the screen)
button_frame = tk.Frame(main_frame)
button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)




# all the button coordinate and size are changed here you can change it to your desired size

# Timer buttons (5s, 10s, 15s)
timer_btn_frame = tk.Frame(button_frame)
timer_btn_frame.pack(side=tk.TOP, pady=5, fill=tk.X)  # Added fill=tk.X to expand frame horizontally

btn_5s = tk.Button(timer_btn_frame, text="5 Second", width=20, height=3)
btn_10s = tk.Button(timer_btn_frame, text="10 Second", width=20, height=3)
btn_15s = tk.Button(timer_btn_frame, text="15 Second", width=20, height=3)

btn_5s.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)  # Added fill=tk.X
btn_10s.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X) # Added fill=tk.X
btn_15s.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X) # Added fill=tk.X


# Action buttons (Save, Resume, Print)
action_btn_frame = tk.Frame(button_frame)
action_btn_frame.pack(side=tk.TOP, pady=5, fill=tk.X)  # Added fill=tk.X

btn_save = tk.Button(action_btn_frame, text="Save", width=30, height=3)
btn_resume = tk.Button(action_btn_frame, text="Resume", width=30, height=3)
btn_print = tk.Button(action_btn_frame, text="Print", width=30, height=3)

# Use grid layout for precise placement
action_btn_frame.columnconfigure(0, weight=1)  # Expand first column
action_btn_frame.columnconfigure(1, weight=1)  # Expand second column
action_btn_frame.columnconfigure(2, weight=1)  # Expand third column

btn_save.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
btn_resume.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
btn_print.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

action_btn_frame.pack_forget()  # Initially hidden

# the button size settings code ends here



# Frame selection area (bottom of the screen)
frame_selection_frame = tk.Frame(button_frame)
frame_selection_frame.pack(side=tk.BOTTOM, pady=5)

border_labels = []
for i in range(4):
    border_img = Image.open(BORDER_IMAGES[i])
    border_img = border_img.resize((150, 100), Image.ANTIALIAS)  # Smaller thumbnails
    border_photo = ImageTk.PhotoImage(border_img)
    label = tk.Label(frame_selection_frame, image=border_photo)
    label.image = border_photo
    label.pack(side=tk.LEFT, padx=5)
    border_labels.append(label)

# Camera initialization
camera = cv2.VideoCapture(2)
if not camera.isOpened():
    print("Error: Camera not found!")
    camera.release()
    exit()

# Create a transparent overlay for dimming
overlay = tk.Frame(root, bg="black")
overlay.place(relwidth=1, relheight=1)  # Cover the entire window
overlay.lift()  # Bring it to the top
overlay.place_forget()  # Initially hidden

# Add "Sleeping" message to the overlay
sleeping_label = tk.Label(overlay, text="Sleeping", font=("Arial", 50), fg="white", bg="black")
sleeping_label.place(relx=0.5, rely=0.5, anchor="center")

def show_timer_buttons():
    action_btn_frame.pack_forget()
    frame_selection_frame.pack_forget()
    timer_btn_frame.pack(side=tk.TOP, pady=5)

def show_action_buttons():
    timer_btn_frame.pack_forget()
    action_btn_frame.pack(side=tk.TOP, pady=5)
    frame_selection_frame.pack(side=tk.BOTTOM, pady=5)

def save_frame(frame):
    global captured_frame, paused, border_applied_frame
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(CAPTURE_DIR, f"capture_{timestamp}.jpg")
    frame_resized = cv2.resize(frame, (900, 1200))  # Resize to 1200x900
    cv2.imwrite(filename, frame_resized)
    captured_frame = frame_resized
    paused = True
    border_applied_frame = None
    text_display_area.config(text="Select frame and click Save")
    show_action_buttons()

def apply_border():
    global captured_frame, selected_border_idx, border_applied_frame
    if captured_frame is None or selected_border_idx < 0:
        return

    border_img = cv2.imread(BORDER_IMAGES[selected_border_idx], cv2.IMREAD_UNCHANGED)
    if border_img is None:
        print("Error: Border image not found.")
        return

    border_resized = cv2.resize(border_img, (900, 1200))

    if border_resized.shape[-1] == 4:
        overlay = border_resized[:, :, :3]
        mask = border_resized[:, :, 3] / 255.0
        merged_image = (captured_frame * (1 - mask[..., None]) + overlay * mask[..., None])
        merged_image = merged_image.astype(np.uint8)
    else:
        merged_image = cv2.addWeighted(captured_frame, 0.7, border_resized, 0.3, 0)

    border_applied_frame = merged_image
    text_display_area.config(text=f"Border {selected_border_idx+1} applied")

def update_frame():
    global paused, countdown_active, countdown_start_time, countdown_duration, captured_frame, border_applied_frame, last_activity_time

    if not paused:
        ret, frame = camera.read()
        if not ret:
            print("Error: Unable to read from camera.")
            return

        # Crop the frame to 1440x900
        height, width, _ = frame.shape
        crop_width = int((width - 1440) / 2)
        frame = frame[:, crop_width:crop_width+1440]

        if countdown_active:
            elapsed_time = time.time() - countdown_start_time
            remaining_time = countdown_duration - int(elapsed_time)

            if remaining_time > 0:
                cv2.putText(frame, str(remaining_time), 
                           (frame.shape[1]//2-50, frame.shape[0]//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 0), 4)
            else:
                save_frame(frame)
                countdown_active = False

    if paused and captured_frame is not None:
        frame = border_applied_frame if border_applied_frame is not None else captured_frame

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)

    # Resize the image to fit within the canvas without stretching
    canvas_width = video_canvas.winfo_width()
    canvas_height = video_canvas.winfo_height()
    img_ratio = img.width / img.height
    canvas_ratio = canvas_width / canvas_height

    if canvas_ratio > img_ratio:
        new_height = canvas_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = canvas_width
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.ANTIALIAS)
    imgtk = ImageTk.PhotoImage(image=img)

    # Clear the canvas and display the new image
    video_canvas.delete("all")
    video_canvas.create_image(
        (canvas_width - new_width) // 2, (canvas_height - new_height) // 2,
        anchor=tk.NW, image=imgtk
    )
    video_canvas.imgtk = imgtk  # Keep a reference to avoid garbage collection

    # change the timer for inactivity from 10 to any seconds you want
    if time.time() - last_activity_time > 120:
        overlay.place(relwidth=1, relheight=1)  # Show the overlay
    else:
        overlay.place_forget()  # Hide the overlay

    root.after(30, update_frame)  # Reduced update frequency

def start_countdown(duration):
    global countdown_active, countdown_start_time, countdown_duration, last_activity_time
    countdown_duration = duration
    countdown_active = True
    countdown_start_time = time.time()
    last_activity_time = time.time()
    text_display_area.config(text=f"{duration}-second timer started")

def on_border_click(event, index):
    global selected_border_idx, last_activity_time
    selected_border_idx = index
    last_activity_time = time.time()
    apply_border()

def on_save():
    global last_activity_time
    if border_applied_frame is not None:
        save_path = os.path.join(MERGE_DIR, f"merged_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png")
        cv2.imwrite(save_path, border_applied_frame)
        text_display_area.config(text=f"Saved: {save_path}")
    last_activity_time = time.time()

def on_resume():
    global paused, captured_frame, border_applied_frame, selected_border_idx, last_activity_time
    paused = False
    captured_frame = None
    border_applied_frame = None
    selected_border_idx = -1
    last_activity_time = time.time()
    show_timer_buttons()
    text_display_area.config(text="Select timer")

def on_print():
    global last_activity_time
    text_display_area.config(text="Printing...")
    last_activity_time = time.time()

# Bind events
for idx, label in enumerate(border_labels):
    label.bind("<Button-1>", lambda e, i=idx: on_border_click(e, i))

btn_5s.config(command=lambda: start_countdown(5))
btn_10s.config(command=lambda: start_countdown(10))
btn_15s.config(command=lambda: start_countdown(15))
btn_save.config(command=on_save)
btn_resume.config(command=on_resume)
btn_print.config(command=on_print)

# Initial state
show_timer_buttons()

# Start video feed in a separate thread
def video_thread():
    update_frame()

Thread(target=video_thread, daemon=True).start()

# Track mouse movement for inactivity
def on_activity(event):
    global last_activity_time
    last_activity_time = time.time()

root.bind("<Motion>", on_activity)
root.bind("<ButtonPress>", on_activity)

root.mainloop()

# Release resources
camera.release()
cv2.destroyAllWindows()