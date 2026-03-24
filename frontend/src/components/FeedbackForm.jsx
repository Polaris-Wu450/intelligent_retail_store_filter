import { useState, useRef, useEffect } from 'react';
import { api, POLLING_CONFIG } from '../services/api';
import Modal from './Modal';

function FeedbackForm({ onSuccess }) {
  const [formData, setFormData] = useState({
    store_id: '',
    store_name: '',
    first_name: '',
    last_name: '',
    phone: '',
    category_code: 'FURNITURE',
    content: '',
  });

  const [stores, setStores] = useState([]);
  const [loadingStores, setLoadingStores] = useState(true);
  const [customerFound, setCustomerFound] = useState(null);
  const [customerNotFoundMessage, setCustomerNotFoundMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [warningModal, setWarningModal] = useState({ open: false, message: '' });
  const [errorModal, setErrorModal] = useState({ open: false, message: '' });
  
  const pollingTimeoutRef = useRef(null);
  const attemptRef = useRef(0);
  const currentFeedbackIdRef = useRef(null);

  useEffect(() => {
    loadStores();
  }, []);

  const loadStores = async () => {
    try {
      const data = await api.getStores();
      setStores(data.stores);
    } catch (error) {
      console.error('Error loading stores:', error);
      setErrorModal({
        open: true,
        message: 'Failed to load stores. Please refresh the page.',
      });
    } finally {
      setLoadingStores(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // If store selection changes, update both store_id and store_name
    if (name === 'store_select') {
      const selectedStore = stores.find(s => s.store_id === value);
      setFormData({
        ...formData,
        store_id: value,
        store_name: selectedStore?.name || '',
      });
    } else {
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };

  const handlePhoneBlur = async () => {
    const { first_name, last_name, phone } = formData;
    
    // Only check if all three fields are filled
    if (!first_name?.trim() || !last_name?.trim() || !phone?.trim()) {
      setCustomerFound(null);
      setCustomerNotFoundMessage('');
      return;
    }

    try {
      const result = await api.getCustomerByDetails(
        first_name.trim(),
        last_name.trim(),
        phone.trim()
      );
      
      if (result.found) {
        setCustomerFound(true);
        setCustomerNotFoundMessage('');
      } else {
        setCustomerFound(false);
        setCustomerNotFoundMessage(result.message || 'New customer - will be created upon submission');
      }
    } catch (error) {
      console.error('Error checking customer:', error);
      // On error, allow submission (customer will be created)
      setCustomerFound(false);
      setCustomerNotFoundMessage('Unable to verify customer - will create if needed');
    }
  };

  const handleSubmit = async (e, confirm = false) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('[FeedbackForm] Submitting feedback:', formData);
      const result = await api.submitFeedback(formData, confirm);
      console.log('[FeedbackForm] Submit result:', result);

      if (result.status === 200 && result.data.warnings) {
        // Warning detected - show modal with detailed message
        console.log('[FeedbackForm] Warning detected:', result.data);
        setLoading(false);
        // Extract message from warnings array (backend returns array of warning objects)
        const warningMessage = Array.isArray(result.data.warnings) && result.data.warnings.length > 0
          ? result.data.warnings[0].message  // Get message from first warning object
          : result.data.message || 'Previous feedback detected. Confirm to continue.';
        setWarningModal({
          open: true,
          message: warningMessage,
        });
        return;
      }

      if (result.status === 409) {
        // Error - blocked (duplicate feedback)
        console.log('[FeedbackForm] Error 409 (Blocked):', result.data);
        setLoading(false);
        setErrorModal({
          open: true,
          message: result.data.message || result.data.error || 'Submission blocked due to duplicate feedback.',
        });
        return;
      }

      if (result.status === 201) {
        // Success - start polling ActionPlan status
        const actionPlanId = result.data.action_plan?.id;
        console.log('[FeedbackForm] Success! ActionPlan ID:', actionPlanId);
        
        if (!actionPlanId) {
          console.error('[FeedbackForm] ERROR: action_plan.id is missing!');
          setLoading(false);
          setErrorModal({
            open: true,
            message: 'Feedback submitted but ActionPlan ID is missing. Please contact support.',
          });
          return;
        }
        
        currentFeedbackIdRef.current = actionPlanId;
        setLoading(false);
        setPolling(true);
        console.log('[FeedbackForm] Starting polling for ActionPlan:', actionPlanId);
        startPolling(actionPlanId);
      } else {
        // Unexpected status code
        console.warn('[FeedbackForm] Unexpected status:', result.status);
        setLoading(false);
        setErrorModal({
          open: true,
          message: `Unexpected response status: ${result.status}`,
        });
      }
    } catch (error) {
      console.error('[FeedbackForm] Submit error:', error);
      setLoading(false);
      setErrorModal({
        open: true,
        message: error.message || 'An unexpected error occurred.',
      });
    }
  };

  const startPolling = async (actionPlanId) => {
    try {
      console.log(`[FeedbackForm] Polling attempt ${attemptRef.current + 1}/${POLLING_CONFIG.maxAttempts} for ActionPlan ${actionPlanId}`);
      
      if (attemptRef.current >= POLLING_CONFIG.maxAttempts) {
        console.error('[FeedbackForm] Polling timeout reached!');
        setPolling(false);
        setErrorModal({
          open: true,
          message: 'Polling timeout - processing took too long. Please check back later.',
        });
        return;
      }

      const statusData = await api.getActionPlanStatus(actionPlanId);
      console.log('[FeedbackForm] Status data:', statusData);

      if (statusData.status === 'completed') {
        console.log('[FeedbackForm] ✅ ActionPlan completed!');
        setPolling(false);
        // Reset form
        setFormData({
          store_id: '',
          store_name: '',
          first_name: '',
          last_name: '',
          phone: '',
          category_code: 'FURNITURE',
          content: '',
        });
        setCustomerFound(null);
        setCustomerNotFoundMessage('');
        attemptRef.current = 0;
        
        console.log('[FeedbackForm] Calling onSuccess...');
        if (onSuccess) {
          onSuccess(statusData);
        }
        return;
      }

      if (statusData.status === 'failed') {
        console.error('[FeedbackForm] ActionPlan generation failed:', statusData.error_message);
        setPolling(false);
        setErrorModal({
          open: true,
          message: statusData.error_message || 'Failed to generate action plan.',
        });
        return;
      }

      // Still processing - schedule next poll
      const delayIndex = Math.min(
        attemptRef.current,
        POLLING_CONFIG.delays.length - 1
      );
      const delay = POLLING_CONFIG.delays[delayIndex];
      
      console.log(`[FeedbackForm] Status: ${statusData.status}, scheduling next poll in ${delay}ms`);

      attemptRef.current += 1;

      pollingTimeoutRef.current = setTimeout(() => {
        startPolling(actionPlanId);
      }, delay);
    } catch (error) {
      console.error('[FeedbackForm] Polling error:', error);
      setPolling(false);
      setErrorModal({
        open: true,
        message: error.message || 'Error while checking status.',
      });
    }
  };

  const handleWarningConfirm = (e) => {
    setWarningModal({ open: false, message: '' });
    handleSubmit(e, true);
  };

  const handleWarningCancel = () => {
    setWarningModal({ open: false, message: '' });
  };

  const handleErrorClose = () => {
    setErrorModal({ open: false, message: '' });
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow-sm p-8">
        {!loading && !polling ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Store Information */}
            <div className="border-b pb-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Store Information</h2>
              <div>
                <label htmlFor="store_select" className="block text-sm font-medium text-gray-700 mb-2">
                  Select Store <span className="text-red-500">*</span>
                </label>
                {loadingStores ? (
                  <div className="text-gray-500 text-sm">Loading stores...</div>
                ) : (
                  <select
                    id="store_select"
                    name="store_select"
                    value={formData.store_id}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">-- Select a store --</option>
                    {stores.map((store) => (
                      <option key={store.store_id} value={store.store_id}>
                        {store.name} ({store.store_id})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {/* Customer Information */}
            <div className="border-b pb-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Customer Information</h2>
              
              {/* Customer Details - check on phone blur */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
                    First Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    required
                    readOnly={customerFound === true}
                    className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      customerFound === true ? 'bg-gray-50 cursor-not-allowed' : ''
                    }`}
                    placeholder="e.g., John"
                  />
                </div>
                <div>
                  <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    required
                    readOnly={customerFound === true}
                    className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      customerFound === true ? 'bg-gray-50 cursor-not-allowed' : ''
                    }`}
                    placeholder="e.g., Doe"
                  />
                </div>
                <div className="md:col-span-2">
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    onBlur={handlePhoneBlur}
                    required
                    readOnly={customerFound === true}
                    className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      customerFound === true ? 'bg-gray-50 cursor-not-allowed' : ''
                    }`}
                    placeholder="e.g., 555-0123 (will check if customer exists)"
                  />
                  {customerFound === true && (
                    <p className="mt-1 text-sm text-green-600">✓ Existing customer found</p>
                  )}
                  {customerFound === false && (
                    <p className="mt-1 text-sm text-blue-600">ℹ️ {customerNotFoundMessage}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Feedback Details */}
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Feedback Details</h2>
              <div className="space-y-4">
                <div>
                  <label htmlFor="category_code" className="block text-sm font-medium text-gray-700 mb-2">
                    Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="category_code"
                    name="category_code"
                    value={formData.category_code}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="FURNITURE">Furniture</option>
                    <option value="ELECTRONICS">Electronics</option>
                    <option value="CLOTHING">Clothing</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
                    Feedback Content <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="content"
                    name="content"
                    value={formData.content}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    placeholder="Please describe the issue or feedback in detail..."
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Submit Feedback
            </button>
          </form>
        ) : (
          <div className="text-center py-12">
            <div className="inline-block w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-lg font-medium text-gray-700">
              {loading ? 'Submitting feedback...' : 'Generating Action Plan...'}
            </p>
            <p className="text-sm text-gray-500 mt-2">This may take 10-30 seconds</p>
          </div>
        )}
      </div>

      {/* Warning Modal */}
      <Modal
        isOpen={warningModal.open}
        onClose={handleWarningCancel}
        title="Potential Duplicate Detected"
        type="warning"
        actions={
          <>
            <button
              onClick={handleWarningCancel}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleWarningConfirm}
              className="px-4 py-2 text-white bg-yellow-600 rounded-lg hover:bg-yellow-700 transition-colors"
            >
              Confirm & Continue
            </button>
          </>
        }
      >
        <p className="text-gray-700 whitespace-pre-line">{warningModal.message}</p>
      </Modal>

      {/* Error Modal */}
      <Modal
        isOpen={errorModal.open}
        onClose={handleErrorClose}
        title="Submission Blocked"
        type="error"
        actions={
          <button
            onClick={handleErrorClose}
            className="px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
          >
            OK
          </button>
        }
      >
        <p className="text-gray-700 whitespace-pre-line">{errorModal.message}</p>
      </Modal>
    </>
  );
}

export default FeedbackForm;
