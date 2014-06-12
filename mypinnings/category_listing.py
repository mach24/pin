import json
import logging

import web

from mypinnings import database
from mypinnings import session
from mypinnings import template
from mypinnings import cached_models
from mypinnings.conf import settings
from mypinnings import auth
from mypinnings.api import api_request, convert_to_id, convert_to_logintoken
from mypinnings import pin_utils
from mypinnings.auth import logged_in


logger = logging.getLogger('mypinnings.categories')

class PageCategory:
    def GET(self, slug=None):
        self.db = database.get_db()
        self.sess = session.get_session()
        auth.force_login(self.sess)
        if slug:
            results = self.db.where('categories', slug=slug)
            for r in results:
                self.category = r
                break
            else:
                self.category = {'name': 'Random', 'id': 0}
        else:
            self.category = {'name': 'Random', 'id': 0}

        self.ajax = int(web.input(ajax=0).ajax)

        if self.ajax:
            return self.get_more_items_as_json()
        else:
            self.sess['seen_items'] = set()
            return self.template_for_showing_categories()

    # def get_items_query(self):
    #     if self.category['id'] == 0:
    #         self.where = 'random() < 0.1'
    #     else:
    #         results = self.db.where(table='categories',
    #                                 parent=self.category['id'])
    #         subcategories_ids = [str(self.category['id'])]
    #         for row in results:
    #             subcategories_ids.append(str(row.id))
    #         subcategories_string = ','.join(subcategories_ids)
    #         self.where = 'categories.id in ({})'.format(subcategories_string)
    #     start = web.input(start=False).start
    #     if start:
    #         offset = 0
    #         self.sess['offset'] = 0
    #     else:
    #         offset = self.sess.get('offset', 0)
    #     self.query = '''
    #         select
    #             tags.tags, pins.*, categories.id as category,
    #             categories.name as cat_name, users.pic as user_pic,
    #             users.username as user_username, users.name as user_name,
    #             count(distinct p1) as repin_count,
    #             count(distinct l1) as like_count
    #         from pins
    #             left join tags on tags.pin_id = pins.id
    #             left join pins p1 on p1.repin = pins.id
    #             left join likes l1 on l1.pin_id = pins.id
    #             left join users on users.id = pins.user_id
    #             left join follows on follows.follow = users.id
    #             join pins_categories on pins.id=pins_categories.pin_id
    #             join categories
    #             on pins_categories.category_id = categories.id
    #         where ''' + self.where + '''
    #         group by tags.tags, categories.id, pins.id, users.id
    #         order by timestamp desc
    #         offset %d limit %d''' % \
    #         (offset * settings.PIN_COUNT, settings.PIN_COUNT)
    #     return self.query

    def template_for_showing_categories(self):
        subcategories = self.db.where(
            table='categories',
            parent=self.category['id'],
            order='is_default_sub_category desc, name'
        )
        results = self.db.where(table='categories',
                                parent=self.category.get('parent'),
                                order='is_default_sub_category desc, name')
        siblings_categories = []
        for row in results:
            if row.id != self.category['id']:
                siblings_categories.append(row)
        results = self.db.where(table='categories',
                                id=self.category.get('parent'))
        for row in results:
            parent = row
            break
        else:
            parent = None
        data = {
            'csid_from_client': "",
            'user_id': self.sess.user_id
        }

        boards = api_request("/api/profile/userinfo/boards",
                             data=data).get("data", [])
        boards = [pin_utils.dotdict(board) for board in boards]

        # Check if user follows the category
        sess_user_id = self.sess.user_id
        follow_cat = None
        if logged_in(self.sess):
            cat_id = self.category['id']
            follow_cat = self.is_followed(sess_user_id, cat_id, 'category') 
        print '#######################################################'
        print follow_cat


        return template.ltpl('category',
                             self.category,
                             cached_models.get_categories(),
                             subcategories,
                             boards,
                             siblings_categories,
                             parent,
                             follow_cat)

    def get_items(self):
        sess = session.get_session()
        start = web.input(start=False).start
        if start:
            offset = 1
            self.sess['offset'] = 1
        else:
            offset = self.sess.get('offset', 1)

        if offset == 0:
            return []

        logintoken = convert_to_logintoken(self.sess.get('user_id'))
        data = {
            "csid_from_client": '',
            "logintoken": logintoken,
            "page": offset,
            "query_type": "range",
            "items_per_page": settings.PIN_COUNT
        }

        if self.category['id'] != 0:
            results = self.db.where(table='categories',
                                    parent=self.category['id'])
            data['category_id_list'] = [self.category['id']]
            for row in results:
                data['category_id_list'].append(str(row.id))

        data = api_request("api/image/query/category", "POST", data)
        if data['status'] == 200:
            if offset >= data['data']['pages_count']:
                self.sess['offset'] = 0
            data_for_image_query = {
                "csid_from_client": '',
                "logintoken": logintoken,
                "query_params": data['data']['image_id_list']
            }
            data_from_image_query = api_request("api/image/query",
                                                "POST",
                                                data_for_image_query)

            if data_from_image_query['status'] == 200:
                set_of_seen_items = self.sess['seen_items']
                items_without_duplicates = []
                for item in data_from_image_query['data']['image_data_list']:
                    itemid = item['id']
                    if itemid not in set_of_seen_items:
                        set_of_seen_items.add(itemid)
                        items_without_duplicates.append(item)
                return items_without_duplicates

        return []

    def get_more_items_as_json(self):
        # self.get_items_query()
        # pins = self.db.query(self.query)
        pins = self.get_items()
        pin_list = []
        for pin in pins:
            pin_list.append(pin)

        offset = self.sess.get('offset', 1)
        if offset > 0 and len(pin_list) > 0:
            offset = offset + 1
        self.sess['offset'] = offset
        json_pins = json.dumps(pin_list)
        return json_pins

    def is_followed(self, follower, follow, f_type):
        following = self.db.select('newsfeed', where="follower = $follower_id AND follow = $follow_id AND feed_type= $f_type", vars={'follower_id': follower, 'follow_id': follow, 'f_type': f_type})
        following = True if len(following) >= 1 else False
        return following


