const cities = [
  { name: 'New York', country: 'USA', lat: 40.7128, lon: -74.0060 },
  { name: 'London', country: 'UK', lat: 51.5074, lon: -0.1278 },
  { name: 'Tokyo', country: 'JPN', lat: 35.6762, lon: 139.6503 },
  { name: 'Mumbai', country: 'IND', lat: 19.0760, lon: 72.8777 },
  { name: 'Beijing', country: 'CHN', lat: 39.9042, lon: 116.4074 },
  { name: 'Sydney', country: 'AUS', lat: -33.8688, lon: 151.2093 }
];

const gridContainer = document.getElementById('city-grid');
const lastUpdatedEl = document.getElementById('last-updated');
const charts = {}; // Store chart instances

async function fetchAirQualityData(city) {
  // Hit our local FastAPI server!
  const url = `http://127.0.0.1:8080/api/forecast?lat=${city.lat}&lon=${city.lon}`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Network response was not ok');
    const data = await response.json();
    return { ...city, payload: data };
  } catch (error) {
    console.error(`Error fetching data for ${city.name}:`, error);
    return null;
  }
}

function getAqiStatus(aqi) {
  if (aqi <= 50) return { label: 'Good', className: 'status-good', cardClass: 'card-good', color: '#10B981' };
  if (aqi <= 100) return { label: 'Moderate', className: 'status-fair', cardClass: 'card-fair', color: '#FBBF24' };
  if (aqi <= 150) return { label: 'Sensitive', className: 'status-moderate', cardClass: 'card-moderate', color: '#F97316' };
  if (aqi <= 200) return { label: 'Unhealthy', className: 'status-poor', cardClass: 'card-poor', color: '#EF4444' };
  if (aqi <= 300) return { label: 'V. Unhealthy', className: 'status-very-poor', cardClass: 'card-very-poor', color: '#8B5CF6' };
  return { label: 'Hazardous', className: 'status-terrible', cardClass: 'card-terrible', color: '#7F1D1D' };
}

function createCityCard(data, index) {
  if (!data || !data.payload || data.payload.error) return '';
  
  const current = data.payload.current;
  const aqi = current.us_aqi || 0;
  const pm25 = current.pm2_5 || 0;
  const pm10 = current.pm10 || 0;
  const no2 = current.no2 || 0;
  
  const status = getAqiStatus(aqi);
  const chartId = `chart-${index}`;
  
  return `
    <div class="city-card ${status.cardClass}">
      <div class="city-header">
        <h2 class="city-name">${data.name}</h2>
        <span class="country-code">${data.country}</span>
      </div>
      <div class="aqi-display">
        <div class="aqi-value ${status.className}">${Math.round(aqi)}</div>
        <div class="aqi-label ${status.className}">AQI</div>
      </div>
      <div class="aqi-status ${status.className}">${status.label} Air Quality</div>
      
      <div class="metrics-grid">
        <div class="metric">
          <span class="metric-label">PM 2.5</span>
          <span class="metric-value">${Math.round(pm25)} <span style="font-size:0.8rem;opacity:0.7;font-weight:400;">μg/m³</span></span>
        </div>
        <div class="metric">
          <span class="metric-label">PM 10</span>
          <span class="metric-value">${Math.round(pm10)} <span style="font-size:0.8rem;opacity:0.7;font-weight:400;">μg/m³</span></span>
        </div>
        <div class="metric">
          <span class="metric-label">NO2</span>
          <span class="metric-value">${Math.round(no2)} <span style="font-size:0.8rem;opacity:0.7;font-weight:400;">μg/m³</span></span>
        </div>
      </div>
      
      <div class="forecast-container" style="margin-top: 1.5rem; height: 120px; border-top: 1px solid var(--glass-border); padding-top: 1rem;">
        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem; text-transform: uppercase;">24H Forecast Model</div>
        <div style="height: 90px; width: 100%;">
            <canvas id="${chartId}"></canvas>
        </div>
      </div>
    </div>
  `;
}

function renderChart(canvasId, forecast, currentColor) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  
  const labels = forecast.map(f => {
    const d = new Date(f.time);
    return d.getHours() + ':00'; // formatted hour
  });
  
  const dataPoints = forecast.map(f => f.predicted_aqi);
  
  if(charts[canvasId]) {
      charts[canvasId].destroy();
  }

  charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Predicted AQI',
        data: dataPoints,
        borderColor: currentColor,
        backgroundColor: currentColor + '20',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
                title: function(context) { return 'Time: ' + context[0].label; }
            }
        }
      },
      scales: {
        x: { 
          display: true, 
          ticks: { maxTicksLimit: 6, color: 'rgba(255,255,255,0.5)', font: {size: 10} },
          grid: { display: false }
        },
        y: { 
          display: true,
          ticks: { maxTicksLimit: 5, color: 'rgba(255,255,255,0.5)', font: {size: 10} },
          grid: { color: 'rgba(255,255,255,0.05)' }
        }
      }
    }
  });
}

async function renderDashboard() {
  gridContainer.innerHTML = '<div class="loading">Loading AI Predictions...</div>';
  
  try {
    const promises = cities.map(city => fetchAirQualityData(city));
    const results = await Promise.all(promises);
    
    gridContainer.innerHTML = '';
    
    results.forEach((data, index) => {
      if (data && data.payload && !data.payload.error) {
        gridContainer.innerHTML += createCityCard(data, index);
      }
    });

    results.forEach((data, index) => {
        if (data && data.payload && !data.payload.error) {
           const currentAqi = data.payload.current.us_aqi;
           const colors = getAqiStatus(currentAqi);
           renderChart(`chart-${index}`, data.payload.forecast, colors.color);
        }
    });

    const now = new Date();
    lastUpdatedEl.textContent = `Last updated: ${now.toLocaleTimeString()}`;
  } catch (err) {
    gridContainer.innerHTML = `<div class="loading" style="color:var(--aqi-poor);">Failed to load ML data. Is Python backend running?</div>`;
  }
}

renderDashboard();
setInterval(renderDashboard, 300000);
