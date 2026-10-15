from new_sim import config_400km_moon_plane
from modelo_3d import calc_sim
import numpy as np

def test_400km_sim():
    print("Testing config_400km_moon_plane...")
    config = config_400km_moon_plane()
    
    # Check altitude
    r_target = 6371000.0 + 400000.0
    print(f"Target Radius: {r_target}")
    print(f"Config x0: {config.x0}")
    assert np.isclose(config.x0, r_target), f"Expected x0 to be {r_target}, got {config.x0}"
    
    # Check velocity
    v_expected = np.sqrt(3.986004418e14 / r_target)
    print(f"Target Velocity: {v_expected}")
    print(f"Config vy0: {config.vy0}")
    assert np.isclose(config.vy0, v_expected), f"Expected vy0 to be {v_expected}, got {config.vy0}"
    
    # Check plane
    assert config.z0 == 0.0, "z0 should be 0"
    assert config.vz0 == 0.0, "vz0 should be 0"
    
    # Run simulation
    print("Running simulation (calc_sim)...")
    try:
        result = calc_sim(config)
        tout = result[0]
        print(f"Simulation finished successfully. Steps: {len(tout)}")
    except Exception as e:
        print(f"Simulation failed: {e}")
        raise

if __name__ == "__main__":
    test_400km_sim()
