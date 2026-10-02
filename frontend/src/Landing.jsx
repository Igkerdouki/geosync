import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import { ArrowRight, ArrowDown, Zap, Map, Wind, FlaskConical, Check } from 'lucide-react'
import './Landing.css'

const API_URL = 'http://localhost:8001/api'

const rise = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-80px' },
  transition: { duration: 0.7, ease: [0.22, 0.61, 0.36, 1] }
}

const formatRecords = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n.toLocaleString())

function Landing({ onEnter }) {
  const [coverage, setCoverage] = useState(null)
  const [applied, setApplied] = useState(null)

  // Coverage figures come straight from the database, so the page never overstates them.
  useEffect(() => {
    axios.get(`${API_URL}/sprays/years`)
      .then(res => {
        const years = res.data.map(y => y.year)
        setCoverage({
          records: res.data.reduce((sum, y) => sum + y.records, 0),
          span: `${Math.min(...years)}–${Math.max(...years)}`
        })
      })
      .catch(() => setCoverage(null))
    axios.get(`${API_URL}/sprays/stats?year=2023`)
      .then(res => setApplied(res.data.total_lbs_applied))
      .catch(() => setApplied(null))
  }, [])

  return (
    <div className="landing">
      <section className="lp-hero">
        <header className="lp-nav">
          <div className="lp-logo"><span className="lp-logo-icon"><Zap size={18} /></span>GeoSync</div>
          <nav className="lp-links">
            <a href="#lp-what">What it does</a>
            <a href="#lp-why">Why it matters</a>
            <a href="#lp-data">The data</a>
          </nav>
          <button className="lp-btn lp-btn-lime lp-btn-sm" onClick={onEnter}>
            Open the live map <ArrowRight size={16} />
          </button>
        </header>

        <div className="lp-hero-grid">
          <div className="lp-hero-copy">
            <div className="lp-hero-body">
              <motion.span className="lp-pill" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
                Pesticide drift, made visible
              </motion.span>
              <motion.h1 initial={{ opacity: 0, y: 26 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.1 }}>
                Someone is always <em>downwind.</em>
              </motion.h1>
              <motion.p initial={{ opacity: 0, y: 26 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}>
                California records every pesticide application in the state. GeoSync turns that
                public record into a live map, a drift forecast and a warning — for the school,
                the clinic and the family next to the field.
              </motion.p>
              <motion.div className="lp-actions" initial={{ opacity: 0, y: 26 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.3 }}>
                <button className="lp-btn lp-btn-lime" onClick={onEnter}>Open the live map <ArrowRight size={18} /></button>
                <a className="lp-btn lp-btn-ghost" href="#lp-what">How it works <ArrowDown size={18} /></a>
              </motion.div>
            </div>
            <div className="lp-stats">
              <div><b>{coverage ? formatRecords(coverage.records) : '—'}</b><span>application records</span></div>
              <div><b>{coverage ? coverage.span : '—'}</b><span>years of public data</span></div>
              <div><b>Live</b><span>weather-driven drift model</span></div>
            </div>
          </div>

          <motion.figure className="lp-hero-figure" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.9, delay: 0.15 }}>
            <img src="/landing/sprayer.jpg" alt="A tractor spraying pesticide across rows of lettuce, a fine mist hanging behind the boom." />
            <div className="lp-float lp-float-top">
              <span className="lp-float-dot" /> Spraying now, drifting next
            </div>
            <div className="lp-float lp-float-bottom">
              <b>{applied ? `${(applied / 1e6).toFixed(1)}M lbs` : '—'}</b>
              <span>of pesticide applied in California in 2023</span>
            </div>
            <figcaption>Pesticide application on leaf lettuce, Yuma, Arizona · Jeff Vanuga, USDA NRCS</figcaption>
          </motion.figure>
        </div>
      </section>

      <section className="lp-band" id="lp-data">
        <div className="lp-band-lead">Built entirely on<br />public data</div>
        <ul>
          <li>CA DPR Pesticide Use Reports</li>
          <li>CalEnviroScreen</li>
          <li>OpenWeatherMap</li>
          <li>US EPA toxicity data</li>
        </ul>
      </section>

      <section className="lp-what" id="lp-what">
        <motion.div className="lp-head" {...rise}>
          <span className="lp-pill lp-pill-dark">What it does</span>
          <h2>From a public record<br />to a warning.</h2>
        </motion.div>

        <div className="lp-cards">
          <motion.article className="lp-card" {...rise}>
            <div className="lp-card-top"><span className="lp-card-icon"><Map size={22} /></span><span className="lp-card-n">01</span></div>
            <h3>A live map</h3>
            <p>Spray events, schools and healthcare sites on one map, with risk zones colour-coded so the picture reads at a glance.</p>
          </motion.article>
          <motion.article className="lp-card" {...rise} transition={{ ...rise.transition, delay: 0.1 }}>
            <div className="lp-card-top"><span className="lp-card-icon"><Wind size={22} /></span><span className="lp-card-n">02</span></div>
            <h3>A drift forecast</h3>
            <p>A Gaussian plume model takes the wind and the weather and predicts where a spray will travel after it leaves the field.</p>
          </motion.article>
          <motion.article className="lp-card" {...rise} transition={{ ...rise.transition, delay: 0.2 }}>
            <div className="lp-card-top"><span className="lp-card-icon"><FlaskConical size={22} /></span><span className="lp-card-n">03</span></div>
            <h3>Research tools</h3>
            <p>Trends by county and by chemical, toxicity classifications, and exports for anyone who wants to check the numbers.</p>
          </motion.article>
        </div>
      </section>

      <section className="lp-why" id="lp-why">
        <motion.div className="lp-collage" {...rise}>
          <img className="lp-photo-a" src="/landing/duster.jpg" alt="A crop duster flying low over a field at dusk, trailing spray." />
          <img className="lp-photo-b" src="/landing/field.jpg" alt="People standing at the edge of a strawberry field under a bright sun." />
          <div className="lp-badge"><Wind size={18} /><div><b>Drift doesn't stop</b><span>at the edge of the field</span></div></div>
        </motion.div>

        <motion.div className="lp-why-copy" {...rise}>
          <span className="lp-pill">Why it matters</span>
          <h2>The data existed.<br />The warning <em>did not.</em></h2>
          <p>
            Every application is logged and published, then buried in databases almost
            nobody outside a research office can query. The people who live, work and
            study beside the fields are the last to know what was sprayed next to them.
          </p>
          <ul className="lp-checks">
            <li><Check size={16} /> See what was applied, where and when</li>
            <li><Check size={16} /> See where the wind is likely to carry it</li>
            <li><Check size={16} /> See which schools and clinics are in its path</li>
          </ul>
          <button className="lp-btn lp-btn-lime" onClick={onEnter}>Explore the map <ArrowRight size={18} /></button>
        </motion.div>
      </section>

      <section className="lp-cta">
        <motion.div className="lp-cta-box" {...rise}>
          <h2>See what was sprayed near you.</h2>
          <button className="lp-btn lp-btn-dark" onClick={onEnter}>Open the live map <ArrowRight size={18} /></button>
        </motion.div>
        <footer className="lp-foot">
          <span>GeoSync · a research prototype. Live events on the map are simulated for demonstration.</span>
          <span>Photographs: Jeff Vanuga and USDA NRCS; Charles O'Rear, EPA Documerica (US National Archives). Public domain.</span>
        </footer>
      </section>
    </div>
  )
}

export default Landing
