# -*- coding: utf-8 -*-
"""大屏接口测试：正常返回、参数校验边界、缓存命中、404"""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["code"] == 0
    assert body["data"]["status"] == "up"


def test_overview_shape(client):
    body = client.get("/api/overview").get_json()
    assert body["code"] == 0
    d = body["data"]
    for key in ("year", "gdp_yi", "pop_wan", "gdp_per_capita", "city_cnt", "updated_at"):
        assert key in d
    assert d["city_cnt"] == 21
    assert d["gdp_yi"] > 0


def test_overview_cached(client):
    """同一接口连续两次，第二次命中 60s 缓存，updated_at 应完全一致"""
    first = client.get("/api/overview").get_json()["data"]
    second = client.get("/api/overview").get_json()["data"]
    assert first == second


def test_trend_default(client):
    body = client.get("/api/trend").get_json()
    assert body["code"] == 0
    rows = body["data"]["list"]
    assert len(rows) == 6
    assert rows[0]["year"] < rows[-1]["year"]        # 按年份升序返回


def test_trend_range_applied(client):
    rows = client.get("/api/trend?range=2").get_json()["data"]["list"]
    assert len(rows) == 2


def test_trend_invalid_range(client):
    r = client.get("/api/trend?range=abc")
    assert r.status_code == 400
    assert r.get_json()["code"] == 400


def test_trend_range_out_of_bounds(client):
    assert client.get("/api/trend?range=99").status_code == 400


def test_region_share_percent(client):
    rows = client.get("/api/region-share").get_json()["data"]["list"]
    assert len(rows) == 4
    assert abs(sum(r["pct"] for r in rows) - 100) < 0.5


def test_city_rank_desc(client):
    rows = client.get("/api/city-rank?top=5").get_json()["data"]["list"]
    assert len(rows) == 5
    gdp = [r["gdp_yi"] for r in rows]
    assert gdp == sorted(gdp, reverse=True)


def test_city_rank_invalid_top(client):
    assert client.get("/api/city-rank?top=0").status_code == 400
    assert client.get("/api/city-rank?top=abc").status_code == 400


def test_city_map_coord(client):
    rows = client.get("/api/city-map").get_json()["data"]["list"]
    assert len(rows) == 21
    for r in rows:
        assert len(r["coord"]) == 2
        assert 108 < r["coord"][0] < 118          # 广东经度范围
        assert 20 < r["coord"][1] < 26            # 广东纬度范围


def test_industry_total(client):
    rows = client.get("/api/industry").get_json()["data"]["list"]
    assert len(rows) == 3
    total = sum(r["value"] for r in rows)
    overview = client.get("/api/overview").get_json()["data"]["gdp_yi"]
    assert abs(total - overview) / overview < 0.02   # 三次产业合计≈全省 GDP


def test_404(client):
    r = client.get("/api/not-exists")
    assert r.status_code == 404
    assert r.get_json()["code"] == 404
