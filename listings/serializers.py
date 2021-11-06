from rest_framework.serializers import ModelSerializer

from .models import Listing


class ListingSerializer(ModelSerializer):
    class Meta:
        model = Listing
        fields = ["listing_type", "title", "country", "city"]
