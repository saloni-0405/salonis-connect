from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User

from django.db.models import Avg, Sum, Count, Q
from decimal import Decimal
from datetime import date
from django.utils import timezone

from .forms import CustomerRegisterForm, WorkerRegisterForm, WorkerProfileForm
from .models import Worker, Booking, Category, Payment, Review
from django.http import JsonResponse

# ---------------- HOME ----------------

def home(request):

    today = timezone.now().date()

    Booking.objects.filter(
        service_date__lt=today,
        status="Completed"
    ).update(status="Finished")

    total_customers = User.objects.filter(is_staff=False).count()
    total_workers = Worker.objects.filter(is_verified=True).count()
    completed_services = Booking.objects.filter(status="Finished").count()

    top_workers = Worker.objects.filter(is_verified=True).annotate(
        avg_rating=Avg('review__rating'),
        total_reviews=Count('review')
    ).order_by('-avg_rating')[:3]

    recent_reviews = Review.objects.select_related(
        'customer',
        'worker'
    ).order_by('-id')[:3]

    categories = Category.objects.all()

    context = {
        'total_customers': total_customers,
        'total_workers': total_workers,
        'completed_services': completed_services,
        'top_workers': top_workers,
        'recent_reviews': recent_reviews,
        'categories': categories
    }

    return render(request, 'home.html', context)


# ---------------- CUSTOMER REGISTER ----------------

def customer_register(request):
    form = CustomerRegisterForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('login')

    return render(request, 'customer_register.html', {'form': form})


# ---------------- WORKER REGISTER ----------------

def worker_register(request):

    if request.method == 'POST':

        form = WorkerRegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            Worker.objects.create(
                user=user,
                category=form.cleaned_data['category'],
                phone=form.cleaned_data['phone'],
                experience=form.cleaned_data['experience'],
                address=form.cleaned_data['address'],
                area=form.cleaned_data['area']
            )

            return redirect('login')

    else:
        form = WorkerRegisterForm()

    return render(request, 'worker_register.html', {'form': form})


# ---------------- LOGIN ----------------

def user_login(request):

    form = AuthenticationForm(request, data=request.POST or None)

    if form.is_valid():

        user = form.get_user()
        login(request, user)

        if user.is_superuser:
            return redirect('admin_dashboard')

        if Worker.objects.filter(user=user).exists():
            return redirect('worker_dashboard')

        return redirect('category_list')

    return render(request, 'login.html', {'form': form})


# ---------------- LOGOUT ----------------

def user_logout(request):
    logout(request)
    return redirect('home')


# ---------------- CATEGORY LIST ----------------

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'category_list.html', {'categories': categories})


# ---------------- WORKER LIST ----------------

def worker_list(request, category_id):

    category = get_object_or_404(Category, id=category_id)

    min_experience = request.GET.get('experience')
    min_rating = request.GET.get('rating')
    sort_by = request.GET.get('sort')
    area = request.GET.get('area')

    workers = Worker.objects.filter(
        category=category,
        is_verified=True,
        is_available=True
    ).annotate(
        avg_rating=Avg('review__rating'),
        completed_jobs=Count('booking', filter=Q(booking__status="Finished"))
    ).order_by(
        '-avg_rating',
        '-completed_jobs',
        '-experience'
    )[:10]

    if area:
        workers = workers.filter(area=area)

    worker_data = []

    for worker in workers:

        rating = worker.avg_rating if worker.avg_rating else 0

        today = timezone.now().date()

        today_bookings = Booking.objects.filter(
            worker=worker,
            service_date=today
        ).exclude(status="Cancelled").count()

        if today_bookings >= worker.max_jobs_per_day:
            availability = "Full"
        else:
            availability = "Available"

        worker_data.append({
            'worker': worker,
            'avg_rating': rating,
            'availability': availability
        })

    context = {
        'worker_data': worker_data,
        'category': category,
        'selected_area': area,
        'selected_experience': min_experience,
        'selected_rating': min_rating,
        'selected_sort': sort_by
    }

    return render(request, 'worker_list.html', context)

# ---------------- BOOK WORKER ----------------

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Worker, Booking


@login_required
def book_worker(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id)

    selected_date = request.GET.get("service_date") or request.POST.get("service_date")

    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    booked_slots = list(
        Booking.objects.filter(
            worker=worker,
            service_date=selected_date
        ).exclude(status="Cancelled").values_list("time_slot", flat=True)
    )

    if request.method == "POST":
        service_date = request.POST.get("service_date")
        time_slot = request.POST.get("time_slot")
        address = request.POST.get("address")

        if service_date:
            try:
                service_date = datetime.strptime(service_date, "%Y-%m-%d").date()
            except ValueError:
                service_date = timezone.now().date()
        else:
            service_date = timezone.now().date()

        if not address:
            address = worker.address

        if not time_slot:
            return render(request, "booking_form.html", {
                "worker": worker,
                "booked_slots": booked_slots,
                "selected_date": selected_date,
                "error": "Please select a time slot."
            })

        daily_bookings = Booking.objects.filter(
            worker=worker,
            service_date=service_date
        ).exclude(status="Cancelled").count()

        if daily_bookings >= worker.max_jobs_per_day:
            return render(request, "booking_form.html", {
                "worker": worker,
                "booked_slots": booked_slots,
                "selected_date": selected_date,
                "error": "Worker is fully booked for this day."
            })

        existing_booking = Booking.objects.filter(
            worker=worker,
            service_date=service_date,
            time_slot=time_slot
        ).exclude(status="Cancelled").exists()

        if existing_booking:
            return render(request, "booking_form.html", {
                "worker": worker,
                "booked_slots": booked_slots,
                "selected_date": selected_date,
                "error": "Worker already booked for this time slot."
            })

        total_price = worker.category.base_price

        booking = Booking.objects.create(
            customer=request.user,
            worker=worker,
            service_date=service_date,
            time_slot=time_slot,
            address=address,
            total_price=total_price,
            status="Pending"
        )

        return redirect("payment_page", booking_id=booking.id)

    return render(request, "booking_form.html", {
        "worker": worker,
        "booked_slots": booked_slots,
        "selected_date": selected_date,
    })
# ---------------- PAYMENT ----------------

from decimal import Decimal
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Booking, Payment

@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

    advance_amount = booking.total_price * Decimal("0.30")

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        allowed_methods = ["UPI", "Card", "Net Banking"]

        if payment_method not in allowed_methods:
            return render(request, "payment_page.html", {
                "booking": booking,
                "advance_amount": advance_amount,
                "error": "Please select a valid online payment method."
            })

        Payment.objects.create(
            booking=booking,
            amount=advance_amount,
            payment_method=payment_method,
            payment_status="Paid"
        )

        booking.status = "Confirmed"
        booking.save()

        messages.success(request, "Advance payment completed successfully.")
        return redirect("customer_dashboard")

    return render(request, "payment_page.html", {
        "booking": booking,
        "advance_amount": advance_amount
    })

# ---------------- MY BOOKINGS ----------------

@login_required
def my_bookings(request):

    bookings = Booking.objects.filter(customer=request.user)

    for booking in bookings:

        if booking.service_date < date.today() and booking.status != "Finished":
            booking.status = "Finished"
            booking.save()

    return render(request, "my_bookings.html", {
        "bookings": bookings
    })


# ---------------- ADD REVIEW ----------------

@login_required
def add_review(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.customer != request.user:
        return redirect('my_bookings')

    if booking.status != "Finished":
        return redirect('my_bookings')

    if request.method == "POST":

        Review.objects.create(
            booking=booking,
            worker=booking.worker,
            customer=request.user,
            rating=request.POST.get("rating"),
            comment=request.POST.get("comment")
        )

        return redirect('my_bookings')

    return render(request, "add_review.html", {"booking": booking})


# ---------------- WORKER DASHBOARD ----------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Avg, Count
from .models import Worker, Booking, Review

# ---------------- WORKER DASHBOARD ----------------

@login_required
def worker_dashboard(request):
    try:
        worker = Worker.objects.get(user=request.user)
    except Worker.DoesNotExist:
        messages.error(request, "You are not registered as a worker yet.")
        return redirect('worker_register')

    bookings = Booking.objects.filter(worker=worker).order_by('-id')

    completed_bookings = bookings.filter(status="Completed")

    total_earned = sum(
        booking.worker.category.base_price
        for booking in completed_bookings
        if booking.worker and booking.worker.category
    )

    worker_payout = total_earned * 0.8
    platform_commission = total_earned * 0.2
    completed_jobs = completed_bookings.count()

    context = {
        "worker": worker,
        "bookings": bookings,
        "total_earned": total_earned,
        "worker_payout": worker_payout,
        "platform_commission": platform_commission,
        "completed_jobs": completed_jobs,
    }

    return render(request, "worker_dashboard.html", context)

# ---------------- WORKER PROFILE ----------------

def worker_profile(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id)

    reviews = Review.objects.filter(worker=worker).select_related('customer')

    rating_data = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )

    context = {
        "worker": worker,
        "reviews": reviews,
        "avg_rating": rating_data["avg_rating"],
        "total_reviews": rating_data["total_reviews"]
    }

    return render(request, "worker_profile.html", context)

# ---------------- EDIT PROFILE ----------------

@login_required
def edit_worker_profile(request):

    worker = get_object_or_404(Worker, user=request.user)

    if request.method == "POST":

        form = WorkerProfileForm(request.POST, request.FILES, instance=worker)

        if form.is_valid():
            form.save()
            return redirect('worker_profile', worker_id=worker.id)

    else:
        form = WorkerProfileForm(instance=worker)

    return render(request, 'edit_worker_profile.html', {'form': form})


# ---------------- START WORK ----------------

@login_required
def start_work(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.worker.user != request.user:
        return redirect('worker_dashboard')

    booking.status = "In Progress"
    booking.save()

    return redirect('worker_dashboard')


# ---------------- COMPLETE WORK ----------------

@login_required
def complete_work(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.worker.user != request.user:
        return redirect('worker_dashboard')

    booking.status = "Completed"
    booking.save()

    return redirect('worker_dashboard')


# ---------------- CONFIRM COMPLETION ----------------

@login_required
def confirm_completion(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.customer == request.user and booking.status == "Completed":
        booking.status = "Finished"
        booking.save()

    return redirect('my_bookings')


# ---------------- CANCEL BOOKING ----------------

@login_required
def cancel_booking(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

    payment = Payment.objects.filter(booking=booking).first()

    if payment and payment.is_paid:

        refund = payment.amount * Decimal('0.5')

        payment.is_refunded = True
        payment.refund_amount = refund
        payment.save()

    booking.status = "Cancelled"
    booking.save()

    return redirect('my_bookings')


# ---------------- ADMIN DASHBOARD ----------------

@staff_member_required
def admin_dashboard(request):

    bookings = Booking.objects.all().order_by('-id')

    total_bookings = Booking.objects.count()
    confirmed = Booking.objects.filter(status="Confirmed").count()
    finished = Booking.objects.filter(status="Finished").count()
    cancelled = Booking.objects.filter(status="Cancelled").count()

    payments = Payment.objects.filter(is_paid=True)

    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_refunded = payments.aggregate(Sum('refund_amount'))['refund_amount__sum'] or Decimal('0.00')

    net_revenue = total_paid - total_refunded

    platform_commission = net_revenue * Decimal("0.20")
    worker_payout = net_revenue * Decimal("0.80")

    context = {
        'bookings': bookings,
        'total_bookings': total_bookings,
        'confirmed': confirmed,
        'finished': finished,
        'cancelled': cancelled,
        'total_paid': total_paid,
        'total_refunded': total_refunded,
        'net_revenue': net_revenue,
        'platform_commission': platform_commission,
        'worker_payout': worker_payout,
    }

    return render(request, 'admin_dashboard.html', context)


# ---------------- SEARCH SERVICES ----------------

def search_services(request):

    query = request.GET.get('q')

    categories = Category.objects.filter(
        name__icontains=query
    )

    return render(request, 'search_results.html', {
        'query': query,
        'categories': categories
    })

# ---------------- PAY REMAINING ----------------
@login_required
def pay_remaining(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)
    remaining = booking.total_price * Decimal("0.70")

    if request.method == "POST":
        Payment.objects.create(
            booking=booking,
            amount=remaining,
            payment_method="UPI",
            is_paid=True
        )

        booking.status = "Finished"
        booking.save()

        return redirect("my_bookings")

    return render(request, "remaining_payment.html", {
        "booking": booking,
        "remaining": remaining
    })


# ---------------- TOGGLE AVAILABILITY ----------------
@login_required
def toggle_availability(request):

    worker = get_object_or_404(Worker, user=request.user)

    worker.is_available = not worker.is_available
    worker.save()

    return redirect("worker_dashboard")


# ---------------- MANAGE WORKERS ----------------
@staff_member_required
def manage_workers(request):

    workers = Worker.objects.all()

    return render(request, "manage_workers.html", {
        "workers": workers
    })


# ---------------- TOGGLE WORKER VERIFICATION ----------------
@staff_member_required
def toggle_worker_verification(request, worker_id):

    worker = get_object_or_404(Worker, id=worker_id)

    worker.is_verified = not worker.is_verified
    worker.save()

    return redirect("manage_workers")

@login_required
def accept_booking(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    # only worker assigned to booking can accept
    if booking.worker.user != request.user:
        return redirect('worker_dashboard')

    booking.status = "Confirmed"
    booking.save()

    return redirect('worker_dashboard')

@login_required
def customer_dashboard(request):

    bookings = Booking.objects.filter(customer=request.user).order_by('-id')

    upcoming = bookings.filter(status__in=["Pending", "Confirmed", "In Progress"])

    completed = bookings.filter(status="Finished")

    context = {
        "bookings": bookings,
        "upcoming": upcoming,
        "completed": completed
    }

    return render(request, "customer_dashboard.html", context)

from django.shortcuts import redirect

def whatsapp_contact(request):

    phone = "919876543210"  # replace with your number

    message = "Hello, I want to book a home service."

    whatsapp_url = f"https://wa.me/{phone}?text={message}"

    return redirect(whatsapp_url)

from django.http import JsonResponse
from django.db.models import Avg
from .models import Worker

from django.http import JsonResponse
from django.db.models import Avg
from .models import Worker


def api_workers(request):

    # Get only verified workers
    workers = Worker.objects.filter(is_verified=True).annotate(
        avg_rating=Avg('review__rating')
    ).order_by('-avg_rating')[:3]   # ONLY TOP 3 WORKERS


    data = []

    for worker in workers:

        # Worker image
        if worker.profile_image:
            image_url = worker.profile_image.url
        else:
            image_url = ""


        data.append({
            "id": worker.id,
            "name": worker.user.username,
            "category": worker.category.name,
            "image": image_url,
            "rating": round(worker.avg_rating or 0, 1)
        })


    return JsonResponse(data, safe=False)

    from .models import Review

def api_reviews(request):

    reviews = Review.objects.select_related(
        "customer",
        "worker",
        "worker__category"
    ).order_by("-id")[:5]

    data = []

    for review in reviews:

        data.append({
            "customer": review.customer.username,
            "comment": review.comment,
            "rating": review.rating,
            "service": review.worker.category.name
        })

    return JsonResponse(data, safe=False)

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Worker, Review


def api_worker_detail(request, worker_id):

    worker = get_object_or_404(
        Worker.objects.select_related('user', 'category'),
        id=worker_id
    )

    reviews = Review.objects.filter(worker=worker)

    review_data = []

    for r in reviews:
        review_data.append({
            "customer": r.customer.username,
            "rating": r.rating,
            "comment": r.comment
        })

    data = {
        "id": worker.id,
        "name": worker.user.username,
        "category": worker.category.name,
        "experience": worker.experience,
        "area": worker.area,
        "image": worker.profile_image.url if worker.profile_image else "",
        "reviews": review_data
    }

    return JsonResponse(data)

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def api_create_booking(request):

    if request.method == "POST":

        data = json.loads(request.body)

        worker_id = data.get("worker_id")
        service_date = data.get("service_date")
        time_slot = data.get("time_slot")
        address = data.get("address")

        worker = Worker.objects.get(id=worker_id)

        booking = Booking.objects.create(
            customer=request.user,
            worker=worker,
            service_date=service_date,
            time_slot=time_slot,
            address=address,
            total_price=worker.category.base_price
        )

        return JsonResponse({
            "message": "Booking created",
            "booking_id": booking.id
        })
    
from django.http import JsonResponse
from django.db.models import Avg
from .models import Worker


def api_workers_all(request):

    workers = Worker.objects.filter(is_verified=True).annotate(
        avg_rating=Avg('review__rating')
    )

    data = []

    for worker in workers:

        if worker.profile_image:
            image = worker.profile_image.url
        else:
            image = ""

        data.append({
            "id": worker.id,
            "name": worker.user.username,
            "category": worker.category.name,
            "image": image,
            "rating": round(worker.avg_rating or 0, 1)
        })

    return JsonResponse(data, safe=False)

from django.contrib import messages
from django.shortcuts import render, redirect
from .models import CustomerLead

def join_as_customer(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        area = request.POST.get("area")
        service_needed = request.POST.get("service_needed")
        message_text = request.POST.get("message")

        CustomerLead.objects.create(
            name=name,
            phone=phone,
            area=area,
            service_needed=service_needed,
            message=message_text
        )

        messages.success(request, "Your request has been submitted successfully. We will contact you soon.")
        return redirect("home")

    return redirect("home")

    from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Worker

@login_required
def edit_worker_profile(request):
    try:
        worker = Worker.objects.get(user=request.user)
    except Worker.DoesNotExist:
        messages.error(request, "You are not registered as a worker.")
        return redirect('worker_register')

    if request.method == "POST":
        worker.phone = request.POST.get('phone')
        worker.experience = request.POST.get('experience')
        worker.address = request.POST.get('address')
        worker.bio = request.POST.get('bio')

        if 'profile_image' in request.FILES:
            worker.profile_image = request.FILES['profile_image']

        worker.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('worker_dashboard')

    return render(request, 'edit_worker_profile.html', {'worker': worker})