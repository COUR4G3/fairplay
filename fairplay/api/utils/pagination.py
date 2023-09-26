from flask import after_this_request, request, url_for


def apply_paged_pagination(
    query,
    page_param="page",
    per_page_default=20,
    per_page_max=1000,
    per_page_param="per_page",
):
    page = request.args.get(page_param, 1, type=int)
    per_page = request.args.get(per_page_param, per_page_default, type=int)

    results = query.paginate(
        page=page, per_page=per_page, error_out=True, max_per_page=per_page_max
    )

    count = len(results.items)

    args = request.args.copy()
    link_header = {"self": url_for(request.endpoint, **request.args)}
    args.pop("page", None)

    if results.has_next:
        link_header["next"] = url_for(request.endpoint, page=results.next_num, **args)
    if results.has_prev:
        link_header["prev"] = url_for(request.endpoint, page=results.prev_num, **args)

    link_header = ", ".join(f'<{url}>; rel="{rel}"' for rel, url in link_header.items())

    @after_this_request
    def add_pagination_headers(response):
        response.headers.update(
            {
                "Link": link_header,
                "X-Pagination-Count": count,
                "X-Pagination-Page": page,
                "X-Pagination-Pages": results.pages,
                "X-Pagination-Per-Page": results.per_page,
                "X-Pagination-Total": results.total,
            }
        )

        return response

    return results.query


def apply_limit_offset_pagination(
    query,
    limit_default=20,
    limit_param="limit",
    limit_max=1000,
    offset_param="offset",
):
    limit = request.args.get(limit_param, limit_default, type=int)
    limit = min(limit_max, limit)

    offset = request.args.get(offset_param, 0, type=int)

    total = query.count()

    query = query.limit(limit).offset(offset)

    count = query.count()

    args = request.args.copy()
    link_header = {"self": url_for(request.endpoint, **request.args)}
    args.pop("offset", None)

    if offset + count < total:
        link_header["next"] = url_for(request.endpoint, offset=offset + count, **args)
    if offset > 0:
        prev_offset = offset - count
        prev_count = count

        # handle odd case where pagination limit may have changed
        if prev_offset < 0:
            prev_offset = 0
            prev_count = abs(prev_offset)

        args.pop("count", None)

        link_header["prev"] = url_for(
            request.endpoint, offset=prev_offset, count=prev_count, **args
        )

    link_header = ", ".join(f'<{url}>; rel="{rel}"' for rel, url in link_header.items())

    @after_this_request
    def add_pagination_headers(response):
        response.headers.update(
            {
                "X-Pagination-Count": count,
                "X-Pagination-Limit": limit,
                "X-Pagination-Offset": offset,
                "X-Pagination-Total": total,
            }
        )

        return response

    return query
