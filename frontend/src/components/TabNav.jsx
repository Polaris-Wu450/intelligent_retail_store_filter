function TabNav({ activeTab, onTabChange }) {
  return (
    <div className="tabs">
      <button
        className={`tab-button ${activeTab === 'feedback' ? 'active' : ''}`}
        onClick={() => onTabChange('feedback')}
      >
        Submit Feedback
      </button>
      <button
        className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`}
        onClick={() => onTabChange('dashboard')}
      >
        Action Plans Dashboard
      </button>
    </div>
  )
}

export default TabNav
