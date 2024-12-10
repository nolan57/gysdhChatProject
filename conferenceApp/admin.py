from django.contrib import admin
from django.utils.html import format_html
from . import models

# Register your models here.

@admin.register(models.Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organizer', 'start_date', 'end_date', 'status', 'is_public']
    list_filter = ['status', 'is_public']
    search_fields = ['name', 'code', 'organizer']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description', 'organizer')
        }),
        ('时间设置', {
            'fields': (
                ('start_date', 'end_date'),
                ('registration_start', 'registration_end'),
                ('check_in_start', 'check_in_end')
            )
        }),
        ('地点信息', {
            'fields': ('venue_name', 'venue_address')
        }),
        ('参会人数', {
            'fields': (
                ('min_participants', 'max_participants'),
                ('company_min_participants', 'company_max_participants')
            )
        }),
        ('状态和设置', {
            'fields': ('status', 'is_public', 'require_approval')
        }),
        ('联系信息', {
            'fields': ('contact_person', 'contact_phone', 'contact_email')
        }),
        ('其他信息', {
            'fields': ('additional_info', 'created_at', 'updated_at')
        }),
    )

@admin.register(models.SupplierCompany)
class SupplierCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'business_type', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(models.ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'position', 'phone', 'is_primary']
    list_filter = ['is_primary', 'company']
    search_fields = ['user__username', 'phone', 'email']

@admin.register(models.Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'position', 'status', 'registration_number']
    list_filter = ['status', 'company']
    search_fields = ['name', 'registration_number', 'phone', 'email']
    readonly_fields = ['registration_number', 'check_in_time']

# 会场管理
@admin.register(models.Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'address']
    search_fields = ['name', 'address']

@admin.register(models.VenueRoom)
class VenueRoomAdmin(admin.ModelAdmin):
    list_display = ['venue', 'name', 'room_type', 'capacity', 'floor']
    list_filter = ['venue', 'room_type']
    search_fields = ['name', 'room_number']

@admin.register(models.Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['room', 'seat_number', 'seat_type', 'row', 'column', 'is_available']
    list_filter = ['room', 'seat_type', 'is_available']
    search_fields = ['seat_number']

@admin.register(models.SeatAssignment)
class SeatAssignmentAdmin(admin.ModelAdmin):
    list_display = ['conference', 'participant', 'seat', 'assigned_at']
    list_filter = ['conference']
    search_fields = ['participant__name', 'seat__seat_number']

# 住宿管理
@admin.register(models.Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'star_rating', 'contact_person', 'contact_phone']
    search_fields = ['name', 'address']

@admin.register(models.RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'name', 'room_type', 'price', 'capacity']
    list_filter = ['hotel', 'room_type']

@admin.register(models.HotelRoom)
class HotelRoomAdmin(admin.ModelAdmin):
    list_display = ['room_type', 'room_number', 'floor', 'status']
    list_filter = ['room_type__hotel', 'status']
    search_fields = ['room_number']

@admin.register(models.Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ['conference', 'participant', 'room', 'check_in_date', 'check_out_date', 'status']
    list_filter = ['conference', 'status']
    search_fields = ['participant__name']

# 餐饮管理
@admin.register(models.Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'capacity', 'contact_person']
    search_fields = ['name', 'location']

@admin.register(models.Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['conference', 'restaurant', 'meal_type', 'date', 'start_time', 'end_time']
    list_filter = ['conference', 'meal_type', 'date']

@admin.register(models.MealOption)
class MealOptionAdmin(admin.ModelAdmin):
    list_display = ['meal', 'name', 'diet_type', 'max_quantity']
    list_filter = ['meal__conference', 'diet_type']

@admin.register(models.MealRegistration)
class MealRegistrationAdmin(admin.ModelAdmin):
    list_display = ['meal', 'participant', 'meal_option', 'status']
    list_filter = ['meal__conference', 'status']
    search_fields = ['participant__name']

# 交通管理
@admin.register(models.Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_type', 'plate_number', 'capacity', 'driver_name']
    list_filter = ['vehicle_type']
    search_fields = ['plate_number', 'driver_name']

@admin.register(models.Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['conference', 'name', 'route_type', 'start_location', 'end_location']
    list_filter = ['conference', 'route_type']
    search_fields = ['name']

@admin.register(models.Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['route', 'vehicle', 'departure_time', 'arrival_time', 'status']
    list_filter = ['route__conference', 'status']

@admin.register(models.TripRegistration)
class TripRegistrationAdmin(admin.ModelAdmin):
    list_display = ['trip', 'participant', 'status', 'luggage_count']
    list_filter = ['trip__route__conference', 'status']
    search_fields = ['participant__name']

# 签到管理
@admin.register(models.CheckInStation)
class CheckInStationAdmin(admin.ModelAdmin):
    list_display = ['conference', 'name', 'location', 'is_active']
    list_filter = ['conference', 'is_active']
    search_fields = ['name', 'location']

@admin.register(models.CheckInRecord)
class CheckInRecordAdmin(admin.ModelAdmin):
    list_display = ['conference', 'participant', 'station', 'check_in_type', 'check_in_time']
    list_filter = ['conference', 'check_in_type']
    search_fields = ['participant__name']
    readonly_fields = ['check_in_time']

@admin.register(models.MaterialCollection)
class MaterialCollectionAdmin(admin.ModelAdmin):
    list_display = ['check_in_record', 'material_type', 'collected_at', 'collected']
    list_filter = ['material_type', 'collected']

# 报名表单管理
@admin.register(models.RegistrationForm)
class RegistrationFormAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_conference', 'is_active', 'start_time', 'end_time', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('时间设置', {
            'fields': ('start_time', 'end_time')
        }),
        ('其他信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_conference(self, obj):
        return obj.conference if hasattr(obj, 'conference') else None
    get_conference.short_description = '关联会议'

@admin.register(models.FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'form', 'field_type', 'required', 'order']
    list_filter = ['form', 'field_type', 'required']
    search_fields = ['label', 'name']
    ordering = ['form', 'order']

@admin.register(models.FieldOption)
class FieldOptionAdmin(admin.ModelAdmin):
    list_display = ['label', 'field', 'value', 'order']
    list_filter = ['field__form']
    search_fields = ['label', 'value']
    ordering = ['field', 'order']

@admin.register(models.FieldLogicRule)
class FieldLogicRuleAdmin(admin.ModelAdmin):
    list_display = ['get_source_field', 'operator', 'get_target_field', 'action']
    list_filter = ['operator', 'action']
    search_fields = ['source_field__label', 'target_field__label']

    def get_source_field(self, obj):
        return obj.source_field.label if obj.source_field else None
    get_source_field.short_description = '源字段'
    get_source_field.admin_order_field = 'source_field__label'

    def get_target_field(self, obj):
        return obj.target_field.label if obj.target_field else None
    get_target_field.short_description = '目标字段'
    get_target_field.admin_order_field = 'target_field__label'
