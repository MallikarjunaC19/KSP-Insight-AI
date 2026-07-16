"""
KSP Insight AI — Set up RBAC Groups with base Django permissions

Django admin checks TWO layers of permission —
(1) base view/add/change/delete permission via Groups (standard Django),
(2) our custom ScopedAdminMixin/OwnRecordAdminMixin, which narrows down
what a user sees ONCE they already have base permission.
Without Groups, a non-superuser staff user has zero base permissions
and gets "You don't have permission to view or edit anything" even
though our custom scoping logic is correctly written.

Permission levels:
    CONSTABLE          -> view only (matches "read-only on cases" design)
    STATION_OFFICER      -> view, add, change (no delete)
    SP_DIG                -> view, add, change (no delete)
    DGP                    -> view, add, change, delete (full access)
    SCRB_ANALYST          -> view only (matches "read-only analytics" design)

"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

from accounts.models import Role, Officer


# Apps whose models should be covered by these groups
MANAGED_APPS = ["accounts", "crimes", "investigations", "persons", "assets", "assistant"]

# role code -> permission levels to grant
ROLE_PERMISSION_LEVELS = {
    Role.RoleCode.CONSTABLE: ["view"],
    Role.RoleCode.STATION_OFFICER: ["view", "add", "change"],
    Role.RoleCode.SP_DIG: ["view", "add", "change"],
    Role.RoleCode.DGP: ["view", "add", "change", "delete"],
    Role.RoleCode.SCRB_ANALYST: ["view"],
}

GROUP_NAME_FOR_ROLE = {
    Role.RoleCode.CONSTABLE: "Constable",
    Role.RoleCode.STATION_OFFICER: "Station Officer",
    Role.RoleCode.SP_DIG: "SP / DIG",
    Role.RoleCode.DGP: "DGP",
    Role.RoleCode.SCRB_ANALYST: "SCRB Analyst",
}


class Command(BaseCommand):
    help = "Create Groups with base permissions matching the 5 RBAC roles, and assign officers to them"

    def handle(self, *args, **options):
        all_models = self.get_all_managed_models()

        for role_code, actions in ROLE_PERMISSION_LEVELS.items():
            group_name = GROUP_NAME_FOR_ROLE[role_code]
            group, created = Group.objects.get_or_create(name=group_name)
            self.stdout.write(f"{'Created' if created else 'Updating'} group: {group_name}")

            permissions = []
            for model in all_models:
                content_type = ContentType.objects.get_for_model(model)
                for action in actions:
                    codename = f"{action}_{model._meta.model_name}"
                    try:
                        perm = Permission.objects.get(content_type=content_type, codename=codename)
                        permissions.append(perm)
                    except Permission.DoesNotExist:
                        continue  # shouldn't happen, but don't crash the whole command over one model

            group.permissions.set(permissions)
            self.stdout.write(f"  -> granted {len(permissions)} permissions ({', '.join(actions)})")

        self.stdout.write("Assigning officers to groups...")
        assigned = 0
        for officer in Officer.objects.select_related("role", "user").all():
            group_name = GROUP_NAME_FOR_ROLE.get(officer.role.name)
            if not group_name:
                continue
            group = Group.objects.get(name=group_name)
            officer.user.groups.add(group)
            assigned += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. 5 groups configured, {assigned} officers assigned. "
            "Log in as any seeded officer and /admin/ should now show their scoped data."
        ))

    def get_all_managed_models(self):
        models = []
        for app_label in MANAGED_APPS:
            models.extend(apps.get_app_config(app_label).get_models())
        return models