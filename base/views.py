from django.http import HttpResponse
from rest_framework import generics, serializers, status, permissions
from .serializers import UserRegistrationSerializer, UserLoginSerializer, TransferSerializer, \
    PasswordVerificationSerializer, TransactionSerializer, NotificationSerializer, TopUpRequestSerializer, UpdateHeightWeightSerializer, \
    CanteenSerializer, FoodCategorySerializer, FoodSerializer, OrderSerializer, FeaturedFoodSerializer, UserVerificationSerializer
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from .models import Transaction, Notification, TopUpRequest, Canteen, FoodCategory, Food, Order, FeaturedFood
from rest_framework.permissions import IsAdminUser


CustomUser = get_user_model()  # Ensure CustomUser is correctly referenced


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access to this view


# @csrf_exempt
class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone_number = serializer.validated_data.get('phone_number')
            password = serializer.validated_data.get('password')

            User = get_user_model()

            # Find user by phone number if provided
            user = None
            if phone_number:
                try:
                    user = User.objects.get(phone_number=phone_number)
                except User.DoesNotExist:
                    return Response({"error": "Invalid phone number"}, status=status.HTTP_401_UNAUTHORIZED)
            elif email:
                user = authenticate(request, email=email, password=password)
                if not user:
                    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

            if user and user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            # Access balance and first_name directly from the CustomUser model
            balance = user.balance
            first_name = user.first_name

            return Response({
                'balance': balance,
                'first_name': first_name
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            # Access all the fields directly from the CustomUser model
            user_details = {
                'phone_number': user.phone_number,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'balance': user.balance,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined,
                'height': user.height,
                'weight': user.weight,
                'bmi': user.bmi,
            }

            return Response(user_details, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class PasswordVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordVerificationSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data['password']
            user = request.user

            if user.check_password(password):
                return Response({"message": "Password is correct"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.contrib.auth import authenticate

User = get_user_model()

class UserVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            phone_number = serializer.validated_data.get('phone_number')
            password = serializer.validated_data.get('password')

            User = get_user_model()
            user = None

            if phone_number:
                user = User.objects.filter(phone_number=phone_number).first()
            if email:
                user = User.objects.filter(email=email).first()

            if user and authenticate(email=user.email, password=password):
                return Response({"message": "User verified"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class TransferView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            recipient_phone_number = serializer.validated_data['recipient_phone_number']
            amount = serializer.validated_data['amount']

            sender = request.user
            try:
                recipient = User.objects.get(phone_number=recipient_phone_number)
            except User.DoesNotExist:
                return Response({"error": "Recipient does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            if sender == recipient:
                return Response({"error": "Cannot transfer money to yourself."}, status=status.HTTP_400_BAD_REQUEST)

            if sender.balance < amount:
                return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

            # Update balances
            sender.balance -= amount
            recipient.balance += amount
            sender.save()
            recipient.save()

            # Create transaction record
            Transaction.objects.create(sender=sender, recipient=recipient, amount=amount)

            return Response({"message": "Transfer successful."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransferBuyerAndVendorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            recipient_phone_number = serializer.validated_data['recipient_phone_number']
            amount = serializer.validated_data['amount']

            vendor = request.user
            if not vendor.is_staff:
                return Response({"error": "You must be a vendor to request payments."},
                                status=status.HTTP_403_FORBIDDEN)

            try:
                # Find the buyer based on the phone number
                buyer = CustomUser.objects.get(phone_number=recipient_phone_number)
                if buyer.is_staff:
                    return Response({"error": "Recipient must be a buyer."}, status=status.HTTP_400_BAD_REQUEST)

                # Check if the buyer has enough balance
                if buyer.balance < amount:
                    return Response({"error": "Buyer has insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

                # Update balances
                buyer.balance -= amount
                vendor.balance += amount
                buyer.save()
                vendor.save()

                # Create transaction record
                Transaction.objects.create(sender=buyer, recipient=vendor, amount=amount)

                return Response({"message": "Transfer successful."}, status=status.HTTP_200_OK)

            except CustomUser.DoesNotExist:
                return Response({"error": "Recipient does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionListView(APIView):
    def get(self, request, *args, **kwargs):
        transactions = Transaction.objects.filter(sender=request.user) | Transaction.objects.filter(recipient=request.user)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class NotificationListCreateView(generics.ListCreateAPIView):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]


class NotificationDetailView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Retrieve notifications for authenticated users
        return Notification.objects.all().order_by('-created_at')


class TopUpRequestCreateView(generics.ListCreateAPIView):
    queryset = TopUpRequest.objects.all()
    serializer_class = TopUpRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Associate the request with the logged-in admin


class TopUpRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TopUpRequest.objects.all()
    serializer_class = TopUpRequestSerializer
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        top_up_request = self.get_object()
        data = request.data

        is_approved = data.get('is_approved')
        if is_approved is not None:
            if is_approved.lower() == 'true':  # Ensure case-insensitive comparison
                top_up_request.is_approved = True
                user = top_up_request.user

                # Use a transaction to ensure consistency
                with transaction.atomic():
                    # Update the user's balance
                    user.balance += top_up_request.amount
                    user.save()

                    # Save the top-up request
                    top_up_request.save()

                # Log the success (optional for debugging)
                print(f"Top-up approved: Added {top_up_request.amount} to {user.email}'s balance. New balance: {user.balance}")

            else:
                top_up_request.is_approved = False
                top_up_request.save()
                print("Top-up rejected")

            return Response(TopUpRequestSerializer(top_up_request).data)
        else:
            return Response({"error": "Field 'is_approved' is required"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateHeightWeightView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        data = request.data

        height = data.get('height')
        weight = data.get('weight')

        if height is not None:
            user.height = height
        if weight is not None:
            user.weight = weight

        user.save()

        return Response({"message": "Height and weight updated successfully"}, status=status.HTTP_200_OK)

# Food System
class CanteenListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Canteen.objects.all()
    serializer_class = CanteenSerializer


class FoodCategoryListView(generics.ListAPIView):
    serializer_class = FoodCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        canteen_id = self.kwargs['canteen_id']
        return FoodCategory.objects.filter(canteen_id=canteen_id)

class FoodListView(generics.ListAPIView):
    serializer_class = FoodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return Food.objects.filter(category_id=category_id)

class FeaturedFoodListView(generics.ListAPIView):
    queryset = FeaturedFood.objects.all()
    serializer_class = FeaturedFoodSerializer
    permission_classes = [IsAuthenticated]

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        food = serializer.validated_data['food']
        quantity = serializer.validated_data['quantity']
        total_price = food.price * quantity
        serializer.save(user=self.request.user, total_price=total_price, vendor=food.vendor)

    def get_serializer_context(self):
        return {'request': self.request}

class OrderListView(generics.ListAPIView):
    # queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:  # Assuming vendor users are marked as staff
            return Order.objects.filter(vendor=user).order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')

class UpdateOrderPaymentStatusView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        order.is_paid = True
        order.save()
        return Response({"status": "payment updated"}, status=status.HTTP_200_OK)

@ensure_csrf_cookie
def csrf_token_view(request):
    # return JsonResponse({'csrfToken': get_token(request)})
    # return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE')})
    return JsonResponse({'csrfToken': get_token(request)})


def hello_world(request):
    return HttpResponse("Juan Bytes Backend, working yan syempre")
