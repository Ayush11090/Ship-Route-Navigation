import React, { useEffect } from 'react';

function App() {
  useEffect(() => {
    const options = {
      key: 'Z7Venz8r7srQPY2ULcAxP5Aj97kOB06L', // Replace with your key
      verbose: true,
      lat: 50.4,
      lon: 14.3,
      zoom: 5,
    };

    let mapInstance;

    // Initialize Windy map
    windyInit(options, (windyAPI) => {
      const { map } = windyAPI;
      mapInstance = map;

      // Route coordinates
      const routeCoords = [
        [51.9225, 4.47917],  // Rotterdam
        [35.6895, 139.6917], // Tokyo
        [1.3521, 103.8198]   // Singapore
      ];

      // Create polyline
      const route = L.polyline(routeCoords, {
        color: 'blue',
        weight: 5,
        opacity: 0.7,
      }).addTo(map);

      // Fit map to route bounds
      map.fitBounds(route.getBounds());

      // Add markers
      routeCoords.forEach(coord => {
        L.marker(coord).addTo(map);
      });
    });

    // Cleanup function
    return () => {
      if (mapInstance) {
        mapInstance.remove();
      }
    };
  }, []); // Empty dependency array ensures this runs once

  return (
    <div 
      id="windy" 
      style={{ 
        width: '100%', 
        height: '100vh',
        position: 'absolute',
        top: 0,
        left: 0
      }} 
    />
  );
}

export default App;