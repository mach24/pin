import web

from api.utils import api_response, save_api_request
from api.views.base import BaseAPI

from mypinnings.database import connect_db
import facebook

db = connect_db()


class PostingOnUserPage(BaseAPI):
    """
    Provides sharing pins to social networks
    
    Method PostingOnUserPage must receive next required params:

    share_list - list of pin's ids
    access_token - access token for social network
    social_network - name of social network (for example "facebook")
    """
    def POST(self):
        """
        Share pins to social network
        """
        request_data = web.input(
            share_list=[],
        )

        # Get data from request
        share_list = map(int, request_data.get("share_list"))
        access_token = request_data.get("access_token")
        social_network = request_data.get("social_network")
        csid_from_client = request_data.get('csid_from_client')
        logintoken = request_data.get('logintoken')
        user_status, user_id = self.authenticate_by_token(logintoken)

        # User id contains error code
        if not user_status:
            return user_id
        user = db.select('users', {'id': user_id}, where='id=$id')[0]
        csid_from_server = user['seriesid']

        # Initialize default posted pins list
        posted_pins = []
        # Setting default status code as 200
        status = 200
        # Setting empty error
        error_code = ""

        # Check input data and set appropriate code if not valid
        if not access_token or not social_network:
            status = 400
            error_code = "Invalid input data"
        else:
            posted_pins, status, error_code = share(
                access_token,
                share_list,
                social_network,
            )

        # Setting data for return
        data = {
            "posted_pins": posted_pins
        }

        response = api_response(data=data,
                                status=status,
                                error_code=error_code,
                                csid_from_client=csid_from_client,
                                csid_from_server=csid_from_server)
        return response


def share(access_token, share_list, social_network="facebook"):
    """
    Share pins to social network, using access token
    """
    # Initialize default access token status
    access_token_status = True

    # Get status of access token for social network
    if social_network == "facebook":
        access_token_status = check_facebook_access_token(access_token)

    if not access_token_status:
        return [], 400, "Bad access token"

    # Initialize shared pins list
    shared_pins = []

    for pin_id in share_list:
        pin = db.select('pins', vars={'id': pin_id}, where='id=$id')

        if len(pin) == 0:
            continue

        pin = pin[0]
        message = ""
        if pin.get('name'):
            message += pin.get('name')+"\n"
        if pin.get('description'):
            message += pin.get('description')+"\n"
        if pin.get('price'):
            message += "Price: "+pin.get('price')+"\n"
        if pin.get('link'):
            message += pin.get('link')+"\n"

        image = pin.get('image_url')
        if image:
            image = open(image)
        else:
            image = None

        share_pin_status = False
        if social_network == "facebook":
            share_pin_status = share_via_facebook(access_token,
                                                  message,
                                                  image)

        if share_pin_status:
            shared_pins.append(pin_id)

    return shared_pins, 200, ""


def check_facebook_access_token(access_token):
    try:
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object("me")
        return True
    except facebook.GraphAPIError, exc:
        return False


def share_via_facebook(access_token, message, image):
    """
    Share pin to facebook
    """
    try:
        graph = facebook.GraphAPI(access_token)
        if image:
            graph.put_photo(image, message)
        else:
            graph.put_object("me", "feed", message=message)

        return True
    except Exception, exc:
        return False