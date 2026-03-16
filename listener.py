from google import genai
client = genai.Client(api_key="AIzaSyA0UweF1OEyEN-Q95NkOQpaem8mOaWdKtY")
form m in client.models.list()
print(f'modelo disponible: {m.name}')