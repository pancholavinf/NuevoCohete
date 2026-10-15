from calc_luna import find_moon_intercept
from new_sim import config_manual
import numpy as np

def test_moon_shot():
    print("Initializing test configuration...")
    # Usar una configuración manual como base
    base_config = config_manual()
    # Limpiar encendidos para empezar de cero
    base_config.data_encendidos = []
    base_config.num_encendidos = 0
    
    # Reducir complejidad para test rápido
    base_config.periodo = 5000 # Simulación corta para test
    base_config.num_calc = 100
    
    print("Running find_moon_intercept...")
    result = find_moon_intercept(base_config)
    
    if result:
        print("\nTest PASSED: Optimizer found a solution.")
        print(result)
        # Verificar que la masa necesaria es positiva
        if result['mass_needed'] > 0:
            print("Mass calculation seems valid.")
        else:
            print("WARNING: Mass needed is <= 0.")
    else:
        print("\nTest FAILED: Optimizer did not find a solution (or timed out).")

if __name__ == "__main__":
    test_moon_shot()
