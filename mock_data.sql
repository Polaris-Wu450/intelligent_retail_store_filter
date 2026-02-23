-- Mock Data for Retail Action Plans
-- Instructions: Open TablePlus, connect to your PostgreSQL database, and execute this SQL

-- Clear existing data (optional - comment out if you want to keep existing data)
TRUNCATE TABLE action_plans RESTART IDENTITY CASCADE;

-- Insert mock action plans
INSERT INTO action_plans (store_name, store_location, issue_description, status, plan_content, error_message, created_at, updated_at) VALUES

-- Record 1: Completed - Refrigeration Issue
('Walmart Supercenter #2547', 'Houston, TX - West Loop', 
'Refrigeration units in produce section experiencing temperature fluctuations between 38-45°F. Fresh vegetables showing premature wilting. Customer complaints increased by 23% this week.',
'completed',
'**IMMEDIATE ACTIONS**

1. Emergency Temperature Control
   - Schedule HVAC technician within 24 hours for unit inspection
   - Move high-risk produce (leafy greens, berries) to backup refrigeration
   - Install temporary temperature monitoring devices

2. Inventory Management
   - Conduct full produce quality audit and remove compromised items
   - Reduce produce orders by 30% until issue resolved
   - Document all waste for insurance claim

3. Customer Communication
   - Post signage about temporary produce section adjustments
   - Train staff to offer substitutions and discounts proactively
   - Monitor social media and address complaints within 2 hours',
NULL,
NOW() - INTERVAL '5 days',
NOW() - INTERVAL '5 days'),

-- Record 2: Completed - Checkout Issues
('Target Store #T-1843', 'San Francisco, CA - Union Square',
'Peak hour checkout wait times averaging 12-15 minutes. Self-checkout machines frequently malfunction. Staff shortage during 5-7 PM rush.',
'completed',
'**CHECKOUT OPTIMIZATION PLAN**

1. Immediate Staffing Solution
   - Deploy 2 additional cashiers during 4-8 PM shifts
   - Cross-train floor staff for emergency checkout support
   - Implement dynamic scheduling based on real-time traffic

2. Self-Checkout Fixes
   - Schedule vendor maintenance for all 6 machines this week
   - Add bilingual help signage with troubleshooting QR codes
   - Station a roaming assistant near self-checkout area

3. Customer Flow Management
   - Install queue management system with digital wait time displays
   - Create express lane (10 items or less) enforcement
   - Offer "skip the line" mobile checkout pilot program',
NULL,
NOW() - INTERVAL '4 days',
NOW() - INTERVAL '4 days'),

-- Record 3: Completed - Parking Issues
('Costco Warehouse #456', 'Seattle, WA - Issaquah',
'Parking lot congestion causing 20-minute delays on weekends. Members complaining about difficulty finding spots. Safety concerns with pedestrian traffic.',
'completed',
'**PARKING & TRAFFIC OPTIMIZATION**

1. Traffic Flow Redesign
   - Hire traffic control staff for Saturday-Sunday 10 AM - 4 PM
   - Implement one-way traffic lanes in parking lot
   - Install directional signage and lane markers this week

2. Capacity Management
   - Deploy parking space sensors with real-time availability app
   - Reserve front row for pickup orders and disabled parking only
   - Create overflow parking plan with shuttle service

3. Peak Load Reduction
   - Launch "Early Bird" promotion: 10% off before 10 AM on Saturdays
   - Send push notifications to members about real-time crowd levels
   - Test weekday evening extended hours to redistribute traffic',
NULL,
NOW() - INTERVAL '3 days',
NOW() - INTERVAL '3 days'),

-- Record 4: Completed - Supply Chain Issues
('Whole Foods Market #10234', 'Austin, TX - Downtown',
'Organic produce delivery delayed 3 days due to supplier issues. Popular items out of stock. Customer loyalty scores dropping.',
'completed',
'**SUPPLY CHAIN RECOVERY PLAN**

1. Emergency Sourcing
   - Contact backup suppliers for immediate delivery (24-48 hours)
   - Partner with 3 local organic farms for temporary supply
   - Authorize 15% premium pricing for expedited sourcing

2. Customer Retention
   - Offer 20% discount vouchers to affected customers via app
   - Create "coming soon" labels with expected restock dates
   - Promote available alternative organic products

3. Supplier Relationship
   - Schedule call with primary supplier to prevent recurrence
   - Negotiate service level agreement with penalty clauses
   - Diversify supplier base to reduce single-point dependency',
NULL,
NOW() - INTERVAL '2 days',
NOW() - INTERVAL '2 days'),

-- Record 5: Completed - Pharmacy Issues
('CVS Pharmacy #8821', 'Boston, MA - Back Bay',
'Pharmacy prescription fulfillment taking 45+ minutes. Long queues at pharmacy counter. Insurance verification system experiencing frequent downtime.',
'completed',
'**PHARMACY OPERATIONS IMPROVEMENT**

1. System & Process Fixes
   - Escalate IT ticket for insurance verification system (priority 1)
   - Implement backup manual verification process during downtime
   - Add second pharmacy terminal to reduce bottlenecks

2. Staffing & Workflow
   - Hire part-time pharmacy technician for peak hours (12-2 PM, 5-7 PM)
   - Create prescription ready notification system via SMS
   - Separate pickup and drop-off windows at counter

3. Customer Experience
   - Deploy text alert system when prescriptions are ready
   - Set up comfortable waiting area with seating
   - Offer free delivery for prescriptions delayed over 1 hour',
NULL,
NOW() - INTERVAL '1 day',
NOW() - INTERVAL '1 day'),

-- Record 6: Pending - No plan generated yet
('Best Buy #1547', 'Los Angeles, CA - Beverly Center',
'High return rate (18%) on electronics due to customers not understanding setup. Geek Squad overwhelmed with basic installation questions.',
'pending',
NULL,
NULL,
NOW() - INTERVAL '3 hours',
NOW() - INTERVAL '3 hours'),

-- Record 7: Processing - Currently being processed
('Home Depot #4422', 'Phoenix, AZ - Tempe',
'Lumber yard organization chaotic after renovation. Staff unable to locate specific items quickly. Order fulfillment time doubled from 15 to 30 minutes.',
'processing',
NULL,
NULL,
NOW() - INTERVAL '10 minutes',
NOW() - INTERVAL '5 minutes'),

-- Record 8: Failed - Error occurred
('Trader Joe''s #534', 'Portland, OR - Pearl District',
'Popular seasonal items selling out by 2 PM daily. Customer frustration with inconsistent restocking. Staff receiving complaints about product availability.',
'failed',
NULL,
'API timeout: Unable to generate action plan due to network connectivity issues.',
NOW() - INTERVAL '1 hour',
NOW() - INTERVAL '1 hour'),

-- Record 9: Completed - Deli Issues
('Safeway #1920', 'Denver, CO - Capitol Hill',
'Deli counter running out of prepared foods by 6 PM. Evening shoppers leaving empty-handed. Lost revenue estimated at $2,000/week.',
'completed',
'**DELI PRODUCTION OPTIMIZATION**

1. Demand Forecasting
   - Analyze sales data from past 90 days to identify peak items
   - Increase evening production batch by 40%
   - Implement second production run at 4 PM for high-demand items

2. Product Mix Strategy
   - Create "Evening Specials" menu with items that hold well
   - Pre-package popular items in multiple sizes
   - Cross-train staff to prepare top 10 items quickly

3. Marketing & Communication
   - Launch "Reserve Your Dinner" pre-order system via app
   - Offer 15% discount on pre-orders placed before 3 PM
   - Display production schedule so customers know when fresh batches arrive',
NULL,
NOW() - INTERVAL '6 hours',
NOW() - INTERVAL '6 hours'),

-- Record 10: Completed - Stocking Issues
('Kroger #782', 'Atlanta, GA - Midtown',
'Night shift stocking crew leaving aisles blocked until morning. Safety hazard and customer dissatisfaction during early hours (6-9 AM).',
'completed',
'**STOCKING OPERATIONS RESTRUCTURE**

1. Workflow Optimization
   - Implement "aisle-complete" protocol before moving to next section
   - Deploy rolling carts instead of pallets during operating hours
   - Create clear zones: stocking vs customer priority areas

2. Scheduling Adjustment
   - Shift 60% of stocking to 10 PM - 4 AM when store is closed
   - Assign dedicated "clean-up crew" for 5:30-7 AM to clear all equipment
   - Use morning crew for facing/organizing rather than heavy stocking

3. Training & Accountability
   - Implement photo checklist: "before leaving" aisle documentation
   - Reward crew for zero customer complaints in a week
   - Schedule manager walk-through at 6 AM to verify readiness',
NULL,
NOW() - INTERVAL '12 hours',
NOW() - INTERVAL '12 hours');

-- Verify the data was inserted
SELECT COUNT(*) as total_records FROM action_plans;
SELECT status, COUNT(*) as count FROM action_plans GROUP BY status;
