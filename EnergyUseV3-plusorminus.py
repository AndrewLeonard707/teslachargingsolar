#!/usr/bin/python3

import teslapy
import pyemvue
import datetime
import time
import schedule
from pyemvue.enums import Scale, Unit

def func():

    def print_recursive(usage_dict, info, depth=0):
        for gid, device in usage_dict.items():
            for channelnum, channel in device.channels.items():
                name = channel.name
                if name == 'Main Meter':
                    name = info[gid].device_name
                print(channel.usage)
                if channel.nested_devices:
                    print_recursive(channel.nested_devices, info, depth+1)

    vue = pyemvue.PyEmVue()
    vue.login(username='a.leonard.tech@gmail.com', password='Darwin#123', token_storage_file='keys.json')

    devices = vue.get_devices()
    device_gids = []
    device_info = {}
    for device in devices:
        if not device.device_gid in device_gids:
            device_gids.append(device.device_gid)
            device_info[device.device_gid] = device
        else:
            device_info[device.device_gid].channels += device.channels

    usage_over_time, start_time = vue.get_chart_usage(devices[0].channels[0], datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(seconds=10), datetime.datetime.now(datetime.timezone.utc), scale=Scale.SECOND.value, unit=Unit.KWH.value)

    # Append current usage to a list file
    usage_list = []
    for usage in usage_over_time:
        if usage is not None:
            usage_list.append(str(usage*60*60))

    # Save the list to a file
    with open('energyuse.txt', 'a') as file:
        file.write('\n'.join(usage_list) + '\n')

    # Get last 1 lines -- was originally going to get average of last 5 lines, at 1 minute each but this can introduce some issues.
    with open('energyuse.txt', 'r') as file:
        lines = file.readlines()
        last_three_lines = lines[-1:]

    #yeah, it still reads last 3 lines... ignore this, it's just one line
    values = []
    for line in last_three_lines:
        value = line.strip()
        if value:
            values.append(float(value))

    # print 1 minute average of power consumption/sending -- is now just instant metering but still available to average in the future
    current_net_metering = sum(values) / len(values) if values else 0
    print("Instant net metering:", current_net_metering, " kW")

    # starts with Tesla API auth
    tesla = teslapy.Tesla('a.leonard.tech@gmail.com')
    if not tesla.authorized:
        print('Use browser to login. Page Not Found will be shown at success.')
        print('Open this URL: ' + tesla.authorization_url())
        tesla.fetch_token(authorization_response=input('Enter URL after authentication: '))

    #if authorized, proceeds
    vehicles = tesla.vehicle_list()
    vehicles[0].sync_wake_up()

    #pulls charging status and assigned current request
    if vehicles:
        # Retrieve the first vehicle
        vehicle = vehicles[0]

        # Access the vehicle's data
        vehicle_data = vehicle.get_vehicle_data()

        # Extract the charge_current_request value
        charge_current_request = vehicle_data.get('charge_state', {}).get('charge_current_request')
        charging_state = vehicle_data.get('charge_state', {}).get('charging_state')
        one_hundred_soc = vehicle_data.get

    else:
        print('No vehicles found.')

    #Some data to display about the car and its charging, plus defining some variables:
    chargingkW = (charge_current_request*240)
    print('Car was previously set to charge to this many amps: ',charge_current_request)
    print('Car was previously set to charge to this many watts: ', chargingkW)
    print('Car charging is currently ' + charging_state + '.')
    available_power = current_net_metering

    #to prevent code from interfering with Supercharging at 50A or higher if this is accidentally left running
    if charge_current_request > 50:
        exit()

    if charging_state == 'Stopped':

        if current_net_metering > -1.5:
            print('Not enough excess solar to begin charging.')

        if -1.5 > current_net_metering > -2.4:
            vehicles = tesla.vehicle_list()
            vehicles[0].sync_wake_up()
            vehicles[0].command('CHARGING_AMPS', charging_amps='5')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 5A for solar production between 1.5kW and 2.4kW, starting charge.')

        if -2.4 > current_net_metering > -3.6:
            vehicles = tesla.vehicle_list()
            vehicles[0].sync_wake_up()
            vehicles[0].command('CHARGING_AMPS', charging_amps='10')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 10A for solar production between 2.4kW and 3.6kW, starting charge.')

        if -3.6 > current_net_metering > -4.8:
            vehicles = tesla.vehicle_list()
            vehicles[0].sync_wake_up()
            vehicles[0].command('CHARGING_AMPS', charging_amps='15')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 15A for solar production between 3.6kW and 4.8kW, starting charge.')

        if -4.8 > current_net_metering > -6:
            vehicles = tesla.vehicle_list()
            vehicles[0].sync_wake_up()
            vehicles[0].command('CHARGING_AMPS', charging_amps='20')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 20A for solar production between 4.8kW and 6kW, starting charge.')

        if -6 > current_net_metering > -7.2:
            vehicles = tesla.vehicle_list()
            vehicles[0].sync_wake_up()
            vehicles[0].command('CHARGING_AMPS', charging_amps='25')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 25A for solar production between 6kW and 7.2kW, starting charge.')

        if -7.2 > current_net_metering:
            vehicles = tesla.vehicle_list()
            vehicles[0].sync_wake_up()
            vehicles[0].command('CHARGING_AMPS', charging_amps='30')
            vehicles[0].command('START_CHARGE')
            print('Set charging amps to 30A for solar production above 7.2kW, starting charge.')


    if charging_state == 'Charging':

        print('Available power is ', available_power, "W and positive number means drawing from grid.")

        if available_power > -0.6:
            vehicles[0].command('CHARGING_AMPS', charging_amps='5')
            print('Not enough available solar power, set charging amps to minimum of 5A.')
            # List to store the timestamps of 5A charging
            FiveAmpCount = []
            # Current timestamp when 5A charging is set, with a label
            FiveAmpSet = (time.strftime('%Y-%m-%d %H:%M:%S'))
            # Append the timestamp to the FiveAmpCount list
            FiveAmpCount.append(FiveAmpSet)
            # Write the timestamps to the text file
            with open('FiveAmpCount.txt', 'a') as file:
                file.write('\n'.join(FiveAmpCount) + '\n')
            print('If this continues for 30 more minutes or 20 instances, charging will be stopped automatically.')

        with open('FiveAmpCount.txt', 'r') as file:
            lines = file.readlines()
            recent_lines = []
            current_time = time.time()
            threshold = 30 * 60  # 30 minutes in seconds

            # Filter the lines within the last 30 minutes
            for line in lines:
                timestamp = time.mktime(time.strptime(line.strip(), '%Y-%m-%d %H:%M:%S'))
                if current_time - timestamp <= threshold:
                    recent_lines.append(line)

            # Check if there are at least 20 recent lines
            if len(recent_lines) >= 20:
                vehicles[0].command('STOP_CHARGE')
                print("There are at least 20 instances of charging being set to 5A in the last 30 minutes. Ending charging")

        if -.6 > available_power > -1.5:
            vehicles = tesla.vehicle_list()
            vehicles[0].sync_wake_up()
            vehicles[0].command('CHARGING_AMPS', charging_amps=(charge_current_request + 5))
            print('Set charging amps to', (charge_current_request + 5), ' for production between 0.3kW and 2.4kW, continuing charge.')

        if available_power < -1.5:
            print('You seem to have a lot of excess energy left, check to see what is going on here.')

schedule.every().day.at('07:00').until('20:00').do(func)
schedule.every(1).minutes.do(func)

func()
while True:
    schedule.run_pending()
    time.sleep(1)

#to-do list:
#log actions
#reduce Tesla API calls where possible
#set to run energy collection every minute but run Tesla adjustments every 5-15 minutes
#Improve Tesla authentication method for daily use

