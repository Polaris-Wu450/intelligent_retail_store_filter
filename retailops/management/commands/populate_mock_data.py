from django.core.management.base import BaseCommand
from django.utils import timezone
from retailops.models import ActionPlan


class Command(BaseCommand):
    help = 'Populate database with mock action plan data'

    def handle(self, *args, **kwargs):
        mock_data = [
            {
                'store_name': 'Walmart Supercenter #2547',
                'store_location': 'Houston, TX - West Loop',
                'issue_description': 'Refrigeration units in produce section experiencing temperature fluctuations between 38-45°F. Fresh vegetables showing premature wilting. Customer complaints increased by 23% this week.',
                'status': 'completed',
                'plan_content': '''**IMMEDIATE ACTIONS**

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
   - Monitor social media and address complaints within 2 hours''',
            },
            {
                'store_name': 'Target Store #T-1843',
                'store_location': 'San Francisco, CA - Union Square',
                'issue_description': 'Peak hour checkout wait times averaging 12-15 minutes. Self-checkout machines frequently malfunction. Staff shortage during 5-7 PM rush.',
                'status': 'completed',
                'plan_content': '''**CHECKOUT OPTIMIZATION PLAN**

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
   - Offer "skip the line" mobile checkout pilot program''',
            },
            {
                'store_name': 'Costco Warehouse #456',
                'store_location': 'Seattle, WA - Issaquah',
                'issue_description': 'Parking lot congestion causing 20-minute delays on weekends. Members complaining about difficulty finding spots. Safety concerns with pedestrian traffic.',
                'status': 'completed',
                'plan_content': '''**PARKING & TRAFFIC OPTIMIZATION**

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
   - Test weekday evening extended hours to redistribute traffic''',
            },
            {
                'store_name': 'Whole Foods Market #10234',
                'store_location': 'Austin, TX - Downtown',
                'issue_description': 'Organic produce delivery delayed 3 days due to supplier issues. Popular items out of stock. Customer loyalty scores dropping.',
                'status': 'completed',
                'plan_content': '''**SUPPLY CHAIN RECOVERY PLAN**

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
   - Diversify supplier base to reduce single-point dependency''',
            },
            {
                'store_name': 'CVS Pharmacy #8821',
                'store_location': 'Boston, MA - Back Bay',
                'issue_description': 'Pharmacy prescription fulfillment taking 45+ minutes. Long queues at pharmacy counter. Insurance verification system experiencing frequent downtime.',
                'status': 'completed',
                'plan_content': '''**PHARMACY OPERATIONS IMPROVEMENT**

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
   - Offer free delivery for prescriptions delayed over 1 hour''',
            },
            {
                'store_name': 'Best Buy #1547',
                'store_location': 'Los Angeles, CA - Beverly Center',
                'issue_description': 'High return rate (18%) on electronics due to customers not understanding setup. Geek Squad overwhelmed with basic installation questions.',
                'status': 'pending',
                'plan_content': None,
            },
            {
                'store_name': 'Home Depot #4422',
                'store_location': 'Phoenix, AZ - Tempe',
                'issue_description': 'Lumber yard organization chaotic after renovation. Staff unable to locate specific items quickly. Order fulfillment time doubled from 15 to 30 minutes.',
                'status': 'processing',
                'plan_content': None,
            },
            {
                'store_name': 'Trader Joe\'s #534',
                'store_location': 'Portland, OR - Pearl District',
                'issue_description': 'Popular seasonal items selling out by 2 PM daily. Customer frustration with inconsistent restocking. Staff receiving complaints about product availability.',
                'status': 'failed',
                'error_message': 'API timeout: Unable to generate action plan due to network connectivity issues.',
            },
            {
                'store_name': 'Safeway #1920',
                'store_location': 'Denver, CO - Capitol Hill',
                'issue_description': 'Deli counter running out of prepared foods by 6 PM. Evening shoppers leaving empty-handed. Lost revenue estimated at $2,000/week.',
                'status': 'completed',
                'plan_content': '''**DELI PRODUCTION OPTIMIZATION**

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
   - Display production schedule so customers know when fresh batches arrive''',
            },
            {
                'store_name': 'Kroger #782',
                'store_location': 'Atlanta, GA - Midtown',
                'issue_description': 'Night shift stocking crew leaving aisles blocked until morning. Safety hazard and customer dissatisfaction during early hours (6-9 AM).',
                'status': 'completed',
                'plan_content': '''**STOCKING OPERATIONS RESTRUCTURE**

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
   - Schedule manager walk-through at 6 AM to verify readiness''',
            },
        ]

        self.stdout.write(self.style.WARNING('Clearing existing action plans...'))
        ActionPlan.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Creating mock action plans...'))
        created_count = 0
        for data in mock_data:
            ActionPlan.objects.create(**data)
            created_count += 1
            self.stdout.write(f'  Created: {data["store_name"]}')

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} mock action plans'))
        self.stdout.write(self.style.SUCCESS('You can now view them in TablePlus or through the API'))
