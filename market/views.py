from django.shortcuts import render, redirect, get_object_or_404
from .models import Item, ItemImage, Order, Message, User
from .forms import ItemForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import translation
from django.conf import settings
from django.db.models import Q, Max, F
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def home(request):
    items = Item.objects.all().order_by('-created_at')
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
    return render(request, 'pages/item_detail.html', {'item': item})

@login_required
def my(request):
    user = request.user
    user_items = Item.objects.filter(seller=user, is_sold=False)
    sold_orders = Order.objects.filter(item__seller=user)
    purchased_orders = Order.objects.filter(buyer=user)
    favorite_items = user.favorites.all()
    return render(request, 'pages/my.html', {
        'user_items': user_items,
        'sold_orders': sold_orders,
        'purchased_orders': purchased_orders,
        'favorite_items': favorite_items,
    })


@login_required
def messages_center(request):
    user = request.user

    latest_by_pair = (
        Message.objects
        .filter(Q(sender=user) | Q(receiver=user))
        .values('sender', 'receiver')
        .annotate(latest_time=Max('timestamp'))
        .values('latest_time')
    )

    latest_conversations = (
        Message.objects
        .filter(Q(sender=user) | Q(receiver=user))
        .filter(timestamp__in=latest_by_pair)
        .order_by('-timestamp')
    )

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
def toggle_favorite(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.user in item.favorited_by.all():
        item.favorited_by.remove(request.user)
    else:
        item.favorited_by.add(request.user)
    return JsonResponse({'success': True})



