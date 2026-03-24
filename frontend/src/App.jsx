import { useState } from 'react'
import TabNav from './components/TabNav'
import FeedbackForm from './components/FeedbackForm'
import PlansList from './components/PlansList'
import PlanDetailModal from './components/PlanDetailModal'

function App() {
  const [activeTab, setActiveTab] = useState('feedback')
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan)
  }

  const handleModalClose = () => {
    setSelectedPlan(null)
  }

  const handleFeedbackSuccess = (statusData) => {
    console.log('[App] handleFeedbackSuccess called with:', statusData);
    console.log('[App] Switching to dashboard tab...');
    setActiveTab('dashboard');
    console.log('[App] Triggering refresh...');
    setRefreshTrigger(prev => prev + 1);
  }

  return (
    <div className="container">
      <h1>Retail Action Plan Generator</h1>
      
      <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === 'feedback' && (
        <FeedbackForm onSuccess={handleFeedbackSuccess} />
      )}

      {activeTab === 'dashboard' && (
        <PlansList 
          onPlanSelect={handlePlanSelect} 
          refreshTrigger={refreshTrigger}
        />
      )}

      {selectedPlan && (
        <PlanDetailModal 
          plan={selectedPlan} 
          onClose={handleModalClose} 
        />
      )}
    </div>
  )
}

export default App
