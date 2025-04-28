from google import genai

client = genai.Client(api_key="")
flight_data = '''{
    "flight1": {
        "price":2000,
        "flightTime":6
    },
    "flight1": {
        "price":4000,
        "flightTime":3
    },
    "flight1": {
        "price":6000,
        "flightTime":2
    }
}'''
response = client.models.generate_content(
    model="gemini-2.0-flash", contents=f"below, you will find a group of flight information base on price and flight time, choose the best one:{flight_data} choose one and print it out only"
)
print(response.text)