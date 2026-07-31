from httpx import AsyncClient


test_shipment_id = None


async def test_submit_shipment(client: AsyncClient, seller_token: str):
    # submit a shipment
    global test_shipment_id
    response = await client.post(
        url="/shipment/",
        json={
            "content": "shipment1",
            "weight": 10,
            "destination": 1,
            "client_contact_email": "client1@gmail.com"
        },
        headers={
            "Authorization": f"Bearer {seller_token}"
        }
    )
    test_shipment_id = response.json()["id"]
    assert response.status_code == 201


async def test_get_shipment(client: AsyncClient, seller_token: str):
    # get the shipment
    response = await client.get(
        url="/shipment/",
        params={
            "id": test_shipment_id
        },
        headers={
            "Authorization": f"Bearer {seller_token}"
        }
    )
    assert response.status_code == 200


async def test_update_shipment(client: AsyncClient, delivery_partner_token: str):
    response = await client.patch(
        url="/shipment/",
        params={
            "id": test_shipment_id,
        },
        json={
            "location": 19001
        },
        headers={
            "Authorization": f"Bearer {delivery_partner_token}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["timeline"][-1]["location"] == 19001


async def test_cancel_shipment(client: AsyncClient, seller_token: str):
    response = await client.get(
        url="/shipment/cancel",
        params={
            "id": test_shipment_id
        },
        headers={
            "Authorization": f"Bearer {seller_token}"
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["timeline"][-1]["status"] == "cancelled"
