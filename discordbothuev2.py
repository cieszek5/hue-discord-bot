import discord
from discord import app_commands
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Replace these with your actual values
DISCORD_TOKEN = "Put here " #Bot Token from Discord Developer Portal
HUE_CLIENT_ID = "Put here" #Client ID from Remote Hue API appids
HUE_CLIENT_SECRET = "Put here" #Client Secret from Remote Hue API appids
HUE_REFRESH_TOKEN = "Put here" #Refresh Token from Setup 1 file.
DISCORD_CHANNEL_ID = Channel_ID  # Channel that bot will post to. Remember to not put this in quotes
HUE_APPLICATION_KEY = "Put here" #Username from Setup 3 file.

# Initialize the bot with no privileged intents
bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)

# Store the access token globally
access_token = None
lights = {}  # Store light information
groups = {}  # Store group information


async def get_access_token():
    global access_token
    if access_token is None:
        url = "https://api.meethue.com/v2/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": HUE_REFRESH_TOKEN
        }
        try:
            response = requests.post(url, data=data, auth=(HUE_CLIENT_ID, HUE_CLIENT_SECRET))
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data['access_token']
            logger.info("Successfully obtained new access token")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            raise Exception("Failed to get access token")
    return access_token


async def make_hue_request(method, endpoint, data=None):
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "hue-application-key": HUE_APPLICATION_KEY
    }
    url = f"https://api.meethue.com/route/clip/v2/resource{endpoint}"
    try:
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to Hue API: {e}")
        return None


async def fetch_lights():
    global lights
    light_response = await make_hue_request("GET", "/light")
    
    if light_response and light_response.status_code == 200:
        lights.clear()
        for light in light_response.json()['data']:
            name = light.get('metadata', {}).get('name') or light.get('id')
            lights[name] = light


class ControlView(discord.ui.View):
    def __init__(self, device_name):
        super().__init__()
        self.device_name = device_name

    @discord.ui.button(label="Turn On", style=discord.ButtonStyle.success)
    async def turn_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        await control_device(self.device_name, 'on')
        await interaction.response.send_message(f"{self.device_name} turned on.", ephemeral=True)

    @discord.ui.button(label="Turn Off", style=discord.ButtonStyle.danger)
    async def turn_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        await control_device(self.device_name, 'off')
        await interaction.response.send_message(f"{self.device_name} turned off.", ephemeral=True)

    @discord.ui.button(label="Change Brightness", style=discord.ButtonStyle.primary)
    async def change_brightness(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BrightnessModal(self.device_name))

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.secondary)
    async def exit_control(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Exited control mode.", ephemeral=True)
        await interaction.message.delete()


class BrightnessModal(discord.ui.Modal, title='Change Brightness'):
    brightness = discord.ui.TextInput(label='Brightness (0-100)', placeholder='Enter a value between 0 and 100')

    def __init__(self, device_name):
        super().__init__()
        self.device_name = device_name

    async def on_submit(self, interaction: discord.Interaction):
        try:
            brightness_value = int(self.brightness.value)
            if 0 <= brightness_value <= 100:
                await control_device(self.device_name, 'brightness', brightness_value)
                await interaction.response.send_message(f"Brightness of {self.device_name} set to {brightness_value}%", ephemeral=True)
            else:
                await interaction.response.send_message("Please enter a value between 0 and 100.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)


@tree.command(name='creategroup', description="Create a new group for your Hue lights")
async def create_group(interaction: discord.Interaction, group_name: str):
    await fetch_lights()
    
    if not lights:
        await interaction.response.send_message("No lights found. Please make sure your Hue bridge is connected and try again.", ephemeral=True)
        return

    embed = discord.Embed(title=f"Create Group: {group_name}", description="Select lights to add to the group:")
    
    options = [discord.SelectOption(label=name, value=name) for name in lights.keys()]
    select_menu = discord.ui.Select(placeholder="Choose lights...", options=options, max_values=len(options))
    
    async def select_callback(interaction: discord.Interaction):
        selected_lights = select_menu.values
        
        if not selected_lights:
            await interaction.response.send_message("You must select at least one light for the group.", ephemeral=True)
            return

        groups[group_name] = {
            "name": group_name,
            "lights": selected_lights,
            "on": {"on": False},
            "type": "Room"
        }
        
        await interaction.response.send_message(f"Group '{group_name}' created successfully with lights: {', '.join(selected_lights)}", ephemeral=True)

    select_menu.callback = select_callback
    view = discord.ui.View()
    view.add_item(select_menu)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name='listgroups', description="List all groups that have been created")
async def list_groups(interaction: discord.Interaction):
    if not groups:
        await interaction.response.send_message("No groups have been created yet.", ephemeral=True)
    else:
        embed = discord.Embed(title="Local Groups", description="Here are the groups you've created:")
        for name, group in groups.items():
            embed.add_field(name=name, value=f"Lights: {', '.join(group['lights'])}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def control_device(name: str, action: str, value=None):
    device = lights.get(name) or groups.get(name)
    if device:
        if name in lights:
            data = {}
            if action in ['on', 'off']:
                data["on"] = {"on": action == 'on'}
            elif action == 'brightness':
                data["dimming"] = {"brightness": value}
            await make_hue_request("PUT", f"/light/{device['id']}", data)
        else:
            if action in ['on', 'off']:
                device['on']['on'] = (action == 'on')
            elif action == 'brightness':
                if 'dimming' not in device:
                    device['dimming'] = {}
                device['dimming']['brightness'] = value
            
            for light_name in device['lights']:
                await control_device(light_name, action, value)


@tree.command(name='control', description="Control your Hue lights and groups")
async def control(interaction: discord.Interaction):
    await fetch_lights()

    embed = discord.Embed(title="Control Your Lights and Groups", description="Select a light or group to control:")
    
    options = [discord.SelectOption(label=name, value=name) for name in groups.keys()] + \
              [discord.SelectOption(label=name, value=name) for name in lights.keys()]
    
    select_menu = discord.ui.Select(placeholder="Choose a light or group...", options=options)

    async def select_callback(interaction: discord.Interaction):
        selected_name = select_menu.values[0]
        embed_detail = discord.Embed(title=f"Controlling: {selected_name}", description=f"Controls for {selected_name}:")
        
        device_info = lights.get(selected_name) or groups.get(selected_name)
        if device_info:
            embed_detail.add_field(name="Status", value=f"{'On' if device_info['on']['on'] else 'Off'}", inline=False)
            if 'dimming' in device_info:
                embed_detail.add_field(name="Brightness", value=f"{device_info['dimming']['brightness']}%", inline=False)

        await interaction.response.edit_message(embed=embed_detail, view=ControlView(selected_name))

    select_menu.callback = select_callback
    await interaction.response.send_message(embed=embed, view=discord.ui.View().add_item(select_menu))


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    await tree.sync()  # Sync commands with Discord
    logger.info(f'Slash commands synced!')



bot.run(DISCORD_TOKEN)
