import { useState } from 'react'
import { api } from '../services/api'

function CreatePlanForm({ onPlanCreated }) {
  const [formData, setFormData] = useState({
    store_name: '',
    store_location: '',
    issue_description: '',
  })
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setSuccess(false)

    try {
      const result = await api.createActionPlan(formData)
      
      setFormData({
        store_name: '',
        store_location: '',
        issue_description: '',
      })
      
      setSuccess(true)
      
      onPlanCreated(result)
      
      setTimeout(() => setSuccess(false), 3000)
    } catch (error) {
      alert('Error: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      {!loading ? (
        <>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="storeName">Store Name</label>
              <input
                type="text"
                id="storeName"
                name="store_name"
                value={formData.store_name}
                onChange={handleChange}
                required
                placeholder="e.g., Downtown Store #42"
              />
            </div>

            <div className="form-group">
              <label htmlFor="storeLocation">Store Location</label>
              <input
                type="text"
                id="storeLocation"
                name="store_location"
                value={formData.store_location}
                onChange={handleChange}
                required
                placeholder="e.g., 123 Main St, San Francisco, CA"
              />
            </div>

            <div className="form-group">
              <label htmlFor="issueDescription">Issue Description</label>
              <textarea
                id="issueDescription"
                name="issue_description"
                value={formData.issue_description}
                onChange={handleChange}
                required
                placeholder="Describe the issue or challenge at this store..."
              />
            </div>

            <button type="submit" className="primary-button">
              Generate Action Plan
            </button>
          </form>
          
          {success && (
            <div className="success-message">
              ✅ Action plan created successfully!
            </div>
          )}
        </>
      ) : (
        <div className="loading">
          <div className="spinner"></div>
          <p>Generating your action plan... Please wait.</p>
        </div>
      )}
    </div>
  )
}

export default CreatePlanForm
