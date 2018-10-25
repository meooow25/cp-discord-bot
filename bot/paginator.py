import math


def paginate(list_, per_page, page_num):
    num_pages = math.ceil(len(list_) / per_page)
    page_num = min(page_num, num_pages)
    end = page_num * per_page
    begin = end - per_page
    return list_[begin:end], page_num, num_pages
