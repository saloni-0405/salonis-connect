from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from bookings.models import Booking


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'accounts/my_bookings.html', {'bookings': bookings})


@login_required
def worker_dashboard(request):
    bookings = Booking.objects.filter(worker__user=request.user)
    return render(request, 'accounts/worker_dashboard.html', {'bookings': bookings})


@login_required
def accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = "accepted"
    booking.save()
    return redirect('worker_dashboard')


@login_required
def add_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        review = request.POST.get("review")
        booking.review = review
        booking.save()
        return redirect('my_bookings')

    return render(request, "accounts/add_review.html", {"booking": booking})