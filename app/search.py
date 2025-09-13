from flask import current_app


def add_to_index(index, model):
    if not current_app.elasticsearch:
        return [], 0
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return [], 0
    current_app.elasticsearch.delete(index=index, id=model.id)

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        print("Elasticsearch not configured")
        return [], 0
    try:
        search = current_app.elasticsearch.search(
            index=index,
            query={'multi_match': {'query': query, 'fields': ['*']}},
            from_=(page - 1) * per_page,
            size=per_page)
        ids = [int(hit['_id']) for hit in search['hits']['hits']]
        return ids, search['hits']['total']['value']
    except Exception as e:
        print(f"Elasticsearch error: {e}")
        return [], 0