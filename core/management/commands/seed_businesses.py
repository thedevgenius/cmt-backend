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
    help = 'Seeds the database with 100 localized demo businesses and tiers.'

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        self.stdout.write("Checking dependencies...")

        user = User.objects.first()
        if not user:
            self.stdout.write("No users found. Creating a dummy 'demo_owner' user...")
            user = User.objects.create_user(username='demo_owner', password='password123', email='demo@example.com')

        cities = list(City.objects.all())
        if not cities:
            self.stdout.write("No cities found. Creating a dummy city 'Kolkata'...")
            dummy_city = City.objects.create(name='Kolkata', slug='kolkata')
            cities = [dummy_city]

        categories = list(Category.objects.filter(is_active=True))
        if not categories:
            self.stdout.write(self.style.ERROR("No active categories found! Please run your category seed script first."))
            return

        self.stdout.write(self.style.WARNING("Starting localized business generation..."))

        # Base Coordinates (Kolkata)
        BASE_LAT = 22.525127273142218
        BASE_LON = 88.35620434357554

        created_count = 0

        with transaction.atomic():
            for _ in range(100):
                # 1. Generate Localized Coordinates
                # Offset by +/- ~5km to create a realistic spread around the base point
                lat_offset = random.uniform(-0.05, 0.05)
                lon_offset = random.uniform(-0.05, 0.05)
                
                # 2. Pick Tier and Status
                tier_choice = random.choices(
                    population=[Business.Tier.BASIC, Business.Tier.PRO, Business.Tier.SPONSORED],
                    weights=[70, 20, 10], # 70% Basic, 20% Pro, 10% Sponsored
                    k=1
                )[0]

                status_choice = random.choices(
                    population=[Business.Status.APPROVED, Business.Status.PENDING, Business.Status.DRAFT],
                    weights=[80, 15, 5],
                    k=1
                )[0]

                # 3. Generate Metrics
                random_rating = round(random.uniform(3.0, 5.0), 2) if random.choice([True, False]) else 0.00
                random_reviews = random.randint(1, 500) if random_rating > 0 else 0

                # 4. Create the instance
                business = Business(
                    owner=user,
                    name=fake.company(),
                    description=fake.paragraph(nb_sentences=5),
                    
                    phone_number=f"+1{fake.numerify('##########')}",
                    phone_number_2=f"+1{fake.numerify('##########')}" if random.choice([True, False]) else "",
                    email=fake.company_email(),
                    website=fake.url() if random.choice([True, False]) else "",
                    
                    address_line_1=fake.street_address(),
                    address_line_2=fake.secondary_address() if random.choice([True, False]) else "",
                    city=random.choice(cities),
                    postal_code=fake.postcode(),
                    
                    # Apply the localized coordinates
                    latitude=BASE_LAT + lat_offset,
                    longitude=BASE_LON + lon_offset,
                    
                    social_links={
                        "facebook": f"https://facebook.com/{fake.slug()}",
                        "instagram": f"https://instagram.com/{fake.slug()}",
                    } if random.choice([True, False]) else {},
                    
                    tier=tier_choice,
                    status=status_choice,
                    is_verified=random.choices([True, False], weights=[30, 70])[0],
                    is_active=True,
                    average_rating=random_rating,
                    total_reviews=random_reviews,
                    view_count=random.randint(10, 10000)
                )

                # Calling .save() triggers both AutoSlugMixin AND the pygeohash generation
                business.save()

                assigned_categories = random.sample(categories, k=random.randint(1, 3))
                business.categories.set(assigned_categories)
                
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} localized demo businesses!'))