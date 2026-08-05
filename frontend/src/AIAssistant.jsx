/**
 * AI Assistant - Embedded chat for pesticide questions
 *
 * Users can ask about:
 * - Chemical dangers and safety
 * - Areas with high exposure
 * - Latest spraying in their area
 * - Health effects
 * - Regulations
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  MessageCircle, Send, X, Bot, User, Loader,
  AlertTriangle, Info, Droplets, MapPin, Clock,
  HelpCircle, Sparkles, ChevronDown
} from 'lucide-react'

const API_URL = 'http://localhost:8001/api'

// Predefined quick questions
const QUICK_QUESTIONS = [
  "What is Chlorpyrifos and is it dangerous?",
  "Which county has the highest pesticide use?",
  "What schools are near pesticide zones?",
  "What are the health effects of glyphosate?",
  "When was the last spray in Kern County?",
  "How does wind affect pesticide drift?"
]

// Knowledge base for common questions (fallback when no API)
const KNOWLEDGE_BASE = {
  chlorpyrifos: {
    answer: `**Chlorpyrifos** is an organophosphate insecticide that has been widely used in agriculture since 1965.

**Health Concerns:**
- EPA Category II (Moderately Toxic)
- Can affect the nervous system
- Linked to developmental issues in children
- California has restricted its use near schools

**Current Status:**
- Banned for most residential uses
- Restricted in California near schools and daycare centers
- Still used in agriculture under strict regulations

**What to do if exposed:**
Contact Poison Control: 1-800-222-1222`,
    risk: "high"
  },
  glyphosate: {
    answer: `**Glyphosate** (Roundup) is the most widely used herbicide in California agriculture.

**Health Effects:**
- EPA Category III (Slightly Toxic)
- WHO classified as "probably carcinogenic to humans" (2015)
- California added it to Prop 65 list (cancer warning)

**Exposure:**
- Most common through residues on food
- Drift from agricultural applications
- Direct contact during application

**In California:**
- Over 15 million lbs applied annually
- Most heavily used in almond, grape, and citrus production`,
    risk: "medium"
  },
  drift: {
    answer: `**Pesticide Drift** is the movement of pesticide through the air during or after application.

**Factors affecting drift:**
1. **Wind speed** - Higher wind = more drift
2. **Temperature** - Hot conditions increase evaporation
3. **Humidity** - Low humidity increases small droplet formation
4. **Droplet size** - Smaller droplets drift farther
5. **Application method** - Aerial spraying drifts more than ground

**How to protect yourself:**
- Monitor GeoSync alerts for nearby applications
- Stay indoors during high-risk conditions
- Close windows when spraying is reported nearby
- Keep children indoors during active spray times`,
    risk: "medium"
  },
  health: {
    answer: `**Common Health Effects of Pesticide Exposure:**

**Acute (immediate):**
- Skin and eye irritation
- Headaches and dizziness
- Nausea and vomiting
- Respiratory problems

**Chronic (long-term):**
- Neurological effects
- Hormone disruption
- Increased cancer risk
- Reproductive issues
- Developmental effects in children

**Vulnerable populations:**
- Children (developing nervous systems)
- Pregnant women
- Agricultural workers
- People with respiratory conditions

**If you suspect exposure:**
- Move to fresh air
- Remove contaminated clothing
- Wash skin with soap and water
- Call Poison Control: 1-800-222-1222`,
    risk: "high"
  },
  schools: {
    answer: `**Schools Near Pesticide Application Zones:**

GeoSync tracks schools in high-use agricultural counties:

**Highest Risk Counties (for schools):**
1. **Fresno County** - 15+ schools in high-exposure zones
2. **Kern County** - 12+ schools near active spray sites
3. **Tulare County** - 8+ schools affected

**California Regulations:**
- 1/4 mile buffer required for certain pesticides
- 48-hour advance notice for fumigants near schools
- SprayDays notification system available

**What schools can do:**
- Register for SprayDays California alerts
- Monitor GeoSync for nearby applications
- Have indoor air filtration
- Adjust outdoor activities during spray events`,
    risk: "high"
  }
}

export default function AIAssistant({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hi! I'm the GeoSync AI Assistant. I can help you with:

- **Chemical information** - What pesticides are used and their risks
- **Location data** - Spray history for specific counties
- **Health effects** - Understanding exposure risks
- **Safety tips** - How to protect yourself and family

What would you like to know?`
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const processQuestion = async (question) => {
    const q = question.toLowerCase()

    // Check knowledge base first
    for (const [key, data] of Object.entries(KNOWLEDGE_BASE)) {
      if (q.includes(key)) {
        return data.answer
      }
    }

    // Try to fetch real data for specific queries
    try {
      // County-specific questions
      if (q.includes('fresno') || q.includes('kern') || q.includes('tulare')) {
        const county = q.includes('fresno') ? 'FRESNO' :
                       q.includes('kern') ? 'KERN' : 'TULARE'

        const res = await axios.get(`${API_URL}/history/peak-days/${county}?year=2023&top_n=3`)
        const days = res.data.peak_days

        if (days && days.length > 0) {
          return `**Recent Spray Data for ${county} County (2023):**

The top spray days were:

${days.map(d => `- **${d.date_formatted}**: ${(d.total_lbs / 1000).toFixed(0)}K lbs applied (${d.spray_events} events)`).join('\n')}

These days had the highest pesticide application volume. If you were in ${county} County on these dates, you may have had elevated exposure.

Would you like more details about specific chemicals used?`
        }
      }

      // Chemical-specific questions
      if (q.includes('chemical') || q.includes('most used')) {
        const res = await axios.get(`${API_URL}/research/chemicals?limit=5`)
        const chems = res.data.chemicals

        if (chems && chems.length > 0) {
          return `**Most Used Pesticides in California:**

${chems.map((c, i) => `${i+1}. **${c.chemical_name}** - ${(c.total_lbs / 1000000).toFixed(1)}M lbs`).join('\n')}

These are aggregated across all California counties. Would you like information about a specific chemical's health effects?`
        }
      }

    } catch (err) {
      console.error('API query failed:', err)
    }

    // Default response
    return `I can help you with information about:

- **Specific chemicals** (e.g., "What is chlorpyrifos?")
- **County data** (e.g., "Spray history in Kern County")
- **Health effects** (e.g., "Health effects of pesticides")
- **School safety** (e.g., "Schools near pesticide zones")
- **Drift risks** (e.g., "How does wind affect drift?")

Try asking about one of these topics!`
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await processQuestion(input)
      setMessages(prev => [...prev, { role: 'assistant', content: response }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm sorry, I encountered an error processing your question. Please try again."
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleQuickQuestion = (question) => {
    setInput(question)
  }

  if (!isOpen) return null

  return (
    <motion.div
      className="ai-assistant-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="ai-assistant"
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        {/* Header */}
        <div className="ai-header">
          <div className="ai-title">
            <Sparkles size={20} />
            <span>GeoSync AI Assistant</span>
          </div>
          <button className="ai-close" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Messages */}
        <div className="ai-messages">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              className={`ai-message ${msg.role}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="message-avatar">
                {msg.role === 'assistant' ? <Bot size={18} /> : <User size={18} />}
              </div>
              <div className="message-content" dangerouslySetInnerHTML={{
                __html: msg.content
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\n/g, '<br/>')
              }} />
            </motion.div>
          ))}

          {loading && (
            <div className="ai-message assistant">
              <div className="message-avatar"><Bot size={18} /></div>
              <div className="message-content typing">
                <Loader className="spin" size={16} /> Thinking...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Questions */}
        <div className="quick-questions">
          <div className="quick-label"><HelpCircle size={14} /> Quick questions:</div>
          <div className="quick-buttons">
            {QUICK_QUESTIONS.slice(0, 3).map((q, i) => (
              <button key={i} onClick={() => handleQuickQuestion(q)}>
                {q.length > 30 ? q.slice(0, 30) + '...' : q}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="ai-input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about chemicals, locations, health effects..."
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>
            <Send size={18} />
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}
