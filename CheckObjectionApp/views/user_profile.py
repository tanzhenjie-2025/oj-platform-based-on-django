# CheckObjectionApp/views/user_profile.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from ..models import UserProfile

User = get_user_model()


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:login'))  # 更新URL名称
def change_password(request):
    """修改密码"""
    if request.method == "POST":
        user_id = request.user.id
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        check_new_password = request.POST.get('check_new_password', '').strip()

        # 1. 获取单个用户实例
        user = User.objects.get(id=user_id)

        # 2. 验证旧密码和新密码
        if not old_password or not new_password or not check_new_password:
            messages.error(request, '所有字段都必须填写')
            return redirect(reverse("CheckObjectionApp:change_password"))

        if new_password != check_new_password:
            messages.error(request, '两次输入的新密码不一致')
            return redirect(reverse("CheckObjectionApp:change_password"))

        if not user.check_password(old_password):
            messages.error(request, '旧密码错误')
            return redirect(reverse("CheckObjectionApp:change_password"))

        # 3. 正确设置新密码
        user.set_password(new_password)
        user.save()

        messages.success(request, '密码修改成功，请重新登录')
        return redirect(reverse("CheckObjectionApp:login"))  # 修改后重新登录

    if request.method == "GET":
        user = request.user
        return render(request, 'CheckObjection/changeName.html', context={'user': user})


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:login'))  # 更新URL名称
def change_profile(request):
    """修改用户资料"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except ObjectDoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    if request.method == "POST":
        # 更新用户基本信息
        if 'username' in request.POST:
            user_id = request.user.id

            # 更新User模型中的字段
            User.objects.filter(id=user_id).update(
                username=request.POST.get('username', ''),
                email=request.POST.get('email', ''),
            )

            # 更新UserProfile中的字段
            user_profile.phone = request.POST.get('phone', '')
            user_profile.bio = request.POST.get('bio', '')
            user_profile.location = request.POST.get('location', '')
            user_profile.website = request.POST.get('website', '')

            # 处理生日字段
            birthday = request.POST.get('birthday', '')
            if birthday:
                user_profile.birthday = birthday

            # 处理头像上传
            if 'avatar' in request.FILES:
                user_profile.avatar = request.FILES['avatar']

            user_profile.save()

            messages.success(request, '个人信息更新成功！')
            return redirect(reverse("CheckObjectionApp:index"))  # 更新URL名称

    if request.method == "GET":
        user = request.user
        # 准备用户信息
        user_info = {
            'username': user.username or '暂无',
            'email': user.email or '暂无',
            'phone': user_profile.phone or '暂无',
            'birthday': user_profile.birthday.strftime('%Y-%m-%d') if user_profile.birthday else '',
            'bio': user_profile.bio or '暂无',
            'location': user_profile.location or '暂无',
            'website': user_profile.website or '暂无',
            'finish': user_profile.finish,
            'avatar_url': user_profile.get_avatar_url(),
            'theme': user_profile.theme,
            'language': user_profile.language,
        }
        return render(request, 'CheckObjection/changeName.html',
                      context={'user': user, 'user_info': user_info})


@require_http_methods(['POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:login'))  # 更新URL名称
def update_preferences(request):
    """更新用户偏好设置"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except ObjectDoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    if request.method == "POST":
        user_profile.theme = request.POST.get('theme', 'light')
        user_profile.language = request.POST.get('language', 'zh-hans')
        user_profile.save()

        messages.success(request, '偏好设置更新成功！')
        return redirect(reverse("CheckObjectionApp:change_profile"))  # 更新URL名称