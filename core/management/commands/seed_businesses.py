import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

# UPDATE THESE IMPORTS TO MATCH YOUR APP STRUCTURE
from businesses.models import Business
from categories.models import Category
from locations.models import City

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with 100 realistic demo businesses'

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        self.stdout.write("Checking dependencies...")

        # 1. Ensure we have at least one User to own the businesses
        user = User.objects.first()
        if not user:
            self.stdout.write("No users found. Creating a dummy 'demo_owner' user...")
            user = User.objects.create_user(username='demo_owner', password='password123', email='demo@example.com')

        # 2. Ensure we have at least one City
        cities = list(City.objects.all())
        if not cities:
            self.stdout.write("No cities found. Creating a dummy city 'Demo City'...")
            dummy_city = City.objects.create(name='Demo City', slug='demo-city')
            cities = [dummy_city]

        # 3. Ensure we have Categories
        categories = list(Category.objects.filter(is_active=True))
        if not categories:
            self.stdout.write(self.style.ERROR("No active categories found! Please run your category seed script first."))
            return

        self.stdout.write(self.style.WARNING("Starting business generation. This may take a few seconds..."))

        created_count = 0

        # Wrap in an atomic transaction for speed and safety
        with transaction.atomic():
            for _ in range(100):
                # Generate strict phone numbers to match your regex: ^\+?1?\d{9,15}$
                fake_phone_1 = f"+1{fake.numerify('##########')}"
                fake_phone_2 = f"+1{fake.numerify('##########')}" if random.choice([True, False]) else ""

                # Pick a random status, heavily weighted towards APPROVED for UI testing
                status_choice = random.choices(
                    population=[Business.Status.APPROVED, Business.Status.PENDING, Business.Status.DRAFT],
                    weights=[80, 15, 5],
                    k=1
                )[0]

                # Generate a realistic but random average rating (e.g., 3.5 to 5.0)
                random_rating = round(random.uniform(3.0, 5.0), 2) if random.choice([True, False]) else 0.00
                random_reviews = random.randint(1, 500) if random_rating > 0 else 0

                # Create the business instance
                business = Business(
                    owner=user,
                    name=fake.company(),
                    description=fake.paragraph(nb_sentences=5),
                    
                    # Contact Info
                    phone_number=fake_phone_1,
                    phone_number_2=fake_phone_2,
                    email=fake.company_email(),
                    website=fake.url() if random.choice([True, False]) else "",
                    
                    # Location
                    address_line_1=fake.street_address(),
                    address_line_2=fake.secondary_address() if random.choice([True, False]) else "",
                    city=random.choice(cities),
                    postal_code=fake.postcode(),
                    latitude=fake.latitude(),
                    longitude=fake.longitude(),
                    
                    # Social Links JSON
                    social_links={
                        "facebook": f"https://facebook.com/{fake.slug()}",
                        "instagram": f"https://instagram.com/{fake.slug()}",
                    } if random.choice([True, False]) else {},
                    
                    # Metrics & Status
                    status=status_choice,
                    is_verified=random.choices([True, False], weights=[30, 70])[0],
                    is_active=True,
                    average_rating=random_rating,
                    total_reviews=random_reviews,
                    view_count=random.randint(10, 10000)
                )

                # Save the instance. This is required to trigger your AutoSlugMixin.
                business.save()

                # Assign 1 to 3 random categories via ManyToMany
                assigned_categories = random.sample(categories, k=random.randint(1, 3))
                business.categories.set(assigned_categories)
                
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} demo businesses!'))