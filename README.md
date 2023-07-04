This file serves as a ReadMe for this code. USE AT YOUR OWN RISK. THIS CODE WAS WRITTEN BY AN AMATEUR AND CONTAINS BUGS/INEFFICIENCIES. DO NOT USE WITHOUT MODIFYING FOR YOUR OWN PURPOSES. I AM NOT RESPONSIBLE FOR DAMAGE OR EXCESS POWER CONSUMPTION FOR YOUR USE/MISUSE OF THIS CODE.

The purpose of the code is to read excess solar usage from an Emporia-monitored power meter and then tell a Tesla to start charging, set a power draw, adjust up/down the power draw, and stop charging depending on available power conditions. The whole goal is to avoid grid draw to the extent possible while using solar to charge the car, even if there are times where it doesn’t use as much solar power as it can.

This code works best if you have a Tesla with stable internet connection, a home charger, and any non-battery-based home solar setup that can be monitored with an Emporia Vue device. This can probably be customized for electrical panel-based Emporia devices.

The main 3rd party libraries this uses are teslapy and pyemvue. 

Let’s start:

The whole code is wrapped in a function that only operates from 8AM to 5:30PM and will run every 2 minutes during that timeframe.

What stops the code entirely? Only certain protections, and these are imperfect:

1. Charging above 50A (i.e. Supercharging)
2. 10 attempts in the last 30 minutes when drawing from the grid is in excess of 2kW (i.e., the car was set to charge at 5A 10 different times in 30 minutes).

What stops the car from charging again while running the code every 2 minutes? 

1. Charging is complete to target charge level set by you in the Tesla app or in the car. (Further customization would note this and then tell the program to stop until a later date, or something.)

The first part of the code, through lines 50, authenticate your Emporia user and get status from the device. Sometimes the API returned [None] for charging, so there is logic to repeat the API call until a non-None response is received. Then, if there are multiple responses in a list, it picks only the first one from the list.

Then, the code uses pyemvue to authenticate your Tesla account using a browser. You will only need to do this infrequently. It will prompt you to sign in using the link provided in the console. You sign in through any browser, and then copy the URL from the URL bar on your browser window when you receive the 404 error. Paste the URL back into the console to authenticate. I do not know what the expiration period for this “token” is but I imagine it is also revoked when you change your Tesla password. 

Beginning line 99, the program will issue commands to the car if charging is stopped and there is available excess solar in increments of less than 1.5kW, 1.5-2.4kW, 2.4-3.6kW, 3.6-4.8kW and 4.8 to >6kW. These should be customized to your preferences and your solar output.

Beginning line 153, the program will issue commands to the car if it is currently charging. It will slow down charging if at certain increments. If drawing more than 2kW from the grid, it will set the car to charge at 5A rather than stopping to avoid repeated start/stop cycles of the HV contactors on your Tesla. It begins making a list of when the car was set to charge at 5A. If it accumulates more than 10 instances of the within 30 minutes, it will stop charging as it assumes the solar output is done for the day. If you have high-draw devices that run for more than 30 minutes, like pool pumps, hot tub heaters, HVAC, etc., you can adjust these intervals so it gives up charging after an hour of trying, rather than half an hour, for example.

Beginning line 197, the program will issue commands to the car to increase power consumption depending on how much excess solar is available while the car is charging. These should also be adjusted to your solar panel setup/capacity. Each one of these has a hard stop at 40A, which is custom to my charging circuit. (I have a 50A breaker and I should charge no more than 42A continuously, which is 80% of the rated circuit load. I rounded down to 40A). You can customize this for higher if you have a 60A breaker and want to limit it at 48A. For some reason, the Tesla app will show a high charging limit even if it may not be able to draw that much. This in-program 40A limit is a safety feature since the app behaves unexpectedly.

The program will continue to run every 2 minutes.

Overall, the tolerances and intervals for excess charging are quite wide, but it largely avoids extensive/excessive draw from the grid. 

To sum up, areas for modification/improvement for your own uses are:

Intervals for solar capacity. 
Stopping the script from waking the car every 2 minutes once the car has reached desired target charge level.
Better scheduling in general.
GUI. 

Find the code useful? Consider sending me a tip of $5 – or whatever you feel appropriate – via PayPal to a.leonard.tech@gmail.com, or via Venmo at @Andrew-Leonard-6 (last phone digits 1839). Thanks!
