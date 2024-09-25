Have you ever wanted to control your Philips Hue lights using discord? This bot will help you with that. 
Before we begin I want to say that this version is designed to be cloud based, not local, mainly because I wanted to put it on external server, but it should be easy to rework it into local, by just modifying request to hue servers.

Setup:
      Start with hue variables

1. Go to https://developers.meethue.com/my-apps/ , and register account.

2. On the same website in "Remote Hue API appids" or " my apps" create new app, fill app name and description with whatever you want and callback url with " https://localhost " and submit it.

3. Now you have HUE_CLIENT_ID and HUE_CLIENT_SECRET, to put in the script.

4. Now go to" https://api.meethue.com/v2/oauth2/authorize?client_id=HUE_CLIENT_ID&response_type=code&state=123 " , after replacing HUE_CLIENT_ID with real values and authorize it. 

5.After successful authorization it should redirect you to the page looking like "https://localhost/?code=auth_code&state=123" , remember this is one time use code if you use it you must go back to step 4 to get a new code.

6. Edit the setup1 file, and input the values , save it and run it. 

7.You get two values HUE_REFRESH_TOKEN and Access Token, put the first into a script.

8.Modify setup2 file with your Access Token, and run it. 

9. If it was successful push the psychical button on your hue bridge.

10.After pushing it, modify setup3 file with Access Token, and run it.  You should get username as a response, put it into script as HUE_APPLICATION_KEY. 

Now the discord part

11. Go to " https://discord.com/developers/applications/ " and create new application.

12. In the bot tab click reset a token, you will get DISCORD_TOKEN, put it into script.

13. Go to General Information tab, to get APPLICATION ID.

14. Go to " https://discord.com/oauth2/authorize?client_id=APPLICATION ID&permissions=2147491840&integration_type=0&scope=bot " and add bot to your server. 


Now the script is ready to run, if you're trying to run it in the private channel, be sure that the bot has sufficient permissions to be on that channel.

Use / commands to control it.

