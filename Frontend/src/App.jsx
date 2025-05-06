import React, { useEffect, useRef, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';

function App() {
  const [coordinates, setCoordinates] = useState([]);
  const [weatherData, setWeatherData] = useState([]);
  const [start, setStart] = useState('');
  const [distance, setDistance] = useState(0);
  const [end, setEnd] = useState('');
  const [status, setStatus] = useState('Disconnected');
  const mapRef = useRef(null);
  const polylineRef = useRef(null);
  const markersRef = useRef([]);
  const weatherMarkersRef = useRef([]);
  const wsRef = useRef(null);

  useEffect(() => {
    const options = {
      key: 'Z7Venz8r7srQPY2ULcAxP5Aj97kOB06L',
      verbose: true,
      zoom: 5,
    };

    windyInit(options, (windyAPI) => {
      const { map } = windyAPI;
      mapRef.current = map;

      polylineRef.current = L.polyline([], {
        color: '#FF6B6B',
        weight: 3,
        opacity: 0.9,
      }).addTo(map);

      return () => {
        if (mapRef.current) mapRef.current.remove();
      };
    });
  }, []);

  useEffect(() => {
    if (coordinates.length > 0 && polylineRef.current) {
      const latLngs = coordinates.map(coord => [coord[0], coord[1]]);
      polylineRef.current.setLatLngs(latLngs);

      // Clear previous markers
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current = [];

      // Add new markers
      coordinates.forEach(coord => {
        const circleMarker = L.circleMarker(coord, {
          radius: 1, // Small dot
          color: '#FF0000', // Red color
          fillColor: '#FF0000',
          fillOpacity: 1
        }).addTo(mapRef.current);
      
        // Bind popup to show coordinates on hover
        circleMarker.bindTooltip(`${coord[0].toFixed(4)}, ${coord[1].toFixed(4)}`, {
          permanent: false, 
          direction: 'top'
        });
      
        markersRef.current.push(circleMarker);
      });

      // Center map on latest coordinate
      mapRef.current.panTo(coordinates[coordinates.length - 1]);
    }
  }, [coordinates]);

  useEffect(() => {
    weatherMarkersRef.current.forEach(marker => marker.remove());
    weatherMarkersRef.current = [];

    weatherData.forEach(point => {
      const { coordinate, wind_speed, wind_direction, wave_height} = point;
      const marker = L.circleMarker(coordinate, {
        radius: 6,
        color: '#3B82F6',
        fillColor: '#3B82F6',
        fillOpacity: 0.7
      }).addTo(mapRef.current);

      const popupContent = `
        <div style="padding: 8px;">
          <h4 style="margin: 0 0 8px 0;">Weather Conditions</h4>
           <p style="margin: 4px 0;">Coordinate: ${coordinate}</p>
          <p style="margin: 4px 0;">Wind Speed: ${wind_speed} km/hr</p>
          <p style="margin: 4px 0;">Wind Direction: ${wind_direction}°</p>
          <p style="margin: 4px 0;">Wave Height: ${wave_height} m</p>
          <p style="margin: 4px 0;">Wave Direction: ${0}°</p>
          <p style="margin: 4px 0;">Current Velocity: ${0}Km/hr</p>
          <p style="margin: 4px 0;">Current Direction: ${0}°</p>
        </div>
      `;

      marker.bindPopup(popupContent);
      weatherMarkersRef.current.push(marker);
    });
  }, [weatherData]);

  const connectWebSocket = () => {
    setStatus('Connecting...');
    wsRef.current = new WebSocket('ws://localhost:5000');

    wsRef.current.onopen = () => {
      setStatus('Path is Mapping...');
      const message = JSON.stringify({
        type: 'start',
        start: start.split(',').map(Number),
        end: end.split(',').map(Number)
      });
      wsRef.current.send(message);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'final':
          setCoordinates(data.path);
          setWeatherData(data.weather);
          setDistance(data.distance)
          break;
        case 'error':
          setStatus(`Error: ${data.message}`);
          break;
      }
    };

    wsRef.current.onerror = (error) => {
      setStatus("Error: Connection failed");
    };

    wsRef.current.onclose = () => {
      setStatus('Disconnected');
    };
  };

  const validateCoordinates = (input) => {
    const coords = input.split(',').map(Number);
    return coords.length === 2 && 
           !isNaN(coords[0]) && 
           !isNaN(coords[1]) &&
           Math.abs(coords[0]) <= 90 &&
           Math.abs(coords[1]) <= 180;
  };
  
  const startNavigation = () => {
    if (!validateCoordinates(start) || !validateCoordinates(end)) {
      alert('Invalid coordinates! Use format: lat,lon');
      return;
    }
    connectWebSocket();
  };


  return (
    <div style={{ height: '100vh', width: '100vw', overflow: 'hidden', position: 'relative' }}>
  {/* Windy Map - Fullscreen Background */}
  <div 
    id="windy" 
    style={{ 
      width: '100%', 
      height: '100%',
      position: 'relative',
      zIndex: 1 
    }}
  />

  {/* Top Navbar - Glassmorphic Overlay */}
  <div style={{
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    padding: '15px 20px',
    color: '#fff',
    background: 'rgba(0, 0, 0,0.8)',
    backdropFilter: 'blur(40px)',
    WebkitBackdropFilter: 'blur(40px)',
    fontSize: '20px',
    fontWeight: 'bold',
    letterSpacing: '1px',
    boxSizing: 'border-box',
    borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
    zIndex: 10
  }}>
    🚢 AI Ship Optimal Route Finder Tool
  </div>

  {/* Input Panel - Glassmorphic Overlay */}
  <div style={{
    position: 'absolute',
    top: '60px',
    left: '20px',
    width: '300px',
    marginTop: '40px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(40px)',
    WebkitBackdropFilter: 'blur(40px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '15px',
    padding: '20px',
    color: '#fff',
    boxShadow: '4px 4px 30px rgba(0,0,0,0.3)',
    zIndex: 10,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    justifyContent: 'flex-start',
    boxSizing: 'border-box'
  }}>
    <div style={{ marginBottom: '10px' }}>
      Status: <strong>{status}</strong>
    </div>

    <input
      type="text"
      placeholder="Start (lat,lon)"
      value={start}
      onChange={(e) => setStart(e.target.value)}
      style={inputStyle}
    />

    <input
      type="text"
      placeholder="End (lat,lon)"
      value={end}
      onChange={(e) => setEnd(e.target.value)}
      style={inputStyle}
    />

    <button
      onClick={startNavigation}
      style={{ ...buttonStyle, marginTop: '10px' }}
      disabled={status === 'Connecting...'}
    >
      {status === 'Path is Mapping...' ? 'Update Route' : 'Start Navigation'}
    </button>

    {/* Total Distance Box */}
    <div
      style={{
        marginTop: '40px',
        fontSize: '16px',
        padding: '15px',
        borderRadius: '10px',
        border: '1px solid rgba(255, 255, 255, 0.3)',
        background: 'rgba(255, 255, 255, 0.07)',
        width: '88%',
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
        color: '#fff',
        textAlign: 'center'
      }}
    >
      Total Distance: <strong>{distance} KM</strong>
    </div>
  </div>
</div>


  

  );
}

const inputStyle = {
  width: '93%',
  marginBottom: '10px',
  padding: '10px',
  borderRadius: '8px',
  border: '1px solid rgba(255, 255, 255, 0.3)',
  background: 'rgba(255, 255, 255, 0.1)',
  color: '#fff',
  outline: 'none',
};

const buttonStyle = {
  width: '100%',
  padding: '12px',
  backgroundColor: 'rgba(14, 25, 229, 0.5)',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  cursor: 'pointer',
  fontWeight: 'bold',
  transition: '0.3s ease-in-out',
};

export default App;