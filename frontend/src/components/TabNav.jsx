function TabNav({ activeTab, onTabChange }) {
  return (
    <div className="tabs">
      <button
        className={`tab-button ${activeTab === 'create' ? 'active' : ''}`}
        onClick={() => onTabChange('create')}
      >
        Create New Plan
      </button>
      <button
        className={`tab-button ${activeTab === 'search' ? 'active' : ''}`}
        onClick={() => onTabChange('search')}
      >
        Search & Browse Plans
      </button>
    </div>
  )
}

export default TabNav
