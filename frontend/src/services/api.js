const API_BASE = '/api';

export const api = {
  async createActionPlan(data) {
    const response = await fetch(`${API_BASE}/action-plans/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  async getActionPlan(planId) {
    const response = await fetch(`${API_BASE}/action-plans/${planId}/`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  async getActionPlanStatus(planId) {
    const response = await fetch(`${API_BASE}/action-plans/${planId}/status/`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  async listActionPlans() {
    const response = await fetch(`${API_BASE}/action-plans/list/`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  async submitFeedback(data, confirm = false) {
    const url = confirm 
      ? `${API_BASE}/feedback/?confirm=true` 
      : `${API_BASE}/feedback/`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    const responseData = await response.json();

    return {
      status: response.status,
      data: responseData,
    };
  },

  async getFeedbackStatus(feedbackId) {
    const response = await fetch(`${API_BASE}/feedback/${feedbackId}/status/`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  async getStores() {
    const response = await fetch(`${API_BASE}/stores/`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  async getCustomerByDetails(firstName, lastName, phone) {
    const params = new URLSearchParams({
      first_name: firstName,
      last_name: lastName,
      phone: phone
    });
    
    const response = await fetch(`${API_BASE}/customers/?${params}`);
    
    // 404 is expected when customer not found
    if (response.status === 404) {
      const data = await response.json();
      return { found: false, message: data.message };
    }
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  async listFeedback(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.category) {
      params.append('category', filters.category);
    }
    
    if (filters.store_id) {
      params.append('store_id', filters.store_id);
    }
    
    const url = params.toString() 
      ? `${API_BASE}/feedback/?${params}` 
      : `${API_BASE}/feedback/`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },
};

export const POLLING_CONFIG = {
  delays: [1000, 2000, 3000, 5000],
  maxDelay: 5000,
  maxAttempts: 30,
};
