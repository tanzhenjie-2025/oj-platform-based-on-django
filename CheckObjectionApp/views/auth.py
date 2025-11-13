# CheckObjectionApp/views/auth.py
from django.contrib.auth import get_user_model,login, logout, authenticate
from django.shortcuts import render, redirect,reverse
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from ..forms import LoginForm, RegisterForm
from ..models import UserProfile

from django.db import IntegrityError
User = get_user_model()

def redirect_root(request):
    """ 重定向到主页 """
    return redirect('CheckObjectionApp:CheckObjectionApp_login')

@require_http_methods(['GET', 'POST'])
def CheckObjection_login(request):
    if request.method == 'GET':
        form = LoginForm()
        content = {'form': form}
        return render(request, 'CheckObjection/CheckObjection_login.html', content)
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            user_input_captcha = form.cleaned_data.pop('captcha')
            user_captcha = str(request.session.get('captcha'))

            # 验证码校验
            if user_input_captcha.lower() != user_captcha.lower():
                form.add_error('captcha', '验证码错误，请重新输入')
                content = {'form': form}
                return render(request, 'CheckObjection/CheckObjection_login.html', content)

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember = form.cleaned_data.get('remember')
            user = authenticate(username=username, password=password)

            if user is not None:
                # 检查用户是否激活
                if not user.is_active:
                    form.add_error(None, '账户已被禁用，请联系管理员')
                    content = {'form': form}
                    return render(request, 'CheckObjection/CheckObjection_login.html', content)

                login(request, user)
                request.session['captcha'] = None
                if remember:
                    request.session.set_expiry(60 * 60 * 24 * 7)
                else:
                    request.session.set_expiry(0)
                return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))
            else:
                # 用户认证失败，检查是用户名问题还是密码问题
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user_exists = User.objects.filter(username=username).exists()
                    if not user_exists:
                        form.add_error('username', '用户名不存在')
                    else:
                        form.add_error('password', '密码错误')
                except Exception:
                    form.add_error(None, '用户名或密码错误')

                content = {'form': form}
                return render(request, 'CheckObjection/CheckObjection_login.html', content)
        else:
            # 表单验证失败，错误信息已经在form中
            content = {'form': form}
            return render(request, 'CheckObjection/CheckObjection_login.html', content)


@require_http_methods(['GET', 'POST'])
def CheckObjection_register(request):
    """注册功能实现"""
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})
    else:
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_input_captcha = form.cleaned_data.get('captcha')
            user_captcha = str(request.session.get('captcha', ''))

            # 验证验证码
            if not user_captcha:
                form.add_error('captcha', '验证码已过期，请刷新验证码')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            if user_input_captcha.lower() != user_captcha.lower():
                form.add_error('captcha', '验证码错误')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            # 双重检查用户名是否存在（防止并发注册等情况）
            if User.objects.filter(username=username).exists():
                form.add_error('username', '用户名已存在')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            try:
                # 创建用户
                user = User.objects.create_user(username=username, password=password)
                user_profile = UserProfile.objects.create(user=user)
                login(request, user)

                # 设置session过期时间
                if form.cleaned_data.get('remember'):
                    request.session.set_expiry(60 * 60 * 24 * 7)
                else:
                    request.session.set_expiry(0)

                # 注册成功后清除验证码session
                if 'captcha' in request.session:
                    del request.session['captcha']

                return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))

            except IntegrityError:
                # 处理数据库唯一性约束错误（用户名重复）
                form.add_error('username', '用户名已存在，请选择其他用户名')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            except Exception as e:
                # 处理创建用户时的意外错误
                form.add_error(None, f'注册失败：{str(e)}')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

        else:
            # 表单验证失败，返回错误信息
            return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def CheckObjection_logout(request):
    """退出功能实现"""
    logout(request)
    return redirect('CheckObjectionApp:CheckObjectionApp_index')

def CheckObjection_noPower(request):
    return render(request,'CheckObjection/CheckObjection_noPower.html')
