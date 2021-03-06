import web
import logging
from web.utils import storify
from mypinnings import pin_utils

from mypinnings.conf import settings
import redis as redis_server

db = None
redis = None
logger = logging.getLogger('mypinnings.pin_utils')
logger.addHandler(logging.NullHandler())


def connect_db():
    global db
    if db is not None:
        return db
    db = web.database(**settings.params)
    return db


def dbget(table, row_id):
    global db
    rows = db.select(table, where='id = $id', vars={'id': row_id})
    return rows[0] if rows else None


def get_db():
    global db
    return db


def redis_connect():
    global redis
    if redis is not None:
        return redis
    try:
        pool = redis_server.ConnectionPool(host=settings.redis['host'],
                                           port=settings.redis['port'],
                                           db=settings.redis['db'])
        redis = redis_server.StrictRedis(connection_pool=pool)
        redis.client_setname('mypinnings_redis')
    except redis_server.ConnectionError:
        logger.error("""Error in connection to redis server. Please check if
                     redis-server is running.""")
    return redis

redis = redis_connect()

def redis_set(key, value, domain='pin_'):
    domain_key = domain + str(key)
    try:
        redis.set(domain_key, value)
    except:
        logger.error('Error in addition of a value to redis')


def redis_has(key, domain='pin_'):
    domain_key = domain + str(key)
    try:
        if(redis_get(domain_key) is not None):
            return True
        else:
            return False
    except:
        logger.error('Error in triggering redis_has method')
    return False


def redis_get(key, domain='pin_'):
    domain_key = domain + str(key)
    try:
        return redis.get(domain_key)
    except:
        logger.error('Couldnt get a value from redis')


def redis_append(key, value):
    try:
        return redis.append(key, value)
    except:
        logger.error('Couldnt append %d value in %d', value, key)
        return False
    return True


def redis_zadd(key, index, value, domain='user_'):
    domain_key = domain + str(key)
    try:
        ''' Change index var index to value to set unique feature '''
        return redis.zadd(domain_key, value, value)
    except:
        logger.error('Coldnt zadd key %d in index %d with value %', key, index,
                     value)


def redis_zget(key, scope_start=0, scope_end=-1, domain='user_'):
    domain_key = domain + str(key)
    try:
        return redis.zrange(domain_key, scope_start, scope_end)
    except:
        logger.error('Couldnt zget key %')


def redis_remove(key, item, domain='user_'):
    domain_key = domain + str(key)
    try:
        return redis.zrem(domain_key, item[0])
    except:
        logger.error('Couldnt pop the element from redis')


def redis_zcount(key, scope_start=0, scope_end=-1, domain='user_'):
    domain_key = domain + str(key)
    try:
        ''' Also redis.zcount can be used if scope definition needed  '''
        # return redis.zcount(domain_key, scope_start, scope_end)
        elems = redis.zcard(domain_key)
        return elems
    except:
        logger.error('Couldnt count the sorted set elements')


def redis_get_user_pins(user_id, offset=0, limit=-1, return_count=False):
    pins_redis = redis_zget(user_id, offset, limit)
    pins_len = len(pins_redis)
    pins = list()
    for pin in pins_redis:
        pin_temp = redis_get(pin)
        eval_tmp = eval(pin_temp)
        store_tmp = pin_utils.dotdict(eval_tmp)
        pins.append(store_tmp)
    if return_count == True:
        pins.append(pins_len)
    return pins


def redis_get_connection():
    global redis
    return redis


def redis_setname(name):
    redis = redis_get_connection()
    try:
        redis.client_setname(name)
    except Exception, e:
        logger.error('Couldnt set redis client name', e)
        return False
    return True


def redis_create_pipe():
    try:
        return redis.pipeline()
    except:
        logger.error('Couldnt create pipline')


def get_user_quota():
    """
        @TODO user quota should be set somewhere in user admin panel
    """
    return 200


# Below are helper function for redis management
def get_users():
    return db.query('SELECT * FROM users')


def create_feed(user_id, pin_id, params):
    """ Creates cached pin and deletes oldest pin if the limit exceedes the
    user quota """
    try:
        create_feed.counter += 1
        if redis_has(pin_id) is not True:
            # Start transaction
            pipe = redis_create_pipe()
            if(redis_zcount(user_id) > get_user_quota()):
                item = redis_zget(user_id, 0, 0) # the last element
                redis_remove(user_id, item)
            try:
                redis_set(pin_id, params)
            except Exception, e:
                print e
            redis_zadd(user_id, create_feed.counter, pin_id)
            # End transaction
            pipe.execute()
        else:
            redis_zadd(user_id, create_feed.counter, pin_id)
    except Exception, e:
        logger.error('Cannot insert feed info in the redis while adding pin',
                     exc_info=True)
create_feed.counter = 0


def generate_feed(user_id, user_username, user_name, user_pic, category, cat_name, id, name, description, link, views, price, image_url,
                  image_width, image_height, image_202_url, image_202_height,
                  image_212_url, image_212_height, product_url, price_range,
                  external_id, board_id, tags,  timestamp, repin_count=0, like_count=0):
    try:
        # There might be better way to pass the details of pin
        params = {'id': id,
                  'name': name,
                  'description': description,
                  'user_id': user_id,
                  'user_name': user_name,
                  'user_username': user_username,
                  'user_pic': user_pic,
                  'category': category,
                  'cat_name': cat_name,
                  'link': link,
                  'views': str(views),
                  'price': str(price),
                  'image_url': image_url,
                  'image_width': image_width,
                  'image_height': image_height,
                  'image_202_url': image_202_url,
                  'image_202_height': image_202_height,
                  'image_212_url': image_212_url,
                  'image_212_height': image_212_height,
                  'product_url': product_url,
                  'price_range': price_range,
                  'external_id': external_id,
                  'board_id': board_id,
                  'tags': tags,
                  'timestamp': timestamp,
                  'repin_count': 0,
                  'like_count': like_count,
                  'repin': 0}

        create_feed(user_id, pin_id=id,
                                params=params)
    except Exception, e:
        print e


def get_user_people(user_id, update_pin_id=0):

    if int(update_pin_id) != 0:
        varu = {'pin_id': update_pin_id}
        get_user_q = "SELECT * FROM pins WHERE id = $pin_id LIMIT 1"
        get_user = db.query(get_user_q, vars=varu)
        get_user = list(get_user)
        user_id = get_user[0].user_id

    query1 = '''
        SELECT follows.follower FROM follows WHERE follows.follow = {id}
        UNION
        SELECT friends.id1 FROM friends WHERE friends.id2 =
        {id}'''.format(id=user_id)

    query2 = '''
        SELECT pins.*, categories.id as category, categories.name as cat_name FROM pins
        LEFT JOIN categories on categories.id in
            (SELECT category_id FROM pins_categories WHERE pin_id = pins.id limit 1)
        WHERE user_id = {id}
        '''.format(id=user_id)

        
    theuser_query = '''
            SELECT * FROM users WHERE id = {id}
            '''.format(id=user_id)

    theuser = list(db.query(theuser_query))
    theuser = theuser[0]
    update_users = list(db.query(query1))
    user_pins = list(db.query(query2))

    if len(user_pins) <= 0 or len(update_users) <= 0 or theuser is None:
        return False


    for update_user in update_users:
        for user_pin in user_pins:
            dictpin = dict(pin_id=user_pin.id)
            tags_obj = db.select('tags', dictpin, where=("pin_id = $pin_id"))
            tags = []
            like_dict = {'pin_id': user_pin.id}
            likes_obj = db.select('likes', like_dict, where=("pin_id=$pin_id"))
            likes = len(likes_obj)

            repin_count = 0

            for tag in tags_obj:
                tags.append(tag.tags)

            if tags:
                tags = tags
            else:
                tags = ''

            user_query = '''
                SELECT * FROM users WHERE id = {id}
                '''.format(id=update_user.follower)
            user = list(db.query(user_query))
            user = user[0]

            generate_feed(update_user.follower, theuser.username, theuser.name,
                          theuser.pic, user_pin.cat_name, user_pin.category, user_pin.id, user_pin.name, 
                          user_pin.description, user_pin.link, user_pin.views, user_pin.price,
                          user_pin.image_url, user_pin.image_width,
                          user_pin.image_height, user_pin.image_202_url,
                          user_pin.image_202_height, user_pin.image_212_url,
                          user_pin.image_212_height, user_pin.product_url,
                          user_pin.price_range, user_pin.external_id,
                          user_pin.board_id, tags, user_pin.timestamp, repin_count,
                          likes)


def refresh_individual_user(user_id, pin_id=0):
    get_user_people(user_id, pin_id)


