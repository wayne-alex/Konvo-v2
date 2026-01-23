# Create your views here.
import json
from collections import defaultdict
from datetime import timedelta
from itertools import groupby
from operator import itemgetter

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import localtime, now

from client.models import Profile, Chat, Message


# Create your views here.
def landing(request):
    return render(request, 'landingv2.html')


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard-v2')
        else:
            messages.error(request, "Username or password incorrect!")
            return render(request, 'loginv2.html')
    return render(request, 'loginv2.html')


def register(request):
    if request.method == 'POST':
        first_name = request.POST['first-name']
        last_name = request.POST['last-name']
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken!")
            return render(request, 'registerv2.html')
        # Create and save the user
        user = User.objects.create_user(username=username, password=password, first_name=first_name,
                                        last_name=last_name)

        _profile = Profile(user=user)
        _profile.save()

        login(request, user)  # Uncomment if you want to log in after successful registration

        messages.success(request, "Registration successful! Finish Setting up your Profile.")
        return redirect('profile-setting-v2')  # Redirect to login page after successful registration

    return render(request, 'registerv2.html')


def profileSetting(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        about = data.get('about')
        avatar = data.get('avatar')
        avatar_string = f'https://mdbcdn.b-cdn.net/img/Photos/new-templates/bootstrap-chat/ava{avatar}-bg.webp'

        user = request.user
        _profile = Profile.objects.get(user=user)
        _profile.about = about
        _profile.profile_picture = avatar_string
        _profile.save()
        return JsonResponse({'success': True})

    return render(request, 'profile-settingV2.html')


def dashboard(request):
    # Get all chats for the current user
    chats = Chat.objects.filter(users=request.user).order_by('-created_at')

    # For each chat, get the latest message and other users
    chat_data = []
    for chat in chats:
        # Get the latest message
        latest_message = Message.objects.filter(chat=chat).order_by('-created_at').first()

        # Get other users in the chat
        other_users = chat.users.exclude(id=request.user.id)

        # Get the chat name (either group name or other users' names)
        if chat.is_group:
            chat_name = chat.name
        else:
            chat_name = ', '.join([f"{user.first_name} {user.last_name}" for user in other_users])

        # Get unread message count
        unread_count = Message.objects.filter(
            chat=chat,
            read=False
        ).exclude(sender=request.user).count()

        # Get the profile picture (using the first other user's picture for 1-on-1 chats)
        if chat.is_group and chat.image:
            profile_pic = chat.image
        elif other_users:
            profile_pic = Profile.objects.get(user=other_users[0]).profile_picture
        else:
            profile_pic = None  # Default profile picture path

        chat_data.append({
            'id': chat.id,
            'name': chat_name,
            'latest_message': latest_message,
            'unread_count': unread_count,
            'profile_pic': profile_pic,
            'is_group': chat.is_group
        })

    return render(request, 'dashboardv2.html', {
        'chats': chat_data
    })


def chat(request, chatId):
    # Get chat and handle if it doesn't exist
    chat = Chat.objects.get(id=chatId)
    if chat.is_group:
        other_users = chat.users.exclude(id=request.user.id)
        messages = Message.objects.filter(chat=chat).annotate(
            date_sent=TruncDate('created_at')
        ).order_by('created_at')
        today = localtime(now()).date()
        yesterday = today - timedelta(days=1)

        grouped_messages_dict = defaultdict(list)

        for message in messages:
            if message.date_sent == today:
                label = 'Today'
            elif message.date_sent == yesterday:
                label = 'Yesterday'
            else:
                label = message.date_sent.strftime('%d %B %Y')
            grouped_messages_dict[label].append(message)

        # Convert to list of dictionaries
        grouped_messages = [
            {'label': label, 'messages': grouped_messages_dict[label]}
            for label in grouped_messages_dict
        ]

        pass
    else:
        # Get other users in chat
        other_users = chat.users.exclude(id=request.user.id)
        username = ', '.join([user.first_name + ' ' + user.last_name for user in other_users])

        # Get profile picture - adjusted for your Profile model
        profile_picture = Profile.objects.get(user=other_users[0]).profile_picture

        # Retrieve and group messages by date - adjusted for your Message model's related name
        messages = Message.objects.filter(chat=chat).annotate(
            date_sent=TruncDate('created_at')
        ).order_by('created_at')

        today = localtime(now()).date()
        yesterday = today - timedelta(days=1)

        grouped_messages_dict = defaultdict(list)

        for message in messages:
            if message.date_sent == today:
                label = 'Today'
            elif message.date_sent == yesterday:
                label = 'Yesterday'
            else:
                label = message.date_sent.strftime('%d %B %Y')
            grouped_messages_dict[label].append(message)

        # Convert to list of dictionaries
        grouped_messages = [
            {'label': label, 'messages': grouped_messages_dict[label]}
            for label in grouped_messages_dict
        ]

    return render(request, 'chatv2.html', {
        'username': username,
        'profile_pic': profile_picture,
        'grouped_messages': grouped_messages,
        'chat_id': chatId,
        'chat': chat,  # Added this to access chat properties in template
    })


def newChat(request):
    profiles = Profile.objects.all().exclude(user=request.user).order_by('user__first_name')
    # profiles = Profile.objects.all().order_by('user__first_name')
    profile_list = [
        {
            'profile': profile,
            'first_letter': profile.user.first_name[0].upper() if profile.user.first_name else '#'
        }
        for profile in profiles
    ]
    grouped_profiles = {}
    for letter, group in groupby(profile_list, key=itemgetter('first_letter')):
        grouped_profiles[letter] = [item['profile'] for item in group]

    return render(request, 'newUserv2.html', {'grouped_profiles': grouped_profiles})


def logout_user(request):
    logout(request)
    return render(request, 'loginv2.html')


def openChat(request, user_id):
    user_to_chat = get_object_or_404(User, id=user_id)
    current_user = request.user
    user_chat = Chat.objects.filter(users=current_user).filter(users=user_to_chat).filter(
        is_group=False).distinct().first()
    if not user_chat:
        user_chat = Chat.objects.create()
        user_chat.users.add(current_user, user_to_chat)

    return redirect('chat-v2', chatId=user_chat.id)


def newGroup(request):
    # Get the current user
    current_user = request.user

    # Get all profiles except the current user's profile
    profiles = Profile.objects.select_related('user').filter(
        ~Q(user=current_user),  # Exclude current user
        user__is_active=True  # Only include active users
    ).order_by(
        'user__first_name',  # Order by first name
        'user__last_name'
    )

    # Create a dictionary to store grouped profiles
    grouped_profiles = {}

    # Group profiles by first letter of first name
    for profile in profiles:
        first_letter = profile.user.first_name[0].upper() if profile.user.first_name else '#'
        if first_letter not in grouped_profiles:
            grouped_profiles[first_letter] = []
        grouped_profiles[first_letter].append(profile)

    # Sort the groups alphabetically
    grouped_profiles = dict(sorted(grouped_profiles.items()))

    context = {
        'grouped_profiles': grouped_profiles,
        'profiles': profiles,  # Also include ungrouped profiles for the checkbox list
    }

    return render(request, 'new-group-v2.html', context)


def newGroupProfile(request):
    return render(request, 'group_profilev2.html')


def createGroup(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            members_json = request.POST.get('members')
            group_image = request.FILES.get('image')

            # Validate required fields
            if not name:
                return JsonResponse({'success': False, 'error': 'Group name is required'})

            if not members_json:
                return JsonResponse({'success': False, 'error': 'No members selected'})

            # Parse members JSON
            try:
                members = json.loads(members_json)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid member data'})

            # Create the group
            group = Chat.objects.create(
                name=name,
                created_by=request.user,
                is_group=True
            )

            # Handle group image if provided
            if group_image:
                group.image = group_image

            member_objects = []
            for member_data in members:
                try:
                    user = User.objects.get(id=member_data['id'])
                    group.users.add(user)

                except User.DoesNotExist:
                    continue
            group.users.add(request.user)
            group.save()

            return JsonResponse({
                'success': True,
                'groupId': group.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    # GET request - render the group creation pa
    return JsonResponse({'success': False, 'message': 'Method not Allowed'}, status=400)
