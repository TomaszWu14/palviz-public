# Agregator zgodnosci (W3): pociety na submoduly, importy dzialaja bez zmian.
from .admin_users import (
    admin_panel, admin_users, admin_user_form, admin_users_import, admin_user_delete,
    admin_user_toggle_active, admin_module_access, admin_role_matrix, admin_control_zones,
    _online_user_ids,  # noqa: F401 (not star-exported, but huctl/views/hu_leader.py imports it directly)
)
from .admin_misc import admin_positions, admin_import_status, admin_position_form, admin_access_audit

__all__ = [
    'admin_panel',
    'admin_users',
    'admin_user_form',
    'admin_users_import',
    'admin_user_delete',
    'admin_user_toggle_active',
    'admin_module_access',
    'admin_role_matrix',
    'admin_positions',
    'admin_import_status',
    'admin_position_form',
    'admin_control_zones',
    'admin_access_audit',
]
