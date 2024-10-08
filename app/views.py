from settings.models import *
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from app.checksm import RechPayChecksum
from app.models import *
from app.forms import *
from django.contrib.auth.decorators import login_required,permission_required,user_passes_test
import requests
from stock.settings import EMAIL_HOST_USER
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
import threading
from django.template.loader import render_to_string
import random
import string
from threading import Thread
import payu_websdk
from django.utils import timezone
from settings.timing import market_open
from django.core.management import call_command
from django.http import HttpResponseRedirect
from wallet.calculation import *
from app.orders.market import market_order
from app.orders.limit import initiate_limit_order
import hashlib
from django.conf import settings
from django.http import HttpResponse
from home.models import *

User = get_user_model()

def generate_payu_hash(data):
    hash_sequence = "|".join([str(data.get(key, '')) for key in [
        'key', 'txnid', 'amount', 'productinfo', 'firstname', 'email', 'udf1', 'udf2', 'udf3', 'udf4', 'udf5', 'udf6', 'udf7', 'udf8', 'udf9', 'udf10']])
    hash_string = f"{hash_sequence}|{settings.PAYU_INFO['merchant_salt']}"
    return hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

# -=--------=---=----------=--=------PAGES--=---=------=---
# CONTACT US
def contact(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request,'We will contact to you as soon as possible')
    return render(request,"home/contact.html")

# ABOUT
def about(request):
    return render(request,"home/about.html")

def disclaimer(request):
    return render(request,"home/disclaimer.html")

# POLICY
def privacypolicy(request):
    return render(request,"home/privacypolicy.html")

def refundpolicy(request):
    return render(request,"home/refundpolicy.html")
# END PAGES

# USER CREATION LOGIN AND SIGNUP
def generate_verification_code(length=60):
    characters = string.ascii_letters + string.digits
    attempts = 0
    while True:
        verification_code = ''.join(random.choice(characters) for _ in range(length))
        if not CustomUser.objects.filter(verification_code=verification_code).exists():
            return verification_code
        attempts += 1

def verify_user(request,code):
    try:
       client = User.objects.filter(verification_code = code).first()
       client.is_active = True
       client.save()
       messages.success(request,'Congratulations ! Your email has been successfully verified Please login to continue.')       
       return redirect('/login/')
    except:
        return redirect('/')

def index(request):
    return render(request,'home/home.html')

def handlelogin(request):
    if request.user.is_authenticated:
        return redirect('/home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request,'Logged In Successfully')
                return redirect('/home?greeting=True')
            else:
                messages.error(request, 'Invalid login credentials.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def reset_password_done(request):
    content = "An Reset Password link has been sent to your email. Please reset to continue."
    return render(request,'message.html',{'content':content})

def password_reset_complete(request):
    messages.success(request,'Congratulations ! Your password updated successfully.')
    return redirect('/login')

def handlesignup(request):
    if request.user.is_authenticated:
        return redirect('/home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            verification_code = generate_verification_code()
            user.verification_code = verification_code
            user.save()
            subject = "E-mail verification for onstock Sign Up"
            html_content = render_to_string('email_template.html', {'verification_code': verification_code})
            content = strip_tags(html_content)
            email = EmailMultiAlternatives(
                subject,
                content ,
                EMAIL_HOST_USER ,
                [user.email]
            )
            email.attach_alternative(html_content,'text/html')
            email.send()
            content = "An verification link has been sent to your email. Please verify to continue."
            messages.success(request,"An verification link has been sent to your email. Please verify to continue.")
            return render(request,'message.html',{'content':content})
    else:
        form = RegistrationForm()
    return render(request, 'signup.html', {'form': form})

def handlelogout(request):
    logout(request)
    messages.success(request,"Logged out Successfully")
    return redirect('/login/')



def search_instruments(request):
    query = request.GET.get('q', '')
    suggestions = Instrument.objects.none()
    if query:
        qarr = query.split(' ')
        if qarr.__len__() == 2:
            if qarr[1].isdigit():
                suggestions = Instrument.objects.filter(
                    strike__startswith=qarr[1]
                    ).filter(tradingsymbol__startswith=qarr[0])
            else:
                suggestions = Instrument.objects.filter(
                    models.Q(tradingsymbol__icontains=query) |
                    models.Q(name__startswith=query)
                ).reverse()
        else:
            suggestions = Instrument.objects.filter(
                models.Q(tradingsymbol__icontains=qarr[0]) |
                models.Q(name__startswith=qarr[0])
            ).reverse()
        


            # suggestions = Instrument.objects.filter(
            #     models.Q(tradingsymbol__icontains=query) |
            #     models.Q(name__startswith=query) |
            #     models.Q(expiry__startswith=query) |
            #     models.Q(strike__startswith=query) |
            #     models.Q(exchange__startswith=query)
            # ).reverse()
    else:
        suggestions = Instrument.objects.none()
    results = [
        {'tradingsymbol': s.tradingsymbol, 'exchange': s.exchange}
        for s in suggestions if s.tradingsymbol
    ][:20] 
    
    return JsonResponse(results, safe=False)

@login_required
def add_watchlist(request):
    if request.method == 'POST':
        try:
            tag = request.POST.get("tag_input")
            data = request.POST.get("data")
            data = eval(data)
            for x in data:
                try:
                    tagob = tags.objects.filter(tag=tag).first()
                    Watchlist.objects.create(user=request.user,symbol=x['symbol'],segment=x['exchange'],tag=tagob)
                    messages.success(request,f"{tag} watchlist Updated ! ")
                except Exception as e:
                    messages.error(request,f"Error {e}, Stock cannot be added.")
        except Exception as e:
            messages.error(request,f"Some Error Occured {e}")
    return redirect('/watchlist')

@login_required
def delete_stock(request):
    if request.method == 'POST':
        try:
            data = request.POST.get("data")
            data = eval(data)
            for x in data:
                try:
                    delob = Watchlist.objects.filter(instrument_key=x).filter(user=request.user)
                    delob.delete()
                except:
                    pass
            messages.success(request,"Watchlist Updated Successfully")
        except Exception as e:
            messages.error(request,f"Some Error Occured")
    return redirect('/watchlist')


@login_required
def create_watchlist(request):
    if request.method == 'POST':
        try:
            name = request.POST.get("name")
            print(name)
            tags.objects.create(user=request.user,tag=name)
            messages.success(request,"Watchlist Updated Successfully")
        except Exception as e:
            messages.error(request,f"Error Occured, {e}")
    return redirect('/watchlist')


# ---------------DASHBOARD
@login_required
def home(request):
    greeting = False
    if 'greeting' in request.GET:
        greeting = True
    tag = tags.objects.filter(tag='@INDEX').first()
    Index = Watchlist.objects.filter(tag=tag)
    tag = tags.objects.filter(tag='@RECOMMENDED').first()
    recommended = Watchlist.objects.filter(tag=tag)
    tag = tags.objects.filter(tag='@EXPLORE').first()
    explore = Watchlist.objects.filter(tag=tag)
    news = News.objects.all().reverse()[:2]
    explore_videos = ExploreVideos.objects.all().reverse()
    watch_list = Watchlist.objects.filter(user=request.user)
    watchlist_list = []
    watchlist_symbollist = []
    all_tags = tags.objects.filter(user=request.user)
    for i in watch_list:
        watchlist_symbollist.append(i.instrument_key)
        if i.tag not in watchlist_list:
            watchlist_list.append(i.tag)
    for i in Index:
        watchlist_symbollist.append(i.instrument_key)
    for i in recommended:
        watchlist_symbollist.append(i.instrument_key)
    for i in explore:
        watchlist_symbollist.append(i.instrument_key)
    print(news)
    context = {
        'greeting':greeting,
        'news':news,
        'explore_videos':explore_videos,
        'explore':explore,
        'recommended':recommended,
        'Index':Index,
        'watch_list':watch_list,
        'all_tags':all_tags,
        'watchlist_list':watchlist_list,
        'watchlist_symbollist':watchlist_symbollist,
    }
    return render(request,'dashboard/home.html',context)


@login_required
def watchlist(request):
    watch_list = Watchlist.objects.filter(user=request.user).filter(on_homepage=False)
    tag = tags.objects.filter(tag='@INDEX').first()
    Index = Watchlist.objects.filter(tag=tag)
    watchlist_list = []
    watchlist_symbollist = []
    all_tags = tags.objects.filter(user=request.user).filter(on_homepage=False).reverse()
    for i in watch_list:
        watchlist_symbollist.append(i.instrument_key)
        if i.tag not in watchlist_list:
            watchlist_list.append(i.tag)
    for i in Index:
        watchlist_symbollist.append(i.instrument_key)
    context = {
        'watch_list':watch_list,
        'all_tags':all_tags,
        'Index':Index,
        'watchlist_list':watchlist_list,
        'watchlist_symbollist':watchlist_symbollist,
    }
    return render(request,'dashboard/watchlist.html',context)

@login_required
def delete_symbol(request,symbol):
    try:
        de = Watchlist.objects.filter(user=request.user,instrument_key=symbol).first()
        de.delete()
    except:
        pass
    return JsonResponse({'success': True, 'message': 'Deleted successfully.'})

@login_required
def orders(request):
    today = timezone.now().date()
    completed = Order.objects.filter(user=request.user, datetime__date=today,status = 'completed').order_by('-datetime')    
    pending = Order.objects.filter(user=request.user, datetime__date=today,status = 'pending').order_by('-datetime')
    initiated = Order.objects.filter(user=request.user, datetime__date=today,status__in=['pending', 'initiated']).order_by('-datetime')
    failed = Order.objects.filter(user=request.user, datetime__date=today,status__in=['failed']).order_by('-datetime')
    tradebook = Order.objects.filter(user=request.user)
    wallet = ((request.user.margin/100)*request.user.wallet)
    settings = charges.objects.first()
    tax = settings.tax
    charge = request.user.intraday_buy_charge
    all_tags = tags.objects.filter(user=request.user)

    # ---------------CONTEXT-----------
    context = {
        "tradebook":tradebook,
        "completed":completed,
        "pending":pending,
        "initiated":initiated,
        "failed":failed,
        "wallet":wallet,
        "all_tags":all_tags,
        "tax":tax,
        "charges":charge,
    }
    return render(request,'dashboard/orders.html',context)

@login_required
def portfolio(request):
    portfolio_symbollist = []
    today = timezone.now().date()
    holdings = Position.objects.filter(user=request.user,is_holding=True,is_closed=False).exclude(created_at__date=today)
    for x in holdings:
        portfolio_symbollist.append(x.instrument_key)
    today = timezone.now().date()
    # Filter positions for today
    positions = Position.objects.filter(user=request.user, last_traded_datetime__date=today)
    open_positions_available = positions.filter(quantity__gt=0).exists() or positions.filter(quantity__lt=0).exists()
    close_positions_available = positions.filter(quantity=0).exists()
    for x in positions:
        portfolio_symbollist.append(x.instrument_key)
    ppnl = 0
    for i in positions:
        ppnl = ppnl + i.realised_pnl
    hpnl = 0.0
    for x in holdings:
        hpnl = hpnl + x.realised_pnl
    wallet = request.user.wallet
    margin = request.user.margin
    settings = charges.objects.first()
    charge = request.user.intraday_buy_charge
    tax = settings.tax
    # ---------------CONTEXT-----------
    all_tags = tags.objects.filter(user=request.user)
    context = {
        "all_tags":all_tags,
        "positions":positions,
        "holdings":holdings,
        "ppnl":round(ppnl,2),
        "hpnl":round(hpnl,2),
        "portfolio_symbollist":portfolio_symbollist,
        'wallet':wallet,
        'margin':margin,
        'charges':charge,
        'tax':tax,
        'open_positions_available':open_positions_available,
        'close_positions_available':close_positions_available,
    }
    return render(request,'dashboard/portfolio.html',context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = BankInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'KYC completed !')
        else:
            messages.error(request, 'Invalid Details')
    return render(request,'dashboard/profile.html')

@login_required
def kyc(request):
    if request.method == 'POST':
        form = BankInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'KYC completed !')
        else:
            messages.error(request, 'Invalid Details')
    return redirect('/watchlist')

# WATCHLIST
@login_required
def add_to_watchlist(request):
    if request.method == 'POST':
        form = WatchlistForm(request.POST)
        if form.is_valid():
            watchlist = form.save(commit=False)
            watchlist.user = request.user
            watchlist.save()
            return JsonResponse({'success': True, 'message': 'Added to watchlist successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'Form data is invalid.'})
    else:
        form = WatchlistForm()
    return render(request, 'market.html', {'form': form})

@login_required
def cancel_order(request, order_id):
    try:
        cancelob = Order.objects.filter(user=request.user).get(order_id=order_id)
        cancelob.status = 'cancelled'
        cancelob.save()
        return JsonResponse({'success': True, 'message': 'Order Cancelled successfully'})
    except:
        return JsonResponse({'success': False, 'message': 'Order Cancellation Failed'})

@login_required
def cancelorder(request, order_id):
    try:
        cancelob = Order.objects.filter(user=request.user).get(order_id=order_id)
        cancelob.status = 'cancelled'
        cancelob.save()
        messages.error(request,'Order Cancelled Successfully')
        return redirect('/orders')
    except:
        messages.error(request,'Order Cancellation Failed')
        return redirect('/orders')

@login_required
def place_order(request):
    if request.method == 'POST':
        instrument_key = request.POST.get("instrument")
        price = float(request.POST.get("price"))
        quantity = int(request.POST.get("quantity"))
        order_type = request.POST.get("order_type")
        product = request.POST.get("product_type")
        type = request.POST.get("type")
        stoploss = request.POST.get("stoploss")
        target = request.POST.get("target")
        og = Instrument.objects.filter(instrument_key=instrument_key).first()
        segment = og.exchange
        symbol = og.tradingsymbol
        token = og.exchange_token
        if not market_open(segment):
            messages.error(request,'Market is closed.')
            return redirect('/orders')
            # return JsonResponse({'success': False, 'message': 'Market Closed !'})
        quantity = quantity * og.lot_size
        status = "failed"
        if type == 'Market':
            status = market_order(request.user,symbol,instrument_key,token,quantity,order_type,product,stoploss,target,'Market')
        else:
            status = initiate_limit_order(request.user,symbol,instrument_key,token,price, quantity,order_type,product,stoploss,target)
        if status == "failed":
            messages.error(request,'Order Rejected.')
            return redirect('/orders')
            # return JsonResponse({'success': False, 'message': 'Order executed but failed !'})
        else:
            messages.success(request,'Order placed successfully.')
            return redirect('/orders')
            # return JsonResponse({'success': True, 'message': 'Order Placed successfully'})
    else:
        return redirect('/orders')
    

@login_required
def trade_charges(request):
    odr = Order.objects.filter(user=request.user,status='completed')
    tcharge = 0
    for i in odr:
        tcharge = tcharge + i.charges
    context = {
        'odr':odr,
        'tcharge':round(tcharge,2)
    }
    return render(request,'dashboard/trade_charges.html',context)


@login_required
def pnl(request):
    odr = Position.objects.filter(user=request.user)
    tpnl = 0
    for i in odr:
        tpnl = tpnl + i.realised_pnl
    odr = Position.objects.filter(user=request.user,quantity=0)
    context = {
        'odr':odr,
        'tpnl':round(tpnl,2)
    }
    return render(request,'pnl.html',context)

@login_required
def transactions(request):
    Transaction.objects.filter(
    user=request.user,
    status='PENDING',
    transaction_type='DEPOSIT'
    ).update(status='FAILED')
    trans = Transaction.objects.filter(user=request.user)
    context = {
        'trans':trans
    }
    return render(request,'dashboard/transactions.html',context)

@login_required
def withdraw(request):
    if request.method == 'POST':
        amount = request.POST.get("amount")
        ob = Transaction.objects.filter(user=request.user,status='REQUESTED')
        check_amount = int(amount)
        for x in ob:
            check_amount = check_amount + x.amount
        if int(check_amount) <= request.user.wallet:
            Transaction.objects.create(user=request.user,amount=int(amount))
            messages.success(request,'Request added, your amount will be transferred to your account within 24 hours.')
        else:
            messages.error(request,'Invalid amount ! Please enter correct amount and try again.')
    return redirect('/transactions')



def orderid(length=15):
    characters = string.ascii_letters + string.digits
    attempts = 0
    while True:
        orderid = ''.join(random.choice(characters) for _ in range(length))
        if not Transaction.objects.filter(transaction_id=orderid).exists():
            return orderid
        attempts += 1

@login_required
def addFunds(request):
    if request.method == 'POST':
        mode = request.POST.get('mode')
        gateway = PaymentGateway.objects.all().first()
        if mode == 'upi':
            amount = request.POST.get('amount')
            url = "https://apiqr.upibuz.in/order/paytm"
            order_id = orderid()
            data = {
                "upiuid": gateway.upi_id,
                "token": gateway.upi_token,
                "orderId": order_id,
                "txnAmount": str(amount),
                "txnNote": "Onstock",
                "callback_url": f"https://onstock.in/payment-status/{order_id}",
                "cust_Mobile":"0000000000",
                "cust_Email":"onstock@gmail.com",
            }
            original_key = gateway.key
            original_key_bytes = original_key.encode('utf-8')
            key = (original_key_bytes + b'\0' * (16 - len(original_key_bytes)))[:16].decode()
            checksum = RechPayChecksum.generateSignature(data,key)
            data["checksum"] = checksum
            remark = Remarks.objects.filter(remark = 'UPI PAYMENT GATEWAY').first()
            Transaction.objects.create(user=request.user,amount=amount,transaction_id=order_id,checksum=checksum,status='PENDING',transaction_type='DEPOSIT',remark=remark)
            return render(request,"pay.html",{"data":data})
        elif mode == 'payu':
            import hashlib
            import random
            import uuid
            # PayU client setup
            userid = request.user.username
            amount = request.POST.get('amount')
            MERCHANT_KEY = gateway.payu_marchent_key
            SALT = gateway.payu_marchent_salt
            txnid = orderid()
            productInfo = "Onstock Deposit"
            firstname = request.user.first_name
            email = request.user.email
            phone = request.user.phone_number
            # Create the hash_string exactly as in PHP
            hash_string = f"{MERCHANT_KEY}|{txnid}|{amount}|{productInfo}|{firstname}|{email}|{userid}||||||||||{SALT}"

            # Generate the hash using SHA-512 and convert to lowercase
            hash_value = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

            # Print the redirection message
            print('<h1 style="color:red;text-align:center;">Please Wait We are redirecting you on Payment Page</h1>')

            # Generate the HTML form for redirection
            html_form = f"""
            <body>
            <form action="https://secure.payu.in/_payment" method="post" name="payuForm">
                  <input type="hidden" name="key" value="{MERCHANT_KEY}" />
                 <input type="hidden" name="hash" value="{hash_value}"/>
                 <input type="hidden" name="txnid" value="{txnid}" />
                <input type="hidden" name="amount" value="{amount}">
                <input type="hidden" name="productinfo" value="{productInfo}">
                <input type="hidden" name="firstname" value="{firstname}">
                <input type="hidden" name="email" value="{email}">
                <input type="hidden" name="phone" value="{phone}">
                <input type="hidden" name="mobile" value="{phone}">
                <input type="hidden" name="surl" value="https://onstock.in/payment/success/">
                <input type="hidden" name="furl" value="https://onstock.in/payment/failure/">
                <input type="hidden" name="udf1" value="{userid}">
                <input type="hidden" name="service_provider" value="payu_paisa" size="64" />
                <script>
                document.body.onload = function(ev){{
                     document.payuForm.submit();
                }}
                </script>
            </form>
            </body>
            """
            remark = Remarks.objects.filter(remark = 'PAYU PAYMENT GATEWAY').first()
            Transaction.objects.create(user=request.user,amount=amount,transaction_id=txnid,checksum='PAYU',status='PENDING',transaction_type='DEPOSIT',remark=remark)
            return HttpResponse(html_form)
            # hash_string = f"{gateway.payu_marchent_key}|{order_id}|{amount}|{'Onstock Deposit'}|{request.user.first_name}|{request.user.email}|{request.user.username}||||||||||{gateway.payu_marchent_salt}"
            # payment_data = {
            #     'key': gateway.key,  # Replace with dynamic amount
            #     'amount': amount,  # Replace with dynamic amount
            #     'hash_string': amount,  # Replace with dynamic amount
            #     'productinfo': 'Onstock Deposit',
            #     'firstname': request.user.first_name,
            #     'email': request.user.email,
            #     'phone': request.user.phone_number,
            #     'txnid': order_id,  # Unique transaction ID
            #     'surl': 'https://onstock.in/payment/success/',  # Success URL
            #     'furl': 'https://onstock.in/payment/failure/',  # Failure URL
            # }
            # # Generate hash for checkout
            # return render(request, 'payment_form.html', {'data': payment_data})
    return redirect('/transactions')

@csrf_exempt
def payment_success(request):
    try:
        order_id = request.POST.get('txnid')
        person = Transaction.objects.filter(transaction_id=order_id).first()
        person.status = 'COMPLETED'
        person.save()
        messages.success(request,"Congratulations! Funds added successfully.")
    except:
        messages.error(request,"Payment Cancelled. Please contact us for further details.")
    return redirect("/transactions")


@csrf_exempt
def payment_failure(request):
    print(request.POST)
    try:
        order_id = request.POST.get('txnid')
        person = Transaction.objects.filter(transaction_id=order_id).first()
        person.status = 'FAILED'
        person.save()
    except:
        pass
    messages.error(request,"Payment Failed. Please contact us for further details.")
    return redirect("/transactions")


@csrf_exempt
def paymentStatus(request,order_id):
    try:
        person = Transaction.objects.filter(transaction_id=order_id).first()
        if request.POST.get("status") == 'SUCCESS':
            person.status = 'COMPLETED'
            person.save()
            messages.success(request,"Congratulations! Funds added successfully.")
            return redirect("/transactions")
        else:
            messages.error(request,"Payment Cancelled. Please contact us for further details.")
            return redirect("/transactions")
    except:
        messages.error(request,"Payment Cancelled. Invalid request")
        return redirect("/transactions")

@login_required
def performance(request):
    start_date_str = ''
    end_date_str = ''
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        if start_date_str and end_date_str:
            # Convert date strings to datetime objects
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Filter positions based on user and date range
            pfm = Position.objects.filter(
                user=request.user,
                is_closed=True,
                last_traded_datetime__date__range=[start_date, end_date]
            )
        else:
            pfm = Position.objects.filter(user=request.user, is_closed=True)
    else:
        # Default behavior (no date filter applied initially)
        pfm = Position.objects.filter(user=request.user, is_closed=True)

    context = {
        'start_date_str':start_date_str,
        'end_date_str':end_date_str,
        'pfm': pfm
    }
    return render(request, 'dashboard/performance.html', context)



def upstox_cred(request,secret):
    if request.method == 'GET':
        try:
            code = request.GET.get('code')
            obj = Upstox.objects.filter(secret_key=secret).first()
            obj.code = code
            obj.save()
            data = {
                'code': code,
                'client_id': obj.api_key,
                'client_secret': obj.secret_key,
                'redirect_uri': obj.redirect_uri,
                'grant_type': 'authorization_code',
            }
            url = 'https://api-v2.upstox.com/login/authorization/token'
            response = requests.post(url,data=data)
            response = response.json()
            obj.access_token = response['access_token']
            obj.save()
            return redirect('/admin/settings/upstox')
        except Exception as e:
            messages.error(request,f'Something went wrong ! {e}')
            return redirect('/admin/settings/upstox')
        
def close_position(request):
    call_command('close_positions')
    return HttpResponseRedirect("/admin/")

def load_instruments_in_background():
    call_command('load_instruments')

def update_symbols(request):
    thread = threading.Thread(target=load_instruments_in_background)
    thread.start()
    return HttpResponseRedirect("/admin/")

@login_required
@permission_required('is_superuser')
@user_passes_test(lambda u: u.is_superuser)
def closepos(request,id):
    try:
        i = Position.objects.filter(id=id).first()
        order_type = 'SELL'
        quantity = i.quantity
        if quantity < 0:
            order_type = 'SELL'
            quantity = quantity * -1
        market_order(i.user,i.symbol,i.instrument_key,i.token,quantity,order_type,i.product,0,0,'Market')
    except:
        pass
    return HttpResponseRedirect("/admin/app/position/")