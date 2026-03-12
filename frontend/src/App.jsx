import { useState } from 'react'
import TabNav from './components/TabNav'
import CreatePlanForm from './components/CreatePlanForm'
import PlansList from './components/PlansList'
import PlanDetailModal from './components/PlanDetailModal'

function App() {
  const [activeTab, setActiveTab] = useState('create')
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handlePlanCreated = (plan) => {
    setSelectedPlan(plan)
    setRefreshTrigger(prev => prev + 1)
  }

  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan)
  }

  const handleModalClose = () => {
    setSelectedPlan(null)
  }

  return (
    <div className="container">
      <h1>Retail Action Plan Generator</h1>
      
      <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === 'create' && (
        <CreatePlanForm onPlanCreated={handlePlanCreated} />
      )}

      {activeTab === 'search' && (
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
