from django.contrib import admin
from .models import (Batch, Palletization, Product, Carton, InnerPack,
                     PalletizationInstruction, ErrorReport, SiteInfo, Customer,
                     Task, Notification, RecurringTask, UserProfile, PowerBIToken,
                     UserModuleAccess, DemoVisitor,
                     EscalationRoute,
                     PackagingIssue, ProductAlias, DictionaryEntry)


@admin.register(DemoVisitor)
class DemoVisitorAdmin(admin.ModelAdmin):
    """Lista odwiedzających demo — tylko do odczytu (dane osobowe, retencja 90 dni)."""
    list_display = ("created_at", "last_name", "first_name", "company")
    ordering = ("-created_at",)
    search_fields = ("last_name", "first_name", "company")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.groups.filter(name="Administratorzy").exists()

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


@admin.register(UserModuleAccess)
class UserModuleAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "module_key", "allowed", "updated_at")
    list_filter = ("module_key", "allowed")
    search_fields = ("user__username", "module_key")


@admin.register(RecurringTask)
class RecurringTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "interval", "next_run", "assignee", "priority", "is_active")
    list_filter = ("interval", "is_active")
    list_editable = ("is_active",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "priority", "status", "assignee", "created_at")
    list_filter = ("status", "category", "priority")
    search_fields = ("title", "source_ref", "dedup_key")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "level", "is_read", "created_at")
    list_filter = ("level", "is_read")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "kind", "city", "max_pallet_height_cm",
                    "requires_fumigated_pallet", "is_active")
    list_filter = ("kind", "is_active", "requires_fumigated_pallet")
    search_fields = ("name", "code", "city")


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "leaders")


@admin.register(PowerBIToken)
class PowerBITokenAdmin(admin.ModelAdmin):
    list_display = ("__str__", "account", "updated_at")
    readonly_fields = ("updated_at",)
    exclude = ("cache",)   # SEC-011: refresh token nie jest wyświetlany ani edytowalny


@admin.register(InnerPack)
class InnerPackAdmin(admin.ModelAdmin):
    list_display = ("name", "length_cm", "width_cm", "height_cm", "units_per_pack", "tare_kg", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "pallet_code", "max_height_total_cm")


@admin.register(Palletization)
class PalletizationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "sku", "variant", "carton_l", "carton_w", "carton_h")


class ProductAliasInline(admin.TabularInline):
    model = ProductAlias
    extra = 1
    fields = ("alias_code", "note")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "ean", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "ean")
    ordering = ("code",)
    inlines = [ProductAliasInline]


@admin.register(ProductAlias)
class ProductAliasAdmin(admin.ModelAdmin):
    list_display = ("alias_code", "product", "note", "created_at")
    search_fields = ("alias_code", "product__code", "product__name")
    raw_id_fields = ("product",)
    ordering = ("alias_code",)


@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "category", "group")
    list_filter = ("category", "group")
    search_fields = ("code", "label", "group")
    ordering = ("category", "group", "code")


@admin.register(Carton)
class CartonAdmin(admin.ModelAdmin):
    list_display = ("name", "length_cm", "width_cm", "height_cm", "unit_weight_kg", "pieces_per_carton", "inner_pack", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "ean")
    raw_id_fields = ("inner_pack",)


@admin.register(PalletizationInstruction)
class PalletizationInstructionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "product", "version", "pallet_code", "is_active", "updated_at")
    list_filter = ("is_active", "pallet_code")
    search_fields = ("product__code", "product__name", "name")
    raw_id_fields = ("product", "carton")
    ordering = ("product", "version")


@admin.register(ErrorReport)
class ErrorReportAdmin(admin.ModelAdmin):
    list_display = ("id", "product_code", "reporter_name", "reporter_location", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("product_code", "reporter_name", "description")
    ordering = ("-created_at",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "section", "allowed_sections", "email_notifications")
    list_filter = ("email_notifications", "section")
    search_fields = ("user__username", "phone")


@admin.register(EscalationRoute)
class EscalationRouteAdmin(admin.ModelAdmin):
    """Mapa eskalacji niekompletnych przesyłek — kto dostaje Task per typ magazynu."""
    list_display = ("warehouse_type", "picking_leader", "area_leader",
                    "shift_manager", "escalate_after_minutes")


@admin.register(PackagingIssue)
class PackagingIssueAdmin(admin.ModelAdmin):
    """Zgłoszenia PHV — tu opiekun master daty zmienia status i dodaje notatkę rozwiązania."""
    list_display = ("id", "ref_code", "issue_type", "status", "reporter", "created_at")
    list_filter = ("issue_type", "status")
    search_fields = ("ref_code", "description", "reporter__username")
