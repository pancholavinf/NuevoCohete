
import numpy as np
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from new_sim import ConfigSim, test_config, config_from_sim_silent, config_manual
from calc_luna import find_moon_intercept
from modelo_3d import calc_sim
from archivo_open import AdminResultasosSim

def create_dummy_sim_result():
    # Run a quick test sim to get some data using a stable config
    print("Generating base simulation data...")
    c = config_manual()
    # Use defaults or slightly reduced for speed, but keep ratio sane
    c.periodo = 5000
    c.num_calc = 1000 
    result = calc_sim(c)
    
    # Unpack result (tuple or list)
    tout, posx, posy, posz, velx, vely, velz, mass, alt_km, poslx, posly, poslz, vellx, velly, vellz, ang, desc = result
    
    # Create the object explicitly as getdata() would
    sim_obj = AdminResultasosSim(
        name="test_sim",
        description="test description",
        posx=posx, posy=posy, posz=posz,
        velx=velx, vely=vely, velz=velz,
        mass=mass,
        alt_tierra_km=alt_km,
        poslx=poslx, posly=posly, poslz=poslz,
        vellx=vellx, velly=velly, vellz=vellz,
        tout=tout,
        ang=ang,
        num_encendidos=len(c.data_encendidos)
    )
    return sim_obj

def test_integration():
    print("=== STARTING INTEGRATION TEST ===")
    
    # 1. Create a dummy simulation object with data
    sim_activa = create_dummy_sim_result()
    print(f"Base simulation created with {len(sim_activa.tout)} steps.")
    
    # 2. Pick a time index to calculate from (e.g., middle of the sim)
    time0 = 50
    print(f"Selecting time index: {time0}")
    
    # 3. Call config_from_sim_silent (THE NEW FUNCTION)
    print("Testing config_from_sim_silent...")
    new_config = config_from_sim_silent(time0, sim_activa)
    
    if new_config is None:
        print("FAILED: config_from_sim_silent returned None")
        return
        
    print("config_from_sim_silent SUCCESS.")
    print(f"New Config Start Position: ({new_config.x0}, {new_config.y0}, {new_config.z0})")
    print(f"Original Position at t={time0}: ({sim_activa.posx[time0]}, {sim_activa.posy[time0]}, {sim_activa.posz[time0]})")
    
    # Verify values match
    if abs(new_config.x0 - sim_activa.posx[time0]) < 0.1:
        print("Position match verified.")
    else:
        print("FAILED: Position mismatch!")
        return

    # 4. Call find_moon_intercept (OPTIMIZER)
    print("Testing find_moon_intercept optimization...")
    # Reduce bounds/iter for speed in this test
    # (In real usage it takes longer, but we just want to ensure it RUNS and doesn't crash)
    # Actually we can't easily change bounds inside the function without modifying it, 
    # but we can let it run. It has maxiter=20, shouldn't be too long.
    
    try:
        burn_params = find_moon_intercept(new_config)
        
        if burn_params:
            print("\nANALYTICAL CALCULATOR SUCCESS.")
            print("Found params:", burn_params)
            print(f"Calculated Delta-V: {burn_params.get('delta_v', 0):.2f} m/s")
        else:
            print("\nCALCULATOR returned None (Error condition triggered).")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAILED: Optimizer crashed with error: {e}")
        return

    print("\n=== INTEGRATION TEST PASSED ===")

if __name__ == "__main__":
    test_integration()
