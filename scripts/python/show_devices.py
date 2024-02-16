import pyvisa


resource_manager = pyvisa.ResourceManager()
devices = resource_manager.list_resources()

for device in devices:
    client = resource_manager.open_resource(device)

    try:
        print(f'{device}: {client.query("*IDN?")}')
    except Exception as e:
        print(type(e), e)
    finally:
        client.close()
