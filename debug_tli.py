import numpy as np
from calc_luna import find_moon_intercept
from modelo_3d import mu_earth, R_earth

class MockConfig:
    def __init__(self):
        self.m0 = 1000.0

# 1. Test from LEO (400 km circular)
print("\n--- TEST 1: LEO Circular (400 km) ---")
r_leo = R_earth + 400000.0
v_circ_leo = np.sqrt(mu_earth / r_leo)

conf_leo = MockConfig()
conf_leo.x0 = r_leo
conf_leo.y0 = 0.0
conf_leo.z0 = 0.0
conf_leo.vx0 = 0.0
conf_leo.vy0 = v_circ_leo
conf_leo.vz0 = 0.0

res_leo = find_moon_intercept(conf_leo)
if res_leo:
    print(f"Delta V: {res_leo['delta_v']:.2f} m/s")
    # Expected: Hohmann transfer to 384,400km
    # vp = sqrt(mu * (2/rp - 1/at))
    # at = (rp + ra)/2
    ra = 384400000.0
    at = (r_leo + ra) / 2
    vp_geo = np.sqrt(mu_earth * (2/r_leo - 1/at))
    dv_geo = vp_geo - v_circ_leo
    print(f"Expected Geo dV: {dv_geo:.2f} m/s")

# 2. Test from Elliptical Orbit (Non-Perigee)
print("\n--- TEST 2: Elliptical Mid-Point ---")
# Imagine an orbit 400x10000 km
r_p = R_earth + 400000.0
r_a = R_earth + 10000000.0
a_ell = (r_p + r_a) / 2
# Pick a point at r = semi-latus rectum or somewhere
r_mid = a_ell
v_mid_mag = np.sqrt(mu_earth * (2/r_mid - 1/a_ell))

# Velocity direction is NOT perpendicular to R
# But for simplicity let's just feed position/velocity and see if solver converges to Lunar Apogee
# flight path angle gamma != 0
# h = r v cos(gamma) = sqrt(mu a (1-e^2))

conf_ell = MockConfig()
conf_ell.x0 = r_mid
conf_ell.y0 = 0.0
conf_ell.z0 = 0.0
# Velocity has radial component
# This is tricky to construct exactly manually but we can trust the solver if it reports close match
conf_ell.vx0 = v_mid_mag * 0.1 # Some radial
conf_ell.vy0 = v_mid_mag * 0.9 # Some tangential
conf_ell.vz0 = 0.0

res_ell = find_moon_intercept(conf_ell)

# 3. Test "Perfect Orbit" Claim
# What if start is already high?
print("\n--- TEST 3: Already at Moon Distance ---")
conf_high = MockConfig()
conf_high.x0 = 384400000.0
conf_high.y0 = 0.0
conf_high.z0 = 0.0
conf_high.vx0 = 0.0
conf_high.vy0 = 1000.0 # Slow
conf_high.vz0 = 0.0

find_moon_intercept(conf_high)
