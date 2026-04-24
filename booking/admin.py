from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from .models import Event, Seat, Booking, Waitlist
from django.db.models import Sum
import csv
from django.http import HttpResponse
# --- SEAT ADMIN ---
@admin.action(description="Mark selected seats as BOOKED")
def mark_as_booked(modeladmin, request, queryset):
    queryset.update(status="BOOKED")

@admin.action(description="Mark selected seats as AVAILABLE")
def mark_as_available(modeladmin, request, queryset):
    queryset.update(status="AVAILABLE")

class SeatAdmin(admin.ModelAdmin):
    list_display = ("event", "row", "number", "status")
    list_filter = ("status", "row")
    actions = [mark_as_booked, mark_as_available]

admin.site.register(Seat, SeatAdmin)

@admin.action(description='Export Selected Bookings to CSV')
def export_bookings_to_csv(modeladmin, request, queryset):
    # 1. Setup the response to be a CSV file
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="confirmed_bookings.csv"'

    writer = csv.writer(response)

    # 2. Write the Header Row
    writer.writerow(['Customer Name', 'Status', 'Quantity', 'Phone', 'Email', 'Payment ID'])

    # 3. Write the Data Rows
    for booking in queryset:
        writer.writerow([
            booking.customer_name,
            booking.status,
            booking.quantity,
            booking.phone,
            booking.email,
            booking.razorpay_payment_id,
        ])

    return response

# --- BOOKING ADMIN ---
class BookingAdmin(admin.ModelAdmin):
    # --- ADD THIS BLOCK INSIDE BookingAdmin ---
    def changelist_view(self, request, extra_context=None):
        # 1. Calculate the numbers
        total_seats = 86
        # Sum all CONFIRMED bookings
        sold = Booking.objects.filter(status='CONFIRMED').aggregate(Sum('quantity'))['quantity__sum']
        if sold is None:
            sold = 0
        available = total_seats - sold

        # 2. Create the message
        msg = f"📊 LIVE STATUS: Total Seats: {total_seats}   |   ✅ Sold: {sold}   |   🟢 Available: {available}"

        # 3. Show it at the top of the page (as a persistent notification)
        self.message_user(request, msg, level='WARNING')

        # 4. Load the page as usual
        return super().changelist_view(request, extra_context=extra_context)
    # Added 'quantity' to the list
    list_display = ('customer_name','status','quantity', 'email', 'phone',   'razorpay_payment_id')
    list_filter = ('status',)
    search_fields = ('customer_name', 'email')
    actions = [export_bookings_to_csv]
    def save_model(self, request, obj, form, change):
        if change:
            try:
                old_version = Booking.objects.get(pk=obj.pk)

                # Check if changed to CONFIRMED
                if old_version.status != 'CONFIRMED' and obj.status == 'CONFIRMED':
                    self.send_confirmation_email(obj)
            except Booking.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

    def send_confirmation_email(self, booking):
        subject = f"Booking Confirmed! (ID: {booking.id})"

        # Now we can use {booking.quantity} safely!
        message = (
            f"Hello {booking.customer_name},\n\n"
            f"We have received your payment for {booking.quantity} ticket(s).\n"
            f"Your booking is now CONFIRMED for Gopal Gatha show.\n\n"
            f"Seating is on a First-Come-First basis.\n\n"
            f"Kindly be seated by 7:15 pm\n\n"
            f"Date : 23rd January 2026, Friday\n\n"
            f"Venue : The Box Too, Erandwane, Pune\n\n"
            f"Time : 7:30 pm - 9:00 pm\n\n"
            f"You are requested to show this confirmation email at the entrance. \n\n"


            f"Thank you!"
        )

        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [booking.email], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")

# --- EVENT ADMIN (NEW: Shows Stats) ---
class EventAdmin(admin.ModelAdmin):
    # Columns to show in the Event list
    list_display = ('name', 'total_capacity_display', 'confirmed_booked', 'actual_available')

    # 1. Total Capacity (Hardcoded to 86)
    def total_capacity_display(self, obj):
        return 86
    total_capacity_display.short_description = "Total Seats"

    # 2. CONFIRMED ONLY (Sold)
    def confirmed_booked(self, obj):
        # Counts only bookings where status is 'Confirmed'
        booked = Booking.objects.filter(event=obj, status='CONFIRMED').aggregate(Sum('quantity'))['quantity__sum']
        return booked if booked else 0
    confirmed_booked.short_description = "✅ Confirmed Sold"

    # 3. AVAILABLE (Total - Confirmed)
    def actual_available(self, obj):
        confirmed = self.confirmed_booked(obj)
        total = self.total_capacity_display(obj)
        # Simple Math: 86 - Sold
        return total - confirmed
    actual_available.short_description = "🟢 Available"
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'timestamp')  # Columns to show
    search_fields = ('name', 'phone')              # Search bar capability
    list_filter = ('timestamp',)                   # Filter by date
    ordering = ('-timestamp',)                     # Newest on top
# Register the Event with these new stats
admin.site.register(Waitlist, WaitlistAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Booking, BookingAdmin)