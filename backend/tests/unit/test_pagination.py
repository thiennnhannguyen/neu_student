import pytest
from sqlalchemy import Column, Integer, MetaData, Table, insert, select

from app.common.errors import ApiError
from app.common.pagination import paginate, paginate_list
from app.extensions import db

items_table = Table("page_items", MetaData(), Column("id", Integer, primary_key=True))


@pytest.fixture
def make_items(app):
    items_table.create(db.engine)
    yield lambda count: db.session.execute(
        insert(items_table), [{"id": i} for i in range(1, count + 1)]
    )
    db.session.rollback()
    items_table.drop(db.engine)


QUERY = select(items_table.c.id).order_by(items_table.c.id)


def test_defaults_to_first_page_of_20(make_items):
    make_items(25)

    result = paginate(QUERY)

    assert result["items"] == list(range(1, 21))
    assert (result["page"], result["page_size"], result["total"]) == (1, 20, 25)


def test_returns_requested_page_from_query_string_values(make_items):
    make_items(25)

    result = paginate(QUERY, page="2", page_size="10")

    assert result["items"] == list(range(11, 21))
    assert (result["page"], result["page_size"], result["total"]) == (2, 10, 25)


def test_page_after_last_returns_empty_items_with_total(make_items):
    make_items(3)

    assert paginate(QUERY, page=5) == {"items": [], "page": 5, "page_size": 20, "total": 3}


def test_empty_data(make_items):
    assert paginate(QUERY) == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_page_size_100_is_allowed(make_items):
    make_items(101)

    result = paginate(QUERY, page_size=100)

    assert len(result["items"]) == 100
    assert result["total"] == 101


@pytest.mark.parametrize(
    "kwargs",
    [
        {"page_size": 101},
        {"page_size": "101"},
        {"page_size": 0},
        {"page_size": "abc"},
        {"page": 0},
        {"page": -1},
        {"page": "-1"},
        {"page": "1.5"},
        {"page": ""},
        {"page": True},
    ],
)
def test_invalid_values_raise_422(app, kwargs):
    with pytest.raises(ApiError) as caught:
        paginate(QUERY, **kwargs)

    assert caught.value.status == 422
    assert caught.value.code == "VALIDATION_ERROR"


def test_over_limit_returns_standard_error_through_http(app):
    from flask import request

    @app.get("/api/_trang")
    def page_route():
        return paginate(QUERY, request.args.get("page"), request.args.get("page_size"))

    response = app.test_client().get("/api/_trang?page_size=101")

    assert response.status_code == 422
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"] == {"page_size": 101, "max": 100}


def test_paginate_list_has_same_shape_as_paginate():
    rows = list(range(1, 26))

    assert paginate_list(rows) == {"items": rows[:20], "page": 1, "page_size": 20, "total": 25}
    assert paginate_list(rows, "2", "20")["items"] == rows[20:]
    assert paginate_list(rows, "9")["items"] == []


@pytest.mark.parametrize(("page", "size"), [("0", None), ("x", None), (None, "101"), (None, "0")])
def test_paginate_list_rejects_bad_params(page, size):
    with pytest.raises(ApiError) as caught:
        paginate_list([], page, size)
    assert caught.value.status == 422
