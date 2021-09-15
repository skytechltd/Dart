import airsim #pip install airsim

# for car use CarClient() 
client = airsim.MultirotorClient()

png_image = client.simGetImage("0", airsim.ImageType.Scene)