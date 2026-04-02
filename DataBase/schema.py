def read_data(data) -> dict:
    return {
        "id": str(data["_id"]),
        "altitude": data.get("altitude", {}),
        "temperature": data.get("temperature", {}),
        "gps": data.get("gps", {})
    }

def list_serial(datas) -> list:
    """Iterates through the MongoDB cursor and serializes every document"""
    return [read_data(item) for item in datas]

def post_data():
    return {"Message": "Data was added"}