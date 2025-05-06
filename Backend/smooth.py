from scipy.interpolate import splprep, splev
import numpy as np

def bspline_smooth(path, smoothing_factor=0.5):
    """Smooth a given path using B-spline interpolation (longitude, latitude format)."""
    path = np.array(path)  # Ensure path is a NumPy array
    
    if len(path) < 4:
        return path.tolist()  # Not enough points for B-spline, return original path as list

    # Extract longitude and latitude separately
    tck, u = splprep([path[:, 0], path[:, 1]], s=smoothing_factor)
    
    # Generate more points for a smoother curve
    u_new = np.linspace(0, 1, len(path) * 5)
    smooth_points = splev(u_new, tck)

    # Return smoothed path as a list of (lon, lat) tuples
    return list(zip(smooth_points[0], smooth_points[1]))
