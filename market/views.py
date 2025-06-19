from django.shortcuts import render, redirect, get_object_or_404
from .models import Item, ItemImage, Order, Message, User
from .forms import ItemForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import translation
from django.conf import settings
from django.db.models import Q, Max, F, Case, When
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def home(request):
    items = Item.objects.filter(is_sold=False).order_by('-created_at')
    return render(request, 'pages/home.html', {'items': items})

@login_required
def upload_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        files = request.FILES.getlist('images')
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            for file in files:
                if file.content_type.startswith('image/'):
                    ItemImage.objects.create(item=item, image=file)
            return redirect('home')
    else:
        form = ItemForm()
    return render(request, 'pages/upload.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'pages/register.html', {'form': form})

def set_language(request):
    lang = request.GET.get('lang', settings.LANGUAGE_CODE)

    if lang in dict(settings.LANGUAGES):
        translation.activate(lang)
        request.session['django_language'] = lang    
        response = redirect(request.META.get('HTTP_REFERER', '/'))
        
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,   
            lang,
            max_age=60 * 60 * 24 * 365,      
            path='/',
        )
        return response

    return redirect(request.META.get('HTTP_REFERER', '/'))

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    images = list(item.images.all())
    return render(request, 'pages/item_detail.html', {'item': item, 'images': images})

@login_required
def my(request):
    user = request.user
    user_items = Item.objects.filter(seller=user, is_sold=False)
    sold_orders = Order.objects.filter(item__seller=user)
    purchased_orders = Order.objects.filter(buyer=user)

    sold_items = [order.item for order in sold_orders]
    purchased_items = [order.item for order in purchased_orders]

    favorite_items = user.favorites.all()

    return render(request, 'pages/my.html', {
        'user_items': user_items,
        'sold_items': sold_items,
        'purchased_items': purchased_items,
        'favorite_items': favorite_items,
    })



from django.db.models import Max, Subquery, OuterRef

@login_required
def messages_center(request):
    user = request.user

    all_threads = (
        Message.objects
        .filter(Q(sender=user) | Q(receiver=user))
        .annotate(
            partner=Case(
                When(sender=user, then=F('receiver')),
                default=F('sender'),
                )
        )
    )

    latest_message_ids = (
        all_threads.values('partner')
        .annotate(latest_id=Max('id'))
        .values_list('latest_id', flat=True)
    )

    latest_conversations = Message.objects.filter(id__in=latest_message_ids).order_by('-timestamp')

    for msg in latest_conversations:
        msg.other_user = msg.receiver if msg.sender == user else msg.sender

    return render(request, 'pages/messages.html', {
        'latest_conversations': latest_conversations
    })


@login_required
def chat_thread(request, username):
    other_user = get_object_or_404(User, username=username)
    user = request.user

    thread = Message.objects.filter(
        Q(sender=user, receiver=other_user) |
        Q(sender=other_user, receiver=user)
    ).order_by('timestamp')


    thread.filter(receiver=user, is_read=False).update(is_read=True)

   
    if request.method == "POST":
        content = request.POST.get("content")
        item_id = request.POST.get("item_id")
        item = Item.objects.get(id=item_id) if item_id else None

        Message.objects.create(
            sender=user,
            receiver=other_user,
            content=content,
            item=item
        )
        return redirect('chat_thread', username=other_user.username)

 
    item_id = request.GET.get('item')
    related_item = Item.objects.get(id=item_id) if item_id else None

    return render(request, 'pages/chat_thread.html', {
        'other_user': other_user,
        'thread': thread,
        'related_item': related_item
    })

@login_required
@require_POST
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    form = ItemForm(request.POST, request.FILES, instance=item)

    if form.is_valid():
        form.save()

        delete_ids = request.POST.getlist("image_ids_to_delete[]")
        if delete_ids:
            ItemImage.objects.filter(id__in=delete_ids, item=item).delete()

        files = request.FILES.getlist("images")
        for file in files:
            if file.content_type.startswith("image/"):
                ItemImage.objects.create(item=item, image=file)

        return JsonResponse({"success": True})
    
    return JsonResponse({"error": "Invalid data"}, status=400)

@login_required
@require_POST
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    item.delete()
    return redirect('my')

@login_required
@require_POST
def purchase_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if item.is_sold:
        return JsonResponse({"error": "Item already sold."}, status=400)
    if item.seller == request.user:
        return JsonResponse({"error": "You cannot buy your own item."}, status=403)

    Order.objects.create(buyer=request.user, item=item)
    item.is_sold = True
    item.save()
    return redirect('my')


@login_required
@require_POST
def toggle_favorite(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.user in item.favorited_by.all():
        item.favorited_by.remove(request.user)
    else:
        item.favorited_by.add(request.user)
    return redirect('item_detail', item_id=item.id)  

@login_required
@require_POST
def send_purchase_request(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if item.is_sold or item.seller == request.user:
        return JsonResponse({"error": "Invalid request"}, status=400)
    
    Message.objects.create(
        sender=request.user,
        receiver=item.seller,
        content=f"我想购买你的商品《{item.title}》",
        item=item
    )
    return redirect('chat_thread', username=item.seller.username)

@login_required
@require_POST
def confirm_deal(request, item_id, buyer_username):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    buyer = get_object_or_404(User, username=buyer_username)

    if item.is_sold:
        return JsonResponse({"error": "Item already sold."}, status=400)

    message = Message.objects.filter(sender=buyer, receiver=request.user, item=item, decision='pending').last()
    if message:
        message.decision = 'accepted'
        message.save()
    
    Order.objects.create(buyer=buyer, item=item)
    item.is_sold = True
    item.save()

    Message.objects.create(
        sender=request.user,
        receiver=buyer,
        content=f"商品《{item.title}》交易已确认，请注意查收。",
        item=item
    )
    return redirect('chat_thread', username=buyer.username)

@login_required
@require_POST
def reject_deal(request, item_id, buyer_username):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    buyer = get_object_or_404(User, username=buyer_username)

    if item.is_sold:
        return JsonResponse({"error": "Item already sold."}, status=400)

    message = Message.objects.filter(sender=buyer, receiver=request.user, item=item, decision='pending').last()
    if message:
        message.decision = 'rejected'
        message.save()
    
    Message.objects.create(
        sender=request.user,
        receiver=buyer,
        content=f"很抱歉，您的购买请求《{item.title}》已被卖家拒绝。",
        item=item
    )
    return redirect('chat_thread', username=buyer.username)

@login_required
def get_item_images(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    images = item.images.all()
    data = {
        "images": [{"id": img.id, "url": img.image.url} for img in images]
    }
    return JsonResponse(data)