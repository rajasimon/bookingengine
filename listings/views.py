from datetime import datetime

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Listing, Reservation
from .serializers import ListingSerializer


class UnitAPIView(APIView):
    """
    API for getting the units ( filter hotels and apartments)
    """

    def get(self, request):
        """
        params:
        max_price - integer
        checK_in - date string
        check_out - date string
        """
        max_price = request.query_params.get("max_price")
        check_in = request.query_params.get("check_in")
        check_out = request.query_params.get("check_out")

        # Convert the check in and out string to datetime object.
        check_in_format = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_format = datetime.strptime(check_out, "%Y-%m-%d")

        hotel_listings = Listing.objects.filter(listing_type="hotel")
        apart_listings = Listing.objects.filter(listing_type="apartment")

        # Out of all apart_listings check against the reservation and make
        # sure listing is not reserved in those check in and check out period.
        for listing in apart_listings:
            reservation = Reservation.objects.filter(
                Q(
                    Q(from_date__gte=check_in_format)
                    & Q(from_date__lte=check_out_format)
                    | Q(to_date__gte=check_in_format)
                    & Q(to_date__lte=check_out_format),
                ),
                booking_info__listing=listing,
            ).all()
            if reservation:
                apart_listings = apart_listings.exclude(
                    id__in=[each["id"] for each in reservation.values("id")]
                )

        # Max price filter for apartments
        apart_listings = apart_listings.filter(booking_info__price__lte=max_price)

        # Hotel should have at least 1 Hotel Room available from any of the HotelRoomTypes
        for listing in hotel_listings:
            # Check the hotel room is not booked
            reservation = Reservation.objects.filter(
                booking_info__listing=listing,
            ).all()
            if reservation:
                # For hotel check if the reservation and check the rooms.
                for each_reserv in reservation:
                    remaining_rooms = (
                        each_reserv.booking_info.hotel_room_type.hotel_rooms.exclude(
                            id=each_reserv.hotel_room.id
                        )
                    )
                    if not remaining_rooms:
                        hotel_listings.exclude(id=listing.id)

        # Sorting
        listings = apart_listings | hotel_listings
        listings = listings.order_by("booking_info__price")
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)
