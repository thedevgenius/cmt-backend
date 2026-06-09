import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# UPDATE THIS IMPORT TO MATCH YOUR APP NAME
from categories.models import Category 

class Command(BaseCommand):
    help = 'Seeds the database with the category hierarchy from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file', 
            type=str, 
            help='The path to the directory_categories.json file'
        )

    def handle(self, *args, **kwargs):
        json_file_path = kwargs['json_file']

        if not os.path.exists(json_file_path):
            raise CommandError(f'File "{json_file_path}" does not exist.')

        with open(json_file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                raise CommandError('Invalid JSON file.')

        categories_data = data.get('categories', [])
        if not categories_data:
            self.stdout.write(self.style.WARNING('No categories found in the JSON.'))
            return

        self.stdout.write('Starting category seeding process...')
        
        # Track counts for the summary
        created_roots = 0
        created_children = 0
        created_grandchildren = 0

        # transaction.atomic() ensures that if anything fails, the database rolls back
        with transaction.atomic():
            for root_index, root_data in enumerate(categories_data):
                root_name = root_data.get('name')
                
                # 1. Create or Get Root Category (Level 1)
                root_category, created = Category.objects.get_or_create(
                    name=root_name,
                    parent=None,
                    defaults={
                        'sort_order': root_index,
                        # If you re-enable the icon field later, you can map the string here:
                        # 'icon_name': root_data.get('icon') 
                    }
                )
                if created: created_roots += 1

                children_data = root_data.get('children', [])
                
                for child_index, child_data in enumerate(children_data):
                    child_name = child_data.get('name')
                    
                    # 2. Create or Get Child Category (Level 2)
                    child_category, created = Category.objects.get_or_create(
                        name=child_name,
                        parent=root_category,
                        defaults={'sort_order': child_index}
                    )
                    if created: created_children += 1

                    subcategories_data = child_data.get('subcategories', [])
                    
                    for sub_index, sub_name in enumerate(subcategories_data):
                        # 3. Create or Get Subcategory (Level 3)
                        _, created = Category.objects.get_or_create(
                            name=sub_name,
                            parent=child_category,
                            defaults={'sort_order': sub_index}
                        )
                        if created: created_grandchildren += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded database!\n'
            f'- Created Root Categories: {created_roots}\n'
            f'- Created Child Categories: {created_children}\n'
            f'- Created Grandchild Categories: {created_grandchildren}'
        ))