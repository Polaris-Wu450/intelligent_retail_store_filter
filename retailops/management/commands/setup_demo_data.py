"""
Django management command to set up demo data for the application.

Usage:
    python manage.py setup_demo_data

Options:
    --clear-all     Delete ALL existing data before creating demo data
    --clear-plans   Delete only ActionPlan data (keep stores/customers)
"""
from django.core.management.base import BaseCommand
from retailops.models import Store, Customer, Feedback, ActionPlan
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Set up demo data: stores, customers, and sample action plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Delete ALL existing data before creating demo data',
        )
        parser.add_argument(
            '--clear-plans',
            action='store_true',
            help='Delete only ActionPlan data (keep stores/customers)',
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("🚀 Setting up Demo Data"))
        self.stdout.write("=" * 70 + "\n")

        # Clear data if requested
        if options['clear_all']:
            self.clear_all_data()
        elif options['clear_plans']:
            self.clear_action_plans()

        # Create demo data
        self.create_stores()
        self.create_customers()
        self.create_sample_action_plans()

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ Demo Data Setup Complete!"))
        self.stdout.write("=" * 70 + "\n")
        self.print_summary()

    def clear_all_data(self):
        self.stdout.write(self.style.WARNING("\n🗑️  Clearing ALL existing data..."))
        
        action_plan_count = ActionPlan.objects.count()
        feedback_count = Feedback.objects.count()
        customer_count = Customer.objects.count()
        store_count = Store.objects.count()
        
        ActionPlan.objects.all().delete()
        Feedback.objects.all().delete()
        Customer.objects.all().delete()
        Store.objects.all().delete()
        
        self.stdout.write(f"   Deleted {action_plan_count} action plans")
        self.stdout.write(f"   Deleted {feedback_count} feedbacks")
        self.stdout.write(f"   Deleted {customer_count} customers")
        self.stdout.write(f"   Deleted {store_count} stores\n")

    def clear_action_plans(self):
        self.stdout.write(self.style.WARNING("\n🗑️  Clearing Action Plans only..."))
        count = ActionPlan.objects.count()
        ActionPlan.objects.all().delete()
        self.stdout.write(f"   Deleted {count} action plans\n")

    def create_stores(self):
        self.stdout.write("\n🏪 Creating Stores...")
        
        stores_data = [
            {'store_id': 'NYC001', 'name': 'New York Manhattan Flagship'},
            {'store_id': 'LA001', 'name': 'Los Angeles Downtown Center'},
            {'store_id': 'SF001', 'name': 'San Francisco Union Square'},
            {'store_id': 'CHI001', 'name': 'Chicago Michigan Avenue'},
            {'store_id': 'SEA001', 'name': 'Seattle Pike Place Market'},
        ]
        
        created = 0
        existing = 0
        
        for data in stores_data:
            store, is_created = Store.objects.get_or_create(
                store_id=data['store_id'],
                defaults={'name': data['name']}
            )
            
            if is_created:
                self.stdout.write(f"   ✅ Created: {store.name} ({store.store_id})")
                created += 1
            else:
                self.stdout.write(f"   ⏭️  Exists: {store.name} ({store.store_id})")
                existing += 1
        
        self.stdout.write(f"\n   📊 Stores: {created} created, {existing} already existed")

    def create_customers(self):
        self.stdout.write("\n👥 Creating Customers...")
        
        customers_data = [
            {
                'customer_id': 'C001',
                'first_name': 'John',
                'last_name': 'Smith',
                'phone': '555-0100'
            },
            {
                'customer_id': 'C002',
                'first_name': 'Emma',
                'last_name': 'Johnson',
                'phone': '555-0101'
            },
            {
                'customer_id': 'C003',
                'first_name': 'Michael',
                'last_name': 'Williams',
                'phone': '555-0102'
            },
            {
                'customer_id': 'C004',
                'first_name': 'Sarah',
                'last_name': 'Brown',
                'phone': '555-0103'
            },
            {
                'customer_id': 'C005',
                'first_name': 'David',
                'last_name': 'Garcia',
                'phone': '555-0104'
            },
        ]
        
        created = 0
        existing = 0
        
        for data in customers_data:
            customer, is_created = Customer.objects.get_or_create(
                customer_id=data['customer_id'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone']
                }
            )
            
            if is_created:
                self.stdout.write(
                    f"   ✅ Created: {customer.first_name} {customer.last_name} "
                    f"({customer.customer_id})"
                )
                created += 1
            else:
                self.stdout.write(
                    f"   ⏭️  Exists: {customer.first_name} {customer.last_name} "
                    f"({customer.customer_id})"
                )
                existing += 1
        
        self.stdout.write(f"\n   📊 Customers: {created} created, {existing} already existed")

    def create_sample_action_plans(self):
        self.stdout.write("\n📋 Creating Sample Action Plans...")
        
        action_plans_data = [
            {
                'store_name': 'New York Manhattan Flagship',
                'store_location': '5th Avenue, New York, NY',
                'issue_description': 'Customer complaints about delayed furniture delivery and poor assembly service quality.',
                'status': 'completed',
                'plan_content': '''PROBLEM LIST / ROOT CAUSE ANALYSIS
1. Delivery delays averaging 3-5 days beyond promised dates
2. Assembly service quality inconsistent (missing tools, incomplete work)
3. Customer communication gaps during delivery process

GOALS (SMART)
1. Reduce delivery delays to <24 hours by end of Q2
2. Achieve 95% assembly service satisfaction rating within 60 days
3. Implement automated delivery tracking notifications by March 15

MANAGER INTERVENTIONS / OPERATIONAL PLAN
1. Partner with new logistics provider with proven NYC coverage
2. Conduct mandatory assembly team training (certified techniques)
3. Deploy SMS/email tracking system for real-time customer updates
4. Assign dedicated delivery coordinator for flagship store

MONITORING PLAN & SLA TRACKING
- Weekly delivery performance review (Thursdays 2pm)
- Customer satisfaction surveys (automated post-delivery)
- Monthly assembly quality audits
- Escalation protocol: >2 complaints/week triggers immediate review'''
            },
            {
                'store_name': 'Los Angeles Downtown Center',
                'store_location': 'Broadway, Los Angeles, CA',
                'issue_description': 'Electronics department receiving complaints about defective products and unhelpful return process.',
                'status': 'completed',
                'plan_content': '''PROBLEM LIST / ROOT CAUSE ANALYSIS
1. Defective electronics rate 8% (industry avg: 3%)
2. Return process unclear and time-consuming (45+ min average)
3. Staff lack technical knowledge for troubleshooting
4. Supplier quality control issues identified

GOALS (SMART)
1. Reduce defect rate to <4% within 90 days
2. Streamline return process to <15 minutes by April 1
3. Train 100% of electronics staff on product troubleshooting by March 31

MANAGER INTERVENTIONS / OPERATIONAL PLAN
1. Audit top 5 electronics suppliers; replace underperformers
2. Implement pre-sale product testing station (sample check)
3. Create simplified return kiosk with clear step-by-step signage
4. Partner with manufacturer for staff technical certification program
5. Establish dedicated returns desk for electronics (separate from general)

MONITORING PLAN & SLA TRACKING
- Daily defect rate tracking dashboard
- Weekly supplier quality score review
- Monthly staff certification progress check
- Customer feedback analysis (post-return survey)
- Quarterly supplier performance review meeting'''
            },
            {
                'store_name': 'San Francisco Union Square',
                'store_location': 'Union Square, San Francisco, CA',
                'issue_description': 'Multiple customer reports of incorrect clothing sizes and fit issues, especially with online orders picked up in-store.',
                'status': 'completed',
                'plan_content': '''PROBLEM LIST / ROOT CAUSE ANALYSIS
1. Size discrepancies between online product descriptions and actual items
2. Inconsistent sizing across different clothing brands
3. Limited fitting room availability causing rushed decisions
4. Online order fulfillment picking wrong sizes (human error)

GOALS (SMART)
1. Reduce size-related returns by 40% within 60 days
2. Achieve 98% accuracy in online order fulfillment by April 15
3. Update 100% of online product descriptions with detailed measurements by March 20

MANAGER INTERVENTIONS / OPERATIONAL PLAN
1. Implement barcode scanning for online order picking (eliminate manual entry)
2. Add detailed size charts and fit guides to all online product pages
3. Expand fitting room capacity by 50% (convert storage space)
4. Train staff on brand-specific sizing differences (quick reference cards)
5. Create "try before you buy" policy for online pickup orders
6. Partner with brands to standardize measurement methodology

MONITORING PLAN & SLA TRACKING
- Daily online order accuracy audit (10% sample)
- Weekly size-related return rate tracking
- Customer satisfaction survey focus on fit accuracy
- Monthly training compliance check
- Quarterly brand partnership review for sizing standardization progress'''
            },
            {
                'store_name': 'Chicago Michigan Avenue',
                'store_location': 'Michigan Avenue, Chicago, IL',
                'issue_description': 'Long checkout wait times during peak hours and frequent POS system crashes.',
                'status': 'processing',
                'plan_content': None
            },
            {
                'store_name': 'Seattle Pike Place Market',
                'store_location': 'Pike Place Market, Seattle, WA',
                'issue_description': 'Customer feedback about unhelpful staff and lack of product knowledge in furniture section.',
                'status': 'pending',
                'plan_content': None
            }
        ]
        
        created = 0
        
        for data in action_plans_data:
            # Check if similar plan already exists (avoid duplicates)
            existing = ActionPlan.objects.filter(
                store_name=data['store_name'],
                issue_description=data['issue_description']
            ).first()
            
            if not existing:
                # Create plan with appropriate timestamps
                created_at = timezone.now() - timedelta(days=created * 2)  # Stagger dates
                
                plan = ActionPlan.objects.create(
                    store_name=data['store_name'],
                    store_location=data['store_location'],
                    issue_description=data['issue_description'],
                    status=data['status'],
                    plan_content=data['plan_content'],
                    created_at=created_at,
                    updated_at=created_at
                )
                
                status_emoji = {
                    'completed': '✅',
                    'processing': '⏳',
                    'pending': '⏸️',
                    'failed': '❌'
                }.get(data['status'], '📋')
                
                self.stdout.write(
                    f"   {status_emoji} Created: {plan.store_name} - "
                    f"{data['issue_description'][:50]}... ({plan.status})"
                )
                created += 1
            else:
                self.stdout.write(
                    f"   ⏭️  Exists: {data['store_name']} - "
                    f"{data['issue_description'][:50]}..."
                )
        
        self.stdout.write(f"\n   📊 Action Plans: {created} created")

    def print_summary(self):
        self.stdout.write("\n📊 Current Database Status:")
        self.stdout.write(f"   🏪 Stores: {Store.objects.count()}")
        self.stdout.write(f"   👥 Customers: {Customer.objects.count()}")
        self.stdout.write(f"   💬 Feedbacks: {Feedback.objects.count()}")
        self.stdout.write(f"   📋 Action Plans: {ActionPlan.objects.count()}")
        
        # Breakdown by status
        for status, label in ActionPlan.STATUS_CHOICES:
            count = ActionPlan.objects.filter(status=status).count()
            if count > 0:
                status_emoji = {
                    'pending': '⏸️',
                    'processing': '⏳',
                    'completed': '✅',
                    'failed': '❌'
                }.get(status, '📋')
                self.stdout.write(f"      {status_emoji} {label}: {count}")
        
        self.stdout.write("\n💡 Tips:")
        self.stdout.write("   - Visit http://localhost:3001 to see the React frontend")
        self.stdout.write("   - Use Django admin to manage data: http://localhost:8000/admin")
        self.stdout.write("   - Run with --clear-all to reset all data")
        self.stdout.write("   - Run with --clear-plans to keep stores/customers\n")
