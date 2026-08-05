import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import axios from 'axios'
import {
  MapPin, School, Building2, TreePine, AlertTriangle,
  ChevronDown, Layers, Filter, Download, Search,
  TrendingUp, Droplets, Calendar, Activity, X,
  Eye, EyeOff, Info, ExternalLink, Zap, Shield,
  Navigation, AlertCircle, CheckCircle, BarChart3,
  Radio, Wind, Thermometer, Clock, Bell, FileText,
  Database, FlaskConical, Map, ChevronRight,
  User, MessageCircle, Tractor, LogIn
} from 'lucide-react'
import './App.css'
import FarmerPortal from './FarmerPortal'
import AIAssistant from './AIAssistant'

const API_URL = 'http://localhost:8001/api'
const WS_URL = 'ws://localhost:8001/api/ws/sprays'

function App() {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const wsRef = useRef(null)
  const sprayMarkersRef = useRef({})

  const [activeTab, setActiveTab] = useState('dashboard')
  const [years, setYears] = useState([])
  const [selectedYear, setSelectedYear] = useState(2023)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showSchools, setShowSchools] = useState(true)
  const [showHospitals, setShowHospitals] = useState(true)
  const [showSpraySites, setShowSpraySites] = useState(true)
  const [atRiskLocations, setAtRiskLocations] = useState([])
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [topCounties, setTopCounties] = useState([])

  // Real-time state
  const [connected, setConnected] = useState(false)
  const [liveSprayEvents, setLiveSprayEvents] = useState([])
  const [notifications, setNotifications] = useState([])
  const [spraySites, setSpraySites] = useState([])

  // Research state
  const [researchData, setResearchData] = useState(null)
  const [chemicals, setChemicals] = useState([])

  // Spray History state (REAL DATA with actual dates)
  const [selectedCounty, setSelectedCounty] = useState('KERN')
  const [sprayHistory, setSprayHistory] = useState(null)
  const [peakDays, setPeakDays] = useState([])
  const [weatherData, setWeatherData] = useState(null)

  // Farmer Portal & AI Assistant
  const [showFarmerPortal, setShowFarmerPortal] = useState(false)
  const [showAIAssistant, setShowAIAssistant] = useState(false)

  // Connect to WebSocket for real-time updates
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    wsRef.current = new WebSocket(WS_URL)

    wsRef.current.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'connection_established') {
        setLiveSprayEvents(data.recent_events || [])
      }

      if (data.type === 'new_spray_event') {
        const evt = data.event
        setLiveSprayEvents(prev => [evt, ...prev].slice(0, 50))

        // Add notification for high-risk events
        if (evt.alert_level === 'critical' || evt.alert_level === 'high') {
          const notification = {
            id: evt.id,
            message: `${evt.chemical} spray at ${evt.site_name}`,
            level: evt.alert_level,
            county: evt.county,
            time: new Date().toLocaleTimeString()
          }
          setNotifications(prev => [notification, ...prev].slice(0, 10))
        }

        // Add marker to map
        addSprayMarkerToMap(evt)
      }
    }

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }

    wsRef.current.onerror = (err) => {
      console.error('WebSocket error:', err)
    }
  }, [])

  const addSprayMarkerToMap = (evt) => {
    if (!map.current) return

    // Create animated marker element
    const el = document.createElement('div')
    el.className = `spray-marker ${evt.alert_level}`

    const inner = document.createElement('div')
    inner.className = 'spray-marker-inner'
    el.appendChild(inner)

    const pulse = document.createElement('div')
    pulse.className = 'spray-marker-pulse'
    el.appendChild(pulse)

    // Create popup content
    const popupHtml = `
      <div class="spray-popup">
        <div class="spray-popup-header ${evt.alert_level}">
          <span class="spray-status">LIVE SPRAY</span>
        </div>
        <div class="spray-popup-body">
          <div class="spray-site">${evt.site_name}</div>
          <div class="spray-chemical">${evt.chemical} (${evt.chemical_type})</div>
          <div class="spray-details">
            <span>${evt.lbs_applied} lbs</span>
            <span>${evt.acres_treated} acres</span>
          </div>
          <div class="spray-weather">
            <span>Wind: ${evt.weather.wind_speed_mph} mph</span>
            <span>Temp: ${evt.weather.temperature_f}°F</span>
          </div>
          ${evt.schools_in_drift_zone > 0 ? `<div class="spray-warning">⚠️ ${evt.schools_in_drift_zone} school(s) in drift zone</div>` : ''}
        </div>
      </div>
    `

    const marker = new maplibregl.Marker({ element: el })
      .setLngLat([evt.lon, evt.lat])
      .setPopup(new maplibregl.Popup({ offset: 25 }).setHTML(popupHtml))
      .addTo(map.current)

    sprayMarkersRef.current[evt.id] = marker

    // Remove marker after 5 minutes
    setTimeout(() => {
      marker.remove()
      delete sprayMarkersRef.current[evt.id]
    }, 300000)
  }

  // Load spray sites
  const loadSpraySites = async () => {
    try {
      const res = await axios.get(`${API_URL}/spray-events/sites`)
      setSpraySites(res.data.sites || [])

      // Add spray sites as a layer
      if (map.current?.getSource('spray-sites')) {
        const geojson = {
          type: 'FeatureCollection',
          features: res.data.sites.map(site => ({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [site.lon, site.lat] },
            properties: { name: site.name, county: site.county, crop: site.crop }
          }))
        }
        map.current.getSource('spray-sites').setData(geojson)
      }
    } catch (err) {
      console.error('Failed to load spray sites:', err)
    }
  }

  useEffect(() => {
    if (map.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          carto: {
            type: 'raster',
            tiles: ['https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
            tileSize: 256
          }
        },
        layers: [{ id: 'carto', type: 'raster', source: 'carto' }],
        glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf'
      },
      center: [-119.4179, 36.7783],
      zoom: 6
    })

    map.current.addControl(new maplibregl.NavigationControl(), 'bottom-right')

    map.current.on('load', () => {
      // County pesticide data
      map.current.addSource('counties', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      })

      // Sensitive locations
      map.current.addSource('locations', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      })

      // Spray sites
      map.current.addSource('spray-sites', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      })

      // Heatmap for pesticide intensity
      map.current.addLayer({
        id: 'pesticide-heat',
        type: 'heatmap',
        source: 'counties',
        paint: {
          'heatmap-weight': ['interpolate', ['linear'], ['get', 'total_lbs'], 0, 0, 100000000, 1],
          'heatmap-intensity': 0.6,
          'heatmap-color': [
            'interpolate', ['linear'], ['heatmap-density'],
            0, 'rgba(0,0,0,0)',
            0.2, 'rgba(254, 178, 76, 0.4)',
            0.4, 'rgba(253, 141, 60, 0.5)',
            0.6, 'rgba(252, 78, 42, 0.6)',
            0.8, 'rgba(227, 26, 28, 0.7)',
            1, 'rgba(189, 0, 38, 0.8)'
          ],
          'heatmap-radius': 50,
          'heatmap-opacity': 0.7
        }
      })

      // Pesticide county circles
      map.current.addLayer({
        id: 'county-circles',
        type: 'circle',
        source: 'counties',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'total_lbs'], 0, 12, 50000000, 35],
          'circle-color': [
            'interpolate', ['linear'], ['get', 'total_lbs'],
            0, '#f59e0b',
            20000000, '#f97316',
            40000000, '#ef4444',
            60000000, '#dc2626'
          ],
          'circle-opacity': 0.85,
          'circle-stroke-width': 2,
          'circle-stroke-color': 'rgba(255,255,255,0.4)'
        }
      })

      // At-risk pulsing rings
      map.current.addLayer({
        id: 'risk-rings',
        type: 'circle',
        source: 'counties',
        filter: ['>', ['get', 'total_lbs'], 30000000],
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'total_lbs'], 30000000, 40, 60000000, 55],
          'circle-color': 'transparent',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ef4444',
          'circle-stroke-opacity': 0.6
        }
      })

      // Spray site markers (agricultural fields)
      map.current.addLayer({
        id: 'spray-sites-layer',
        type: 'circle',
        source: 'spray-sites',
        paint: {
          'circle-radius': 6,
          'circle-color': '#22c55e',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
          'circle-opacity': 0.8
        }
      })

      // School markers
      map.current.addLayer({
        id: 'schools-layer',
        type: 'circle',
        source: 'locations',
        filter: ['==', ['get', 'category'], 'school'],
        paint: {
          'circle-radius': 8,
          'circle-color': '#3b82f6',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff'
        }
      })

      // Healthcare markers
      map.current.addLayer({
        id: 'hospitals-layer',
        type: 'circle',
        source: 'locations',
        filter: ['==', ['get', 'category'], 'healthcare'],
        paint: {
          'circle-radius': 8,
          'circle-color': '#ec4899',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff'
        }
      })

      setupInteractions()
      loadData()
      loadSpraySites()
      connectWebSocket()
      setLoading(false)
    })

    return () => {
      wsRef.current?.close()
    }
  }, [connectWebSocket])

  const setupInteractions = () => {
    const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 15 })

    // County hover tooltip
    map.current.on('mouseenter', 'county-circles', (e) => {
      map.current.getCanvas().style.cursor = 'pointer'
      const p = e.features[0].properties
      const lbs = Number(p.total_lbs)
      const risk = lbs > 30000000 ? 'HIGH' : lbs > 15000000 ? 'MEDIUM' : 'LOW'
      const riskClass = risk.toLowerCase()

      popup.setLngLat(e.lngLat).setHTML(`
        <div class="tooltip">
          <div class="tooltip-header">
            <span class="tooltip-icon pesticide">●</span>
            <span class="tooltip-title">Pesticide Zone</span>
          </div>
          <div class="tooltip-county">${p.county} County</div>
          <div class="tooltip-stats">
            <div><strong>${formatNumber(lbs)}</strong> lbs applied</div>
            <div><strong>${formatNumber(p.spray_count)}</strong> spray events</div>
          </div>
          <div class="tooltip-risk ${riskClass}">Risk: ${risk}</div>
        </div>
      `).addTo(map.current)
    })

    map.current.on('mouseleave', 'county-circles', () => {
      map.current.getCanvas().style.cursor = ''
      popup.remove()
    })

    // Spray site hover
    map.current.on('mouseenter', 'spray-sites-layer', (e) => {
      map.current.getCanvas().style.cursor = 'pointer'
      const p = e.features[0].properties

      popup.setLngLat(e.lngLat).setHTML(`
        <div class="tooltip spray-site">
          <div class="tooltip-header">
            <span class="tooltip-icon spray">●</span>
            <span class="tooltip-title">Agricultural Site</span>
          </div>
          <div class="tooltip-name">${p.name}</div>
          <div class="tooltip-detail">Crop: ${p.crop}</div>
          <div class="tooltip-detail">${p.county} County</div>
        </div>
      `).addTo(map.current)
    })

    map.current.on('mouseleave', 'spray-sites-layer', () => {
      map.current.getCanvas().style.cursor = ''
      popup.remove()
    })

    // School hover tooltip
    map.current.on('mouseenter', 'schools-layer', (e) => {
      map.current.getCanvas().style.cursor = 'pointer'
      const p = e.features[0].properties

      popup.setLngLat(e.lngLat).setHTML(`
        <div class="tooltip school">
          <div class="tooltip-header">
            <span class="tooltip-icon school">●</span>
            <span class="tooltip-title">School</span>
          </div>
          <div class="tooltip-name">${p.name}</div>
          <div class="tooltip-detail">${p.type.replace('_', ' ')}</div>
          <div class="tooltip-detail">${p.county} County</div>
        </div>
      `).addTo(map.current)
    })

    map.current.on('mouseleave', 'schools-layer', () => {
      map.current.getCanvas().style.cursor = ''
      popup.remove()
    })

    // Hospital hover
    map.current.on('mouseenter', 'hospitals-layer', (e) => {
      map.current.getCanvas().style.cursor = 'pointer'
      const p = e.features[0].properties

      popup.setLngLat(e.lngLat).setHTML(`
        <div class="tooltip hospital">
          <div class="tooltip-header">
            <span class="tooltip-icon hospital">●</span>
            <span class="tooltip-title">Healthcare</span>
          </div>
          <div class="tooltip-name">${p.name}</div>
          <div class="tooltip-detail">${p.county} County</div>
        </div>
      `).addTo(map.current)
    })

    map.current.on('mouseleave', 'hospitals-layer', () => {
      map.current.getCanvas().style.cursor = ''
      popup.remove()
    })

    // Click handlers
    map.current.on('click', 'schools-layer', (e) => {
      const p = e.features[0].properties
      const coords = e.features[0].geometry.coordinates
      setSelectedLocation({
        type: 'school',
        name: p.name,
        category: p.type,
        county: p.county,
        lat: coords[1],
        lon: coords[0]
      })
    })

    map.current.on('click', 'hospitals-layer', (e) => {
      const p = e.features[0].properties
      const coords = e.features[0].geometry.coordinates
      setSelectedLocation({
        type: 'healthcare',
        name: p.name,
        category: p.type,
        county: p.county,
        lat: coords[1],
        lon: coords[0]
      })
    })
  }

  const loadData = async () => {
    try {
      const [locRes, countiesRes] = await Promise.all([
        axios.get(`${API_URL}/locations`),
        axios.get(`${API_URL}/sprays/heatmap?year=2023`)
      ])

      if (map.current?.getSource('locations')) {
        map.current.getSource('locations').setData(locRes.data)
      }
      if (map.current?.getSource('counties')) {
        map.current.getSource('counties').setData(countiesRes.data)
        const sorted = countiesRes.data.features
          .sort((a, b) => b.properties.total_lbs - a.properties.total_lbs)
          .slice(0, 5)
          .map(f => ({ name: f.properties.county, lbs: f.properties.total_lbs }))
        setTopCounties(sorted)
      }
    } catch (err) {
      console.error('Failed to load data:', err)
    }
  }

  // Load research data
  const loadResearchData = async () => {
    try {
      const [chemRes, trendsRes] = await Promise.all([
        axios.get(`${API_URL}/research/chemicals?limit=20`),
        axios.get(`${API_URL}/research/trends`)
      ])
      setChemicals(chemRes.data.chemicals || [])
      setResearchData(trendsRes.data)
    } catch (err) {
      console.error('Failed to load research data:', err)
    }
  }

  useEffect(() => {
    if (activeTab === 'research' && !researchData) {
      loadResearchData()
    }
  }, [activeTab])

  // Load spray history (REAL DATA with actual dates)
  const loadSprayHistory = async (county) => {
    try {
      const [peakRes, timelineRes] = await Promise.all([
        axios.get(`${API_URL}/history/peak-days/${county}?year=${selectedYear}&top_n=10`),
        axios.get(`${API_URL}/history/timeline/${county}?year=${selectedYear}`)
      ])
      setPeakDays(peakRes.data.peak_days || [])
      setSprayHistory(timelineRes.data)
    } catch (err) {
      console.error('Failed to load spray history:', err)
    }
  }

  // Load weather/drift data
  const loadWeatherData = async (lat, lon) => {
    try {
      const res = await axios.get(`${API_URL}/weather/drift-risk?lat=${lat}&lon=${lon}&chemical_toxicity=high`)
      setWeatherData(res.data)
    } catch (err) {
      console.error('Failed to load weather:', err)
    }
  }

  useEffect(() => {
    if (activeTab === 'history' && selectedCounty) {
      loadSprayHistory(selectedCounty)
      // Load weather for county center (Kern = Bakersfield)
      const countyCoords = {
        KERN: [35.3733, -119.0187],
        FRESNO: [36.7378, -119.7871],
        TULARE: [36.2078, -119.3472],
        MONTEREY: [36.6777, -121.6555],
        IMPERIAL: [32.7920, -115.5630]
      }
      const coords = countyCoords[selectedCounty] || [36.7783, -119.4179]
      loadWeatherData(coords[0], coords[1])
    }
  }, [activeTab, selectedCounty, selectedYear])

  useEffect(() => {
    if (!map.current?.getLayer('schools-layer')) return
    map.current.setLayoutProperty('schools-layer', 'visibility', showSchools ? 'visible' : 'none')
  }, [showSchools])

  useEffect(() => {
    if (!map.current?.getLayer('hospitals-layer')) return
    map.current.setLayoutProperty('hospitals-layer', 'visibility', showHospitals ? 'visible' : 'none')
  }, [showHospitals])

  useEffect(() => {
    if (!map.current?.getLayer('spray-sites-layer')) return
    map.current.setLayoutProperty('spray-sites-layer', 'visibility', showSpraySites ? 'visible' : 'none')
  }, [showSpraySites])

  useEffect(() => {
    if (!map.current || !selectedYear) return

    axios.get(`${API_URL}/sprays/heatmap?year=${selectedYear}`)
      .then(res => {
        map.current?.getSource('counties')?.setData(res.data)
        const sorted = res.data.features
          .sort((a, b) => b.properties.total_lbs - a.properties.total_lbs)
          .slice(0, 5)
          .map(f => ({ name: f.properties.county, lbs: f.properties.total_lbs }))
        setTopCounties(sorted)
      })
      .catch(console.error)

    axios.get(`${API_URL}/locations/at-risk?year=${selectedYear}`)
      .then(res => setAtRiskLocations(res.data.locations?.slice(0, 10) || []))
      .catch(console.error)
  }, [selectedYear])

  useEffect(() => {
    axios.get(`${API_URL}/sprays/years`).then(res => setYears(res.data)).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedYear) return
    axios.get(`${API_URL}/sprays/stats?year=${selectedYear}`).then(res => setStats(res.data)).catch(console.error)
  }, [selectedYear])

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num?.toFixed(0) || '0'
  }

  const zoomTo = (lat, lon) => {
    map.current?.flyTo({ center: [lon, lat], zoom: 10 })
  }

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const schoolCount = atRiskLocations.filter(l => l.category === 'school').length
  const healthcareCount = atRiskLocations.filter(l => l.category === 'healthcare').length
  const highestCounty = topCounties[0]?.name || 'N/A'

  // Render Dashboard Tab
  const renderDashboard = () => (
    <>
      {/* Left Sidebar */}
      <aside className="sidebar">
        {/* Connection Status */}
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          <Radio size={14} />
          {connected ? 'Live Updates Active' : 'Connecting...'}
        </div>

        {/* Year Filter */}
        <div className="card">
          <div className="card-header"><Calendar size={16} /> Time Period</div>
          <div className="select-wrapper">
            <select value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
              {years.map(y => <option key={y.year} value={y.year}>{y.year}</option>)}
            </select>
            <ChevronDown size={16} className="select-icon" />
          </div>
        </div>

        {/* Map Layers */}
        <div className="card">
          <div className="card-header"><Layers size={16} /> Map Layers</div>
          <div className="layer-toggles">
            <button className={`layer-btn ${showSchools ? 'active' : ''}`} onClick={() => setShowSchools(!showSchools)}>
              <School size={16} /> Schools {showSchools ? <Eye size={14} /> : <EyeOff size={14} />}
            </button>
            <button className={`layer-btn ${showHospitals ? 'active' : ''}`} onClick={() => setShowHospitals(!showHospitals)}>
              <Building2 size={16} /> Healthcare {showHospitals ? <Eye size={14} /> : <EyeOff size={14} />}
            </button>
            <button className={`layer-btn ${showSpraySites ? 'active' : ''}`} onClick={() => setShowSpraySites(!showSpraySites)}>
              <MapPin size={16} /> Spray Sites {showSpraySites ? <Eye size={14} /> : <EyeOff size={14} />}
            </button>
          </div>
        </div>

        {/* Live Spray Events */}
        {liveSprayEvents.length > 0 && (
          <div className="card live-events-card">
            <div className="card-header"><Radio size={16} className="pulse" /> Live Spray Events</div>
            <div className="live-events-list">
              {liveSprayEvents.slice(0, 5).map((evt) => (
                <motion.div
                  key={evt.id}
                  className={`live-event ${evt.alert_level}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  onClick={() => zoomTo(evt.lat, evt.lon)}
                >
                  <div className="live-event-header">
                    <span className={`live-badge ${evt.alert_level}`}>{evt.alert_level.toUpperCase()}</span>
                    {evt.verification_status === 'farmer_reported' && (
                      <span className="verification-badge farmer-reported" title="Farmer-reported, pending verification">FARMER REPORTED</span>
                    )}
                    {evt.source === 'pur_official' && (
                      <span className="verification-badge verified" title="Verified against official PUR records">VERIFIED</span>
                    )}
                    <span className="live-time">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="live-site">{evt.site_name}</div>
                  <div className="live-chemical">{evt.chemical} • {evt.lbs_applied} lbs</div>
                  <div className="live-weather">
                    <Wind size={12} /> {evt.weather.wind_speed_mph} mph
                    <Thermometer size={12} /> {evt.weather.temperature_f}°F
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* At-Risk Locations */}
        <div className="card alert-card">
          <div className="card-header"><AlertTriangle size={16} /> At-Risk Locations</div>
          <div className="risk-list">
            {atRiskLocations.slice(0, 6).map((loc, i) => (
              <motion.div key={i} className="risk-item" onClick={() => zoomTo(loc.lat, loc.lon)} whileHover={{ x: 4 }}>
                <div className={`risk-marker ${loc.category}`}>
                  {loc.category === 'school' ? <School size={14} /> : <Building2 size={14} />}
                </div>
                <div className="risk-info">
                  <div className="risk-name">{loc.name}</div>
                  <div className="risk-meta">{formatNumber(loc.county_pesticide_lbs)} lbs • {loc.county}</div>
                </div>
                <span className={`risk-badge ${loc.risk_level}`}>
                  {loc.risk_level === 'very_high' ? 'HIGH' : loc.risk_level.toUpperCase()}
                </span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Mini Bar Chart */}
        <div className="card">
          <div className="card-header"><BarChart3 size={16} /> Risk by County</div>
          <div className="mini-chart">
            {topCounties.map((c, i) => (
              <div key={i} className="chart-row">
                <span className="chart-label">{c.name}</span>
                <div className="chart-bar-wrapper">
                  <motion.div
                    className="chart-bar"
                    initial={{ width: 0 }}
                    animate={{ width: `${(c.lbs / topCounties[0].lbs) * 100}%` }}
                    transition={{ duration: 0.5, delay: i * 0.1 }}
                  />
                </div>
                <span className="chart-value">{formatNumber(c.lbs)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Insight */}
        <div className="card insight-card">
          <div className="card-header"><Zap size={16} /> AI Risk Insight</div>
          <p className="insight-text">
            <strong>Fresno County</strong> shows the highest overlap between pesticide use and nearby schools.
            Several schools are located within high-exposure zones, suggesting this area should be
            <strong> prioritized for further review</strong>.
          </p>
        </div>
      </aside>

      {/* Map */}
      <div className="map-wrapper">
        <div className="map-container" ref={mapContainer} />

        {/* Notifications */}
        <div className="notifications">
          <AnimatePresence>
            {notifications.map((n) => (
              <motion.div
                key={n.id}
                className={`notification ${n.level}`}
                initial={{ x: 300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 300, opacity: 0 }}
              >
                <div className="notification-content">
                  <AlertTriangle size={16} />
                  <div>
                    <div className="notification-msg">{n.message}</div>
                    <div className="notification-meta">{n.county} County • {n.time}</div>
                  </div>
                </div>
                <button onClick={() => dismissNotification(n.id)}><X size={14} /></button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Legend */}
        <div className="map-legend">
          <div className="legend-title">Map Legend</div>
          <div className="legend-items">
            <div className="legend-item"><span className="legend-dot orange" /> Pesticide Usage</div>
            <div className="legend-item"><span className="legend-dot red-ring" /> High-Risk Zone</div>
            <div className="legend-item"><span className="legend-dot green" /> Spray Sites</div>
            <div className="legend-item"><span className="legend-dot blue" /> Schools</div>
            <div className="legend-item"><span className="legend-dot pink" /> Healthcare</div>
          </div>
          <div className="legend-scale">
            <div className="legend-bar" />
            <div className="legend-labels"><span>Low</span><span>High</span></div>
          </div>
        </div>

        {/* Map controls */}
        <div className="map-controls">
          <button className="map-btn" onClick={() => map.current?.flyTo({ center: [-119.4179, 36.7783], zoom: 6 })}>
            <Navigation size={18} />
          </button>
        </div>
      </div>

      {/* Right Details Panel */}
      <AnimatePresence>
        {selectedLocation && (
          <motion.aside
            className="detail-panel"
            initial={{ x: 320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 320, opacity: 0 }}
            transition={{ type: 'spring', damping: 25 }}
          >
            <button className="panel-close" onClick={() => setSelectedLocation(null)}><X size={18} /></button>

            <div className={`detail-icon ${selectedLocation.type}`}>
              {selectedLocation.type === 'school' ? <School size={24} /> : <Building2 size={24} />}
            </div>

            <h2 className="detail-title">{selectedLocation.name}</h2>
            <p className="detail-subtitle">{selectedLocation.category?.replace('_', ' ')} • {selectedLocation.county} County</p>

            <div className="detail-coords">
              <span>Lat: {selectedLocation.lat?.toFixed(4)}</span>
              <span>Lon: {selectedLocation.lon?.toFixed(4)}</span>
            </div>

            <div className="detail-action">
              <Shield size={16} />
              <div>
                <strong>Monitoring Status</strong>
                <p>This location is being monitored for pesticide drift exposure.</p>
              </div>
            </div>

            <button className="detail-btn" onClick={() => {
              setActiveTab('alerts')
              setSelectedLocation(null)
            }}>
              Set Up Alerts <Bell size={14} />
            </button>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  )

  // Render Research Tab
  const renderResearch = () => (
    <div className="research-content">
      <div className="research-sidebar">
        <div className="card">
          <div className="card-header"><FlaskConical size={16} /> Research Tools</div>
          <div className="research-tools">
            <button className="research-tool-btn">
              <Database size={18} />
              <span>Export Data</span>
              <ChevronRight size={14} />
            </button>
            <button className="research-tool-btn">
              <TrendingUp size={18} />
              <span>Trend Analysis</span>
              <ChevronRight size={14} />
            </button>
            <button className="research-tool-btn">
              <Map size={18} />
              <span>Spatial Analysis</span>
              <ChevronRight size={14} />
            </button>
            <button className="research-tool-btn">
              <FileText size={18} />
              <span>Generate Report</span>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><Calendar size={16} /> Data Coverage</div>
          <div className="data-coverage">
            <div className="coverage-item">
              <span>Years</span>
              <strong>2014 - 2023</strong>
            </div>
            <div className="coverage-item">
              <span>Records</span>
              <strong>55M+</strong>
            </div>
            <div className="coverage-item">
              <span>Counties</span>
              <strong>58</strong>
            </div>
            <div className="coverage-item">
              <span>Chemicals</span>
              <strong>1,000+</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="research-main">
        <div className="research-header">
          <h2>Research Dashboard</h2>
          <p>Access 10 years of California Pesticide Use Report data for academic research.</p>
        </div>

        <div className="research-grid">
          <div className="research-card">
            <h3><Droplets size={18} /> Top Chemicals by Volume</h3>
            <div className="chemical-list">
              {chemicals.slice(0, 10).map((chem, i) => (
                <div key={i} className="chemical-item">
                  <span className="chemical-rank">#{i + 1}</span>
                  <span className="chemical-name">{chem.chemical_name}</span>
                  <span className="chemical-amount">{formatNumber(chem.total_lbs)} lbs</span>
                </div>
              ))}
            </div>
          </div>

          <div className="research-card">
            <h3><BarChart3 size={18} /> Usage Trends</h3>
            <div className="trends-chart">
              {researchData?.yearly_totals?.slice(-5).map((yr, i) => (
                <div key={i} className="trend-bar-row">
                  <span className="trend-year">{yr.year}</span>
                  <div className="trend-bar-wrapper">
                    <div
                      className="trend-bar"
                      style={{ width: `${(yr.total_lbs / (researchData.yearly_totals[0]?.total_lbs || 1)) * 100}%` }}
                    />
                  </div>
                  <span className="trend-value">{formatNumber(yr.total_lbs)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="research-card full-width">
            <h3><FileText size={18} /> API Documentation</h3>
            <div className="api-docs">
              <p>Access our REST API for programmatic data retrieval:</p>
              <div className="api-endpoints">
                <code>GET /api/research/export?year=2023&county=FRESNO&format=csv</code>
                <code>GET /api/research/chemicals?limit=100</code>
                <code>GET /api/research/trends</code>
                <code>GET /api/research/county/{'{county}'}</code>
              </div>
            </div>
          </div>

          {/* Data Sources & Methodology */}
          <div className="research-card full-width methodology">
            <h3><Info size={18} /> Data Sources & Methodology</h3>
            <div className="methodology-content">
              <div className="methodology-grid">
                <div className="method-item">
                  <span className="method-label">Data Source</span>
                  <span className="method-value">California Department of Pesticide Regulation (CA DPR) Pesticide Use Reports (PUR)</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Years Covered</span>
                  <span className="method-value">2014 - 2023 (10 years)</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Unit of Measurement</span>
                  <span className="method-value">Pounds (lbs) of active ingredient applied</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Geographic Scope</span>
                  <span className="method-value">All 58 California counties</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Reporting Basis</span>
                  <span className="method-value">Mandatory reporting by licensed applicators (California Food & Agricultural Code §12979)</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Risk Classification</span>
                  <span className="method-value">Based on total lbs applied per county. High = &gt;30M lbs, Medium = 15-30M lbs, Low = &lt;15M lbs. Does not currently weight by toxicity.</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Drift Estimation</span>
                  <span className="method-value">Gaussian Plume Model with Pasquill-Gifford atmospheric stability classification</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Limitations</span>
                  <span className="method-value">PUR data has 12-18 month reporting lag. GeoSync does not replace official state reporting systems.</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Farmer Portal</span>
                  <span className="method-value">Optional farmer-submitted reports are labeled as "farmer-reported" until verified against official records. Not intended to replace CalAgPermits or county reporting requirements.</span>
                </div>
                <div className="method-item">
                  <span className="method-label">Data Integration</span>
                  <span className="method-value">GeoSync combines official PUR datasets with optional farmer-reported updates to provide faster, more localized monitoring while preserving data credibility through verification labeling.</span>
                </div>
              </div>
              <div className="methodology-citation">
                <p><strong>Citation:</strong> California Department of Pesticide Regulation. Pesticide Use Reporting (PUR) Database. Available at: <a href="https://www.cdpr.ca.gov/docs/pur/purmain.htm" target="_blank" rel="noopener noreferrer">cdpr.ca.gov/docs/pur/purmain.htm</a></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  // Render Alerts Tab
  const renderAlerts = () => (
    <div className="alerts-content">
      <div className="alerts-sidebar">
        <div className="card">
          <div className="card-header"><Bell size={16} /> Alert Settings</div>
          <div className="alert-settings">
            <label className="alert-setting">
              <input type="checkbox" defaultChecked />
              <span>High-risk spray events</span>
            </label>
            <label className="alert-setting">
              <input type="checkbox" defaultChecked />
              <span>Schools in drift zone</span>
            </label>
            <label className="alert-setting">
              <input type="checkbox" />
              <span>All spray events</span>
            </label>
            <label className="alert-setting">
              <input type="checkbox" defaultChecked />
              <span>High-toxicity chemicals</span>
            </label>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><MapPin size={16} /> Monitored Locations</div>
          <div className="monitored-list">
            <div className="monitored-item">
              <School size={16} />
              <span>Fresno High School</span>
            </div>
            <div className="monitored-item">
              <School size={16} />
              <span>Roosevelt High School</span>
            </div>
            <div className="monitored-item">
              <Building2 size={16} />
              <span>Community Regional Medical</span>
            </div>
          </div>
          <button className="add-location-btn">+ Add Location</button>
        </div>
      </div>

      <div className="alerts-main">
        <div className="alerts-header">
          <h2>Alert Center</h2>
          <div className="alert-stats">
            <div className="alert-stat critical">{notifications.filter(n => n.level === 'critical').length} Critical</div>
            <div className="alert-stat high">{notifications.filter(n => n.level === 'high').length} High</div>
            <div className="alert-stat medium">{notifications.filter(n => n.level === 'medium').length} Medium</div>
          </div>
        </div>

        <div className="alerts-list">
          {liveSprayEvents.filter(e => e.alert_level !== 'low').map((evt) => (
            <motion.div
              key={evt.id}
              className={`alert-item ${evt.alert_level}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className={`alert-badge ${evt.alert_level}`}>
                <AlertTriangle size={16} />
                {evt.alert_level.toUpperCase()}
              </div>
              <div className="alert-content">
                <div className="alert-title">{evt.chemical} spray detected at {evt.site_name}</div>
                <div className="alert-details">
                  <span>{evt.county} County</span>
                  <span>{evt.lbs_applied} lbs applied</span>
                  <span>Wind: {evt.weather.wind_speed_mph} mph</span>
                </div>
                {evt.schools_in_drift_zone > 0 && (
                  <div className="alert-warning">
                    <AlertCircle size={14} />
                    {evt.schools_in_drift_zone} school(s) within {evt.drift_zone.distance_km} km drift zone
                  </div>
                )}
              </div>
              <div className="alert-time">
                <Clock size={14} />
                {new Date(evt.timestamp).toLocaleTimeString()}
              </div>
            </motion.div>
          ))}

          {liveSprayEvents.filter(e => e.alert_level !== 'low').length === 0 && (
            <div className="no-alerts">
              <CheckCircle size={48} />
              <h3>No Active Alerts</h3>
              <p>All systems normal. You'll be notified when high-risk spray events occur.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )

  // Render Spray History Tab - REAL DATA for parents
  const renderHistory = () => (
    <div className="history-content">
      <div className="history-sidebar">
        <div className="card">
          <div className="card-header"><MapPin size={16} /> Select County</div>
          <div className="select-wrapper">
            <select value={selectedCounty} onChange={(e) => setSelectedCounty(e.target.value)}>
              <option value="KERN">Kern County</option>
              <option value="FRESNO">Fresno County</option>
              <option value="TULARE">Tulare County</option>
              <option value="MONTEREY">Monterey County</option>
              <option value="IMPERIAL">Imperial County</option>
            </select>
            <ChevronDown size={16} className="select-icon" />
          </div>
        </div>

        <div className="card">
          <div className="card-header"><Calendar size={16} /> Year</div>
          <div className="select-wrapper">
            <select value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
              {years.map(y => <option key={y.year} value={y.year}>{y.year}</option>)}
            </select>
            <ChevronDown size={16} className="select-icon" />
          </div>
        </div>

        {weatherData && (
          <div className="card weather-card">
            <div className="card-header"><Wind size={16} /> Current Drift Risk</div>
            <div className={`drift-risk-indicator ${weatherData.risk_assessment?.risk_level}`}>
              <AlertCircle size={20} />
              <span>{weatherData.risk_assessment?.risk_level?.toUpperCase()}</span>
            </div>
            <div className="weather-details">
              <div className="weather-item">
                <Wind size={14} />
                <span>{weatherData.weather?.wind_speed_mph} mph {weatherData.weather?.wind_direction_cardinal}</span>
              </div>
              <div className="weather-item">
                <Thermometer size={14} />
                <span>{weatherData.weather?.temperature_f}°F</span>
              </div>
              <div className="weather-item">
                <Droplets size={14} />
                <span>{weatherData.weather?.humidity_pct}% humidity</span>
              </div>
            </div>
            <div className="drift-distance">
              Max drift: <strong>{weatherData.drift_estimate?.max_drift_distance_miles} miles</strong>
            </div>
            <p className="drift-recommendation">{weatherData.risk_assessment?.recommendation}</p>
          </div>
        )}

        {sprayHistory && (
          <div className="card">
            <div className="card-header"><BarChart3 size={16} /> Monthly Summary</div>
            <div className="monthly-summary">
              {Object.entries(sprayHistory.monthly_summary || {}).slice(0, 6).map(([month, data]) => (
                <div key={month} className="month-row">
                  <span className="month-name">{month.slice(0, 3)}</span>
                  <div className="month-bar-wrapper">
                    <div
                      className="month-bar"
                      style={{
                        width: `${Math.min((data.total_lbs / 10000000) * 100, 100)}%`
                      }}
                    />
                  </div>
                  <span className="month-value">{formatNumber(data.total_lbs)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="history-main">
        <div className="history-header">
          <h2>Spray History - {selectedCounty} County</h2>
          <p>Actual spray dates from California Pesticide Use Reports. This is <strong>official data</strong> that parents can trust.</p>
        </div>

        <div className="peak-days-section">
          <h3><AlertTriangle size={18} /> Highest Spray Days in {selectedYear}</h3>
          <p className="section-desc">These are the days with the most pesticide application. If you or your children were outdoors on these dates, you may have had elevated exposure.</p>

          <div className="peak-days-grid">
            {peakDays.map((day, i) => (
              <motion.div
                key={day.date}
                className={`peak-day-card ${i < 3 ? 'high-risk' : ''}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <div className="peak-day-rank">#{day.rank}</div>
                <div className="peak-day-content">
                  <div className="peak-day-date">{day.date_formatted}</div>
                  <div className="peak-day-stats">
                    <span className="peak-lbs">{formatNumber(day.total_lbs)} lbs</span>
                    <span className="peak-events">{day.spray_events.toLocaleString()} spray events</span>
                    <span className="peak-chemicals">{day.unique_chemicals} chemicals</span>
                  </div>
                  <div className="peak-day-chemicals">
                    {day.chemicals?.slice(0, 5).filter(c => c).map((chem, j) => (
                      <span key={j} className="chemical-tag">{chem}</span>
                    ))}
                    {day.chemicals?.length > 5 && (
                      <span className="chemical-more">+{day.chemicals.length - 5} more</span>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="data-source-info">
          <Info size={16} />
          <div>
            <strong>Data Source</strong>
            <p>California Department of Pesticide Regulation - Pesticide Use Reports (PUR).
               Data is reported annually by agricultural applicators as required by law.</p>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="app">
      <div className="bg-gradient" />
      <div className="bg-grid" />

      {/* Header */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon"><Zap size={20} /></div>
          <span className="logo-text">GeoSync</span>
        </div>

        <nav className="nav">
          <button className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <Activity size={16} /> Dashboard
          </button>
          <button className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
            <Calendar size={16} /> Spray History
          </button>
          <button className={`nav-btn ${activeTab === 'research' ? 'active' : ''}`} onClick={() => setActiveTab('research')}>
            <TrendingUp size={16} /> Research
          </button>
          <button className={`nav-btn ${activeTab === 'alerts' ? 'active' : ''}`} onClick={() => setActiveTab('alerts')}>
            <AlertTriangle size={16} /> Alerts
            {notifications.length > 0 && <span className="nav-badge">{notifications.length}</span>}
          </button>
        </nav>

        <div className="header-actions">
          <button className="btn-ai" onClick={() => setShowAIAssistant(true)}>
            <MessageCircle size={16} /> AI Assistant
          </button>
          <button className="btn-farmer" onClick={() => setShowFarmerPortal(true)}>
            <Tractor size={16} /> Farmer Portal
          </button>
          <button className="btn-secondary"><Download size={16} /> Export</button>
        </div>
      </header>

      {/* Summary Cards */}
      <div className="summary-bar">
        <motion.div className="summary-card has-tooltip" whileHover={{ y: -2 }}>
          <div className="summary-icon orange"><Droplets size={20} /></div>
          <div className="summary-content">
            <span className="summary-value">{stats ? formatNumber(stats.total_lbs_applied) : '—'} <span className="summary-unit">lbs</span></span>
            <span className="summary-label">Total Pesticide Applied</span>
          </div>
          <button className="info-toggle" title="Click for details"><Info size={10} /></button>
          <div className="card-tooltip">Pounds of active ingredient applied, as reported to CA DPR ({selectedYear})</div>
        </motion.div>

        <motion.div className="summary-card has-tooltip" whileHover={{ y: -2 }}>
          <div className="summary-icon blue"><School size={20} /></div>
          <div className="summary-content">
            <span className="summary-value">{schoolCount}</span>
            <span className="summary-label">Schools in High-Use Counties</span>
          </div>
          <button className="info-toggle" title="Click for details"><Info size={10} /></button>
          <div className="card-tooltip">Schools located in counties with &gt;30M lbs pesticide use annually</div>
        </motion.div>

        <motion.div className="summary-card has-tooltip" whileHover={{ y: -2 }}>
          <div className="summary-icon pink"><Building2 size={20} /></div>
          <div className="summary-content">
            <span className="summary-value">{healthcareCount}</span>
            <span className="summary-label">Healthcare in High-Use Counties</span>
          </div>
          <button className="info-toggle" title="Click for details"><Info size={10} /></button>
          <div className="card-tooltip">Healthcare facilities in counties with &gt;30M lbs pesticide use annually</div>
        </motion.div>

        <motion.div className="summary-card has-tooltip" whileHover={{ y: -2 }}>
          <div className="summary-icon red"><AlertCircle size={20} /></div>
          <div className="summary-content">
            <span className="summary-value">{highestCounty}</span>
            <span className="summary-label">Highest Volume County</span>
          </div>
          <button className="info-toggle" title="Click for details"><Info size={10} /></button>
          <div className="card-tooltip">County with most pounds of pesticide applied in {selectedYear}. Risk = total lbs applied (not toxicity-weighted).</div>
        </motion.div>

        <motion.div className="summary-card simulated has-tooltip" whileHover={{ y: -2 }}>
          <div className="summary-icon orange"><Radio size={20} className={connected ? 'pulse' : ''} /></div>
          <div className="summary-content">
            <span className="summary-value">{liveSprayEvents.length}</span>
            <span className="summary-label">Simulated Events <span className="demo-badge">DEMO</span></span>
          </div>
          <button className="info-toggle" title="Click for details"><Info size={10} /></button>
          <div className="card-tooltip">Simulated real-time events for demonstration. Historical data available through 2023.</div>
        </motion.div>
      </div>

      {/* Main Content */}
      <main className="main">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'history' && renderHistory()}
        {activeTab === 'research' && renderResearch()}
        {activeTab === 'alerts' && renderAlerts()}
      </main>

      {/* Farmer Portal Modal */}
      <AnimatePresence>
        {showFarmerPortal && (
          <FarmerPortal
            isOpen={showFarmerPortal}
            onClose={() => setShowFarmerPortal(false)}
          />
        )}
      </AnimatePresence>

      {/* AI Assistant Modal */}
      <AnimatePresence>
        {showAIAssistant && (
          <AIAssistant
            isOpen={showAIAssistant}
            onClose={() => setShowAIAssistant(false)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
