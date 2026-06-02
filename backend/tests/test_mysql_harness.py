def test_mysql_client_health(mysql_client):
    response = mysql_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
