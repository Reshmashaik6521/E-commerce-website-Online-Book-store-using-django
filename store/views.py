from django.shortcuts import redirect, render,get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login,logout
import json
import datetime
from .models import *
from .utils import cookieCart, cartData, guestOrder
from .forms import CreateUserForm


#register page here
def registerPage(request):
     form = CreateUserForm()

     if request.method == 'POST':
          form = CreateUserForm(request.POST)
          if form.is_valid():
               form.save()
               user = form.cleaned_data.get('username')
               messages.success(request, 'Account was successfully created for '+ user)
               return redirect('login')
          

     context = {'form': form}
     return render(request, 'accounts/register.html', context)

#login page here
def loginPage(request):
     if request.method == 'POST':
          username = request.POST.get('username')
          password = request.POST.get('password')

          user = authenticate(request, username=username, password=password)

          if user is not None:
               login(request, user)
               return redirect('store')
          else:
               messages.info(request,"Username or Password is incorrect")

     return render(request,'accounts/login.html')

#logout page here
def logoutUser(request):
     logout(request)
     return redirect('store')


#store view here
def store(request):
     data = cartData(request)
     cartItems = data['cartItems']
     
     books = Book.objects.all() 
     context = {'books': books, 'cartItems': cartItems, 'shipping': False}
     return render(request, 'store/store.html', context)

def cart(request):
     data = cartData(request)
     cartItems = data['cartItems']
     order = data['order']
     items = data['items']

     context = {'items': items, 'order': order, 'cartItems': cartItems}
     return render(request, 'store/cart.html', context)



def checkout(request):
     data = cartData(request)
     cartItems = data['cartItems']
     order = data['order']
     items = data['items']

     context = {'items': items, 'order': order,'cartItems': cartItems}
     return render(request, 'store/checkout.html', context)


def updateItem(request):
     data = json.loads(request.body)
     bookId = data['bookId']
     action = data['action']
     print('Action:', action)
     print('bookId:', bookId)

     customer = request.user.customer
     book = Book.objects.get(id=bookId)
     order, created = Order.objects.get_or_create(customer=customer,complete=False)

     orderItem, created = OrderItem.objects.get_or_create(order=order,book=book)

     if action == 'add':
          orderItem.quantity = (orderItem.quantity + 1)
     elif action == 'remove':
          orderItem.quantity = (orderItem.quantity - 1)
     
     orderItem.save()

     if orderItem.quantity <= 0:
          orderItem.delete()

     return JsonResponse('Item was added', safe=False)


def processOrder(request):
     transaction_id = datetime.datetime.now().timestamp()
     data = json.loads(request.body)
     if request.user.is_authenticated:
          customer = request.user.customer
          order, created = Order.objects.get_or_create(customer=customer,complete=False)
          
     else:
          customer, order = guestOrder(request,data)

     total = float(data['form']['total'])
     order.transaction_id = transaction_id

     if total == float(order.get_cart_total) :
          order.complete = True
     order.save()

     if order.shipping == True:
          ShippingAddress.objects.create(
               customer = customer,
               order = order,
               city = data['shipping']['city'],
               area = data['shipping']['area'],
               address = data['shipping']['address'],
               phone = data['shipping']['phone'],
          )
     return JsonResponse('Payment complete!', safe=False) 



def BookDetailView(request,book_id):
     data = cartData(request)
     cartItems = data['cartItems']
     book = get_object_or_404(Book, pk=book_id)
     template_name = 'books/book_detail.html'
     context = {'book':book, 'cartItems':cartItems}
     return render(request,template_name, context)

from django.views.generic import FormView
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm

class PaypalFormView(FormView):
    template_name = 'paypal_form.html'
    form_class = PayPalPaymentsForm

    def get_initial(self):
        return {
            'business': 'your-paypal-business-reshmashaik6521@gmail.com',
            'amount': 20,
            'currency_code': 'INR',
            'item_name': 'Example item',
            'invoice': 1234,
            'notify_url': self.request.build_absolute_uri(reverse('paypal-ipn')),
            'return_url': self.request.build_absolute_uri(reverse('paypal-return')),
            'cancel_return': self.request.build_absolute_uri(reverse('paypal-cancel')),
            'lc': 'EN',
            'no_shipping': '1',
        }


 #def AuthorDetailView(request, pk):
 #    data = cartData(request)
 #    cartItems = data['cartItems']
 #    author = get_object_or_404(Author, pk=pk)
 #    template_name = 'authors/author_detail.html'
 #    context = {'author':author, 'cartItems':cartItems}
 #     return render(request, template_name, context)
     