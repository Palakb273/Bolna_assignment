from app.domain.address import Address
from app.validation.required_fields import missing_required_fields


def test_customer_description_is_premise():
    assert missing_required_fields(Address(house_flat='Sharma Medical Store', area='Market',
                                           city='Town', pincode='500032')) == ()


def test_building_landmark_do_not_identify_premise():
    assert missing_required_fields(Address(building='Towers', landmark='School')) == (
        'house_flat', 'area', 'city', 'pincode')
