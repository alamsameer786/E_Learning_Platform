from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from core.models import UserProfile

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email', '')
        
        # Validation
        if not username:
            messages.error(request, 'Username is required!')
            return redirect('signup')
            
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters!')
            return redirect('signup')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('signup')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password1,
                email=email
            )
            
            # Create user profile (using get_or_create to avoid integrity error)
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Login user
            login(request, user)
            messages.success(request, f'Welcome {username}! Your account has been created.')
            return redirect('dashboard')
            
        except IntegrityError:
            messages.error(request, 'Profile already exists. Please try again.')
            return redirect('signup')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('signup')
    
    return render(request, 'accounts/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Username and password are required!')
            return redirect('login')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return redirect('login')
    
    return render(request, 'accounts/login.html')
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
def profile_view(request):
    return render(request, 'accounts/profile.html')