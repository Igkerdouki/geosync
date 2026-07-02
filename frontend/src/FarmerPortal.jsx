/**
 * Farmer Portal - Login, Register, and Spray Reporting
 *
 * This is where farmers log their spray activities in real-time.
 * Data immediately updates the public dashboard.
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  User, Lock, Mail, Phone, MapPin, Wheat, Building,
  Droplets, Calendar, Clock, Wind, Thermometer,
  AlertTriangle, CheckCircle, ChevronRight, LogOut,
  Plus, History, BarChart3, Send, Loader, Home
} from 'lucide-react'

const API_URL = 'http://localhost:8001/api'

// Chemical types for dropdown
const CHEMICAL_TYPES = [
  'herbicide',
  'insecticide',
  'fungicide',
  'fumigant',
  'rodenticide',
  'plant growth regulator',
  'adjuvant',
  'other'
]

const APPLICATION_METHODS = [
  'ground spray',
  'aerial spray',
  'irrigation (chemigation)',
  'seed treatment',
  'soil injection',
  'hand application',
  'other'
]

const COUNTIES = [
  'FRESNO', 'KERN', 'TULARE', 'MONTEREY', 'IMPERIAL',
  'SAN JOAQUIN', 'VENTURA', 'STANISLAUS', 'MERCED', 'KINGS',
  'MADERA', 'SANTA BARBARA', 'SAN DIEGO', 'RIVERSIDE', 'SACRAMENTO'
]

export default function FarmerPortal({ isOpen, onClose, onLogout }) {
  if (!isOpen) return null
  const [view, setView] = useState('login') // login, register, dashboard
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Auth state
  const [token, setToken] = useState(localStorage.getItem('farmer_token'))
  const [farmer, setFarmer] = useState(null)

  // Form states
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({
    email: '', password: '', farm_name: '', owner_name: '',
    county: 'FRESNO', farm_size: 'medium', primary_crops: '',
    phone: '', address: '', lat: null, lon: null
  })

  const [sprayForm, setSprayForm] = useState({
    chemical_name: '',
    chemical_type: 'herbicide',
    lbs_applied: '',
    acres_treated: '',
    application_method: 'ground spray',
    target_crop: '',
    field_name: '',
    lat: '',
    lon: '',
    scheduled_time: '',
    notes: '',
    wind_speed_mph: '',
    wind_direction: '',
    temperature_f: ''
  })

  const [myReports, setMyReports] = useState([])
  const [stats, setStats] = useState(null)

  // Check if already logged in
  useEffect(() => {
    if (token) {
      fetchProfile()
    }
  }, [token])

  const fetchProfile = async () => {
    try {
      const res = await axios.get(`${API_URL}/farmers/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setFarmer(res.data)
      setView('dashboard')
      fetchMyReports()
      fetchStats()
    } catch (err) {
      // Token invalid
      localStorage.removeItem('farmer_token')
      setToken(null)
      setView('login')
    }
  }

  const fetchMyReports = async () => {
    try {
      const res = await axios.get(`${API_URL}/farmers/my-reports?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setMyReports(res.data.reports || [])
    } catch (err) {
      console.error('Failed to fetch reports:', err)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_URL}/farmers/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setStats(res.data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await axios.post(`${API_URL}/farmers/login`, loginForm)
      localStorage.setItem('farmer_token', res.data.token)
      setToken(res.data.token)
      setFarmer(res.data.farmer)
      setView('dashboard')
      setSuccess('Welcome back!')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await axios.post(`${API_URL}/farmers/register`, registerForm)
      localStorage.setItem('farmer_token', res.data.token)
      setToken(res.data.token)
      setView('dashboard')
      setSuccess('Registration successful! Welcome to GeoSync.')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitSpray = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const payload = {
        ...sprayForm,
        lbs_applied: parseFloat(sprayForm.lbs_applied),
        acres_treated: parseFloat(sprayForm.acres_treated),
        lat: parseFloat(sprayForm.lat),
        lon: parseFloat(sprayForm.lon),
        scheduled_time: new Date(sprayForm.scheduled_time).toISOString(),
        wind_speed_mph: sprayForm.wind_speed_mph ? parseFloat(sprayForm.wind_speed_mph) : null,
        temperature_f: sprayForm.temperature_f ? parseFloat(sprayForm.temperature_f) : null
      }

      const res = await axios.post(`${API_URL}/farmers/spray-report`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setSuccess(`Report submitted! ${res.data.message}`)

      // Reset form
      setSprayForm({
        chemical_name: '', chemical_type: 'herbicide', lbs_applied: '',
        acres_treated: '', application_method: 'ground spray', target_crop: '',
        field_name: '', lat: '', lon: '', scheduled_time: '',
        notes: '', wind_speed_mph: '', wind_direction: '', temperature_f: ''
      })

      // Refresh reports
      fetchMyReports()
      fetchStats()

      setTimeout(() => setSuccess(''), 5000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit report')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('farmer_token')
    setToken(null)
    setFarmer(null)
    setView('login')
    if (onLogout) onLogout()
  }

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num?.toFixed(0) || '0'
  }

  // Login Form
  const renderLogin = () => (
    <motion.div
      className="portal-form"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="portal-header">
        <Wheat className="portal-icon" />
        <h2>Farmer Login</h2>
        <p>Log in to report your spray activities</p>
      </div>

      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label><Mail size={16} /> Email</label>
          <input
            type="email"
            value={loginForm.email}
            onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
            placeholder="farmer@example.com"
            required
          />
        </div>

        <div className="form-group">
          <label><Lock size={16} /> Password</label>
          <input
            type="password"
            value={loginForm.password}
            onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
            placeholder="••••••••"
            required
          />
        </div>

        {error && <div className="form-error"><AlertTriangle size={16} /> {error}</div>}

        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? <Loader className="spin" size={18} /> : <><ChevronRight size={18} /> Sign In</>}
        </button>
      </form>

      <div className="portal-footer">
        <p>Don't have an account?</p>
        <button onClick={() => setView('register')}>Register your farm</button>
      </div>
    </motion.div>
  )

  // Register Form
  const renderRegister = () => (
    <motion.div
      className="portal-form register"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="portal-header">
        <Building className="portal-icon" />
        <h2>Register Your Farm</h2>
        <p>Join GeoSync to report spray activities</p>
      </div>

      <form onSubmit={handleRegister}>
        <div className="form-row">
          <div className="form-group">
            <label><User size={16} /> Owner Name</label>
            <input
              type="text"
              value={registerForm.owner_name}
              onChange={(e) => setRegisterForm({...registerForm, owner_name: e.target.value})}
              placeholder="John Smith"
              required
            />
          </div>
          <div className="form-group">
            <label><Building size={16} /> Farm Name</label>
            <input
              type="text"
              value={registerForm.farm_name}
              onChange={(e) => setRegisterForm({...registerForm, farm_name: e.target.value})}
              placeholder="Smith Family Farms"
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label><Mail size={16} /> Email</label>
            <input
              type="email"
              value={registerForm.email}
              onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
              placeholder="farmer@example.com"
              required
            />
          </div>
          <div className="form-group">
            <label><Lock size={16} /> Password</label>
            <input
              type="password"
              value={registerForm.password}
              onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
              placeholder="••••••••"
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label><MapPin size={16} /> County</label>
            <select
              value={registerForm.county}
              onChange={(e) => setRegisterForm({...registerForm, county: e.target.value})}
            >
              {COUNTIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label><Wheat size={16} /> Farm Size</label>
            <select
              value={registerForm.farm_size}
              onChange={(e) => setRegisterForm({...registerForm, farm_size: e.target.value})}
            >
              <option value="small">Small (&lt; 100 acres)</option>
              <option value="medium">Medium (100-500 acres)</option>
              <option value="large">Large (500-2000 acres)</option>
              <option value="enterprise">Enterprise (&gt; 2000 acres)</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label><Wheat size={16} /> Primary Crops</label>
          <input
            type="text"
            value={registerForm.primary_crops}
            onChange={(e) => setRegisterForm({...registerForm, primary_crops: e.target.value})}
            placeholder="almonds, grapes, tomatoes"
          />
        </div>

        <div className="form-group">
          <label><Phone size={16} /> Phone (optional)</label>
          <input
            type="tel"
            value={registerForm.phone}
            onChange={(e) => setRegisterForm({...registerForm, phone: e.target.value})}
            placeholder="(559) 555-0123"
          />
        </div>

        {error && <div className="form-error"><AlertTriangle size={16} /> {error}</div>}

        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? <Loader className="spin" size={18} /> : <><CheckCircle size={18} /> Create Account</>}
        </button>
      </form>

      <div className="portal-footer">
        <p>Already have an account?</p>
        <button onClick={() => setView('login')}>Sign in</button>
      </div>
    </motion.div>
  )

  // Dashboard
  const renderDashboard = () => (
    <motion.div
      className="farmer-dashboard"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* Header */}
      <div className="dashboard-header">
        <div className="farmer-info">
          <div className="farmer-avatar"><Wheat size={24} /></div>
          <div>
            <h2>{farmer?.farm_name || 'My Farm'}</h2>
            <p>{farmer?.county} County</p>
          </div>
        </div>
        <button className="btn-logout" onClick={handleLogout}>
          <LogOut size={18} /> Logout
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="farmer-stats">
          <div className="stat-card">
            <Droplets size={20} />
            <div className="stat-value">{formatNumber(stats.total_lbs_applied)}</div>
            <div className="stat-label">Total lbs Applied</div>
          </div>
          <div className="stat-card">
            <MapPin size={20} />
            <div className="stat-value">{formatNumber(stats.total_acres_treated)}</div>
            <div className="stat-label">Acres Treated</div>
          </div>
          <div className="stat-card">
            <History size={20} />
            <div className="stat-value">{stats.total_reports}</div>
            <div className="stat-label">Reports Filed</div>
          </div>
          <div className="stat-card">
            <BarChart3 size={20} />
            <div className="stat-value">{stats.unique_chemicals}</div>
            <div className="stat-label">Chemicals Used</div>
          </div>
        </div>
      )}

      {success && (
        <motion.div
          className="success-banner"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <CheckCircle size={18} /> {success}
        </motion.div>
      )}

      {/* New Spray Report Form */}
      <div className="spray-report-section">
        <h3><Plus size={18} /> Report New Spray Application</h3>
        <p>Submit this form BEFORE you spray. This data will immediately update the public dashboard.</p>

        <form onSubmit={handleSubmitSpray} className="spray-form">
          <div className="form-section">
            <h4>Chemical Information</h4>
            <div className="form-row">
              <div className="form-group">
                <label>Chemical Name *</label>
                <input
                  type="text"
                  value={sprayForm.chemical_name}
                  onChange={(e) => setSprayForm({...sprayForm, chemical_name: e.target.value})}
                  placeholder="e.g., Glyphosate, Chlorpyrifos"
                  required
                />
              </div>
              <div className="form-group">
                <label>Chemical Type *</label>
                <select
                  value={sprayForm.chemical_type}
                  onChange={(e) => setSprayForm({...sprayForm, chemical_type: e.target.value})}
                >
                  {CHEMICAL_TYPES.map(t => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Amount (lbs) *</label>
                <input
                  type="number"
                  step="0.01"
                  value={sprayForm.lbs_applied}
                  onChange={(e) => setSprayForm({...sprayForm, lbs_applied: e.target.value})}
                  placeholder="100.00"
                  required
                />
              </div>
              <div className="form-group">
                <label>Acres Treated *</label>
                <input
                  type="number"
                  step="0.1"
                  value={sprayForm.acres_treated}
                  onChange={(e) => setSprayForm({...sprayForm, acres_treated: e.target.value})}
                  placeholder="50.0"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4>Application Details</h4>
            <div className="form-row">
              <div className="form-group">
                <label>Application Method *</label>
                <select
                  value={sprayForm.application_method}
                  onChange={(e) => setSprayForm({...sprayForm, application_method: e.target.value})}
                >
                  {APPLICATION_METHODS.map(m => (
                    <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Target Crop *</label>
                <input
                  type="text"
                  value={sprayForm.target_crop}
                  onChange={(e) => setSprayForm({...sprayForm, target_crop: e.target.value})}
                  placeholder="e.g., almonds, grapes"
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Field Name (optional)</label>
                <input
                  type="text"
                  value={sprayForm.field_name}
                  onChange={(e) => setSprayForm({...sprayForm, field_name: e.target.value})}
                  placeholder="e.g., North Block, Field 7"
                />
              </div>
              <div className="form-group">
                <label>Scheduled Time *</label>
                <input
                  type="datetime-local"
                  value={sprayForm.scheduled_time}
                  onChange={(e) => setSprayForm({...sprayForm, scheduled_time: e.target.value})}
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4>Location</h4>
            <div className="form-row">
              <div className="form-group">
                <label>Latitude *</label>
                <input
                  type="number"
                  step="0.0001"
                  value={sprayForm.lat}
                  onChange={(e) => setSprayForm({...sprayForm, lat: e.target.value})}
                  placeholder="36.7378"
                  required
                />
              </div>
              <div className="form-group">
                <label>Longitude *</label>
                <input
                  type="number"
                  step="0.0001"
                  value={sprayForm.lon}
                  onChange={(e) => setSprayForm({...sprayForm, lon: e.target.value})}
                  placeholder="-119.7871"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4>Weather Conditions (optional but recommended)</h4>
            <div className="form-row three">
              <div className="form-group">
                <label><Wind size={14} /> Wind Speed (mph)</label>
                <input
                  type="number"
                  step="0.1"
                  value={sprayForm.wind_speed_mph}
                  onChange={(e) => setSprayForm({...sprayForm, wind_speed_mph: e.target.value})}
                  placeholder="5.0"
                />
              </div>
              <div className="form-group">
                <label>Wind Direction</label>
                <input
                  type="text"
                  value={sprayForm.wind_direction}
                  onChange={(e) => setSprayForm({...sprayForm, wind_direction: e.target.value})}
                  placeholder="NW"
                />
              </div>
              <div className="form-group">
                <label><Thermometer size={14} /> Temperature (°F)</label>
                <input
                  type="number"
                  step="0.1"
                  value={sprayForm.temperature_f}
                  onChange={(e) => setSprayForm({...sprayForm, temperature_f: e.target.value})}
                  placeholder="75"
                />
              </div>
            </div>
          </div>

          <div className="form-group">
            <label>Notes (optional)</label>
            <textarea
              value={sprayForm.notes}
              onChange={(e) => setSprayForm({...sprayForm, notes: e.target.value})}
              placeholder="Any additional details about this application..."
              rows={3}
            />
          </div>

          {error && <div className="form-error"><AlertTriangle size={16} /> {error}</div>}

          <button type="submit" className="btn-submit large" disabled={loading}>
            {loading ? (
              <Loader className="spin" size={20} />
            ) : (
              <><Send size={20} /> Submit Spray Report</>
            )}
          </button>
        </form>
      </div>

      {/* Recent Reports */}
      {myReports.length > 0 && (
        <div className="recent-reports">
          <h3><History size={18} /> Your Recent Reports</h3>
          <div className="reports-list">
            {myReports.slice(0, 5).map((report) => (
              <div key={report.report_id} className={`report-card ${report.drift_risk}`}>
                <div className="report-header">
                  <span className="report-id">{report.report_id}</span>
                  <span className={`risk-badge ${report.drift_risk}`}>{report.drift_risk}</span>
                </div>
                <div className="report-chemical">{report.chemical_name}</div>
                <div className="report-details">
                  <span>{report.lbs_applied} lbs</span>
                  <span>{report.acres_treated} acres</span>
                  <span>{report.target_crop}</span>
                </div>
                <div className="report-time">
                  {new Date(report.scheduled_time).toLocaleString()}
                </div>
                {report.nearby_schools > 0 && (
                  <div className="report-warning">
                    ⚠️ {report.nearby_schools} school(s) nearby
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )

  return (
    <div className="farmer-portal-overlay">
      <motion.div
        className="farmer-portal"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <button className="portal-close" onClick={onClose}>×</button>

        {view === 'login' && renderLogin()}
        {view === 'register' && renderRegister()}
        {view === 'dashboard' && renderDashboard()}
      </motion.div>
    </div>
  )
}
