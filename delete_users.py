import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from django.db import transaction
from django.apps import apps
from home.models import Users, RoleUsers

target_uids = [13616, 13608, 13604, 13596]
backup_admin_id = 1

print("Starting user deletion and reference reassignment transaction...")

try:
    with transaction.atomic(using='default'):
        # 1. Promote backup admin to superuser and staff
        backup_admin = Users.objects.get(id=backup_admin_id)
        backup_admin.is_superuser = True
        backup_admin.is_staff = True
        backup_admin.save()
        print(f"Promoted backup admin: ID: {backup_admin.id}, Username: {backup_admin.username}, Email: {backup_admin.email}")

        # 2. Reassign content references in all other tables
        all_models = apps.get_models(include_auto_created=True)
        for model in all_models:
            if model == Users:
                continue
                
            # Check fields
            user_fields = []
            for f in model._meta.get_fields():
                if f.is_relation and f.related_model == Users:
                    if f.many_to_one or f.one_to_one:
                        user_fields.append(f.name + '_id')
            
            if user_fields:
                for uf in user_fields:
                    try:
                        # Find records referencing target users
                        reassign_count = model.objects.filter(**{f'{uf}__in': target_uids}).update(**{uf: backup_admin_id})
                        if reassign_count > 0:
                            print(f"Reassigned {reassign_count} records in {model.__name__} ({model._meta.db_table}) field {uf} to User 1")
                    except Exception as e:
                        print(f"Failed to reassign {model.__name__}.{uf}: {e}")

        # 3. Delete role mappings for the target users
        role_delete_count, _ = RoleUsers.objects.filter(user_id__in=target_uids).delete()
        print(f"Deleted {role_delete_count} role mapping records from role_users")

        # 4. Delete the target users
        user_delete_count, _ = Users.objects.filter(id__in=target_uids).delete()
        print(f"Successfully deleted {user_delete_count} users from the database")

    print("\nUSER DELETION AND REASSIGNMENT COMPLETED SUCCESSFULLY!")

except Exception as e:
    print(f"\nOPERATION FAILED: {e}")
    exit(1)
