import numpy as np
import os
from grf_data import animar_simulacion
from archivo_open import AdminResultasosSim

# Mock or Load data
def test_animation():
    sim_id = "121"
    filename = f"log_simulaciones/sim_run_{sim_id}.npz"
    
    if not os.path.exists(filename):
        print(f"Test file {filename} not found. Skipping.")
        return

    print(f"Loading {filename}...")
    data = np.load(filename, allow_pickle=True)
    
    # Reconstruct tuple like graf_data() does
    # (tout, x, y, z, vx, vy, vz, mass, alt, xL, yL, zL, vxL, vyL, vzL, ang, desc)
    
    # Handle old/new compatibility manually as per archivo_open logic
    try:
        alt_km = data['alt_tierra_km']
    except KeyError:
        Rplanet = 6_357_000.0
        alt_km = (np.sqrt(data['position_x']**2 + data['position_y']**2 + data['position_z']**2) - Rplanet) / 1000.0
        
    try:
        # This might be just 'ang' or we need to format it
        ang = data['ang']
    except KeyError:
        ang = []

    # Slice data for speed test (first 100 points)
    limit = 10
    sim_data_tuple = (
        data['time'][:limit],
        data['position_x'][:limit], data['position_y'][:limit], data['position_z'][:limit],
        data['velocity_x'][:limit], data['velocity_y'][:limit], data['velocity_z'][:limit],
        data['mass'][:limit],
        alt_km[:limit],
        data['L_pos_x'][:limit], data['L_pos_y'][:limit], data['L_pos_z'][:limit],
        data['L_vel_x'][:limit], data['L_vel_y'][:limit], data['L_vel_z'][:limit],
        ang,
        str(data.get('description', 'Test Description'))
    )

    output_dir = "vid_sims"
    vid_name = f"{sim_id}_sim"
    
    print("Calling animar_simulacion (fast mode)...")
    animar_simulacion(sim_data_tuple, output_folder=output_dir, video_name=vid_name)
    
    expected_mp4 = os.path.join(output_dir, vid_name + ".mp4")
    expected_gif = os.path.join(output_dir, vid_name + ".gif")
    
    if os.path.exists(expected_mp4) and os.path.getsize(expected_mp4) > 0:
        print(f"SUCCESS: MP4 created at {expected_mp4}")
    elif os.path.exists(expected_gif) and os.path.getsize(expected_gif) > 0:
        print(f"SUCCESS: GIF created at {expected_gif} (FFmpeg fallback)")
    else:
        print(f"FAILURE: No video found at {expected_mp4} or {expected_gif}")

if __name__ == "__main__":
    test_animation()
