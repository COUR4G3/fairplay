from flask import request


def apply_paged_pagination(query, page_param="page", per_page=25):
    page = request.args.get(page_param, 1, type=int)

    query = query.paginate(page=page, per_page=per_page)

    return query
