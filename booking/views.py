from django.shortcuts import render, redirect  # <--- CHANGED: Added redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Sum
from .models import Booking, Event, Waitlist

# --- 1. HOME PAGE ---
def index(request):
    # SET YOUR TOTAL CAPACITY HERE
    total_capacity = 86

    # 2. CALCULATE SOLD SEATS
    sold_data = Booking.objects.filter(status__iexact='confirmed').aggregate(Sum('quantity'))
    sold_count = sold_data['quantity__sum'] or 0

    # 3. CALCULATE REMAINING
    seats_left = total_capacity - sold_count

    # Prevent negative numbers
    if seats_left < 0: seats_left = 0

    # 4. CHECK IF SOLD OUT (New Logic)
    is_sold_out = (seats_left == 0)

    return render(request, 'booking/seat_map_general.html', {
        'seats_left': seats_left,
        'is_sold_out': is_sold_out,  # <--- CHANGED: Passed this to HTML
    })

# --- 2. SUBMIT BOOKING (Existing) ---
@csrf_exempt
def submit_manual_booking(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            event_obj = Event.objects.first()
            if not event_obj:
                return JsonResponse({'success': False, 'error': 'No Event configured.'})
            
            raw_phone = str(data['phone'])
            clean_phone = raw_phone.replace(" ", "").replace("+", "").replace("-", "")
            if len(clean_phone) > 10:
                clean_phone = clean_phone[-10:]

            booking = Booking.objects.create(
                event=event_obj,
                customer_name=data['name'],
                email=data['email'],
                phone=clean_phone,
                razorpay_payment_id=data['utr'],
                quantity=int(data.get('qty', 1)),
                status="PENDING",
                amount=0
            )

            return JsonResponse({'success': True})
        except Exception as e:
            print(f"Booking Error: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

# --- 3. SUBMIT WAITLIST (New Function) ---
def submit_waitlist(request):
    if request.method == "POST":
        name = request.POST.get('waitlist_name')
        phone = request.POST.get('waitlist_phone')
        
        # Save to database if data exists
        if name and phone:
            Waitlist.objects.create(name=name, phone=phone)
        
        # Create a simple success page or redirect back
        # Ideally, make a 'booking/waitlist_success.html' template
        return render(request, 'booking/waitlist_success.html') 
        
    return redirect('index')