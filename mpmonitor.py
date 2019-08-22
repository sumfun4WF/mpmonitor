import sys
import time
import signal
import requests
import json
import getpass
import steam.webauth as wa
from collections import OrderedDict
from io import StringIO
import lxml.html

s = requests.Session()

# Platform selection
while True:
	platform = input("Which platform are you using? (steam/mycom)\n")
	if platform.lower()=='steam':
		isSteam=True
	elif platform.lower()=='mycom':
		isSteam=False
	else:
		continue
	break

# Login credentials request
email = input("Email/Username: ")
password = getpass.getpass("Password: ")
# Login credentials request

def steam_login():
	# Login to steam
	user = wa.WebAuth(email, password)
	try:
		user.login()
	except wa.CaptchaRequired:
		print("Please complete the captcha: "+user.captcha_url)
		captcha_code=input("Please input the captcha response code: ")
		user.login(captcha=captcha_code)
	except wa.EmailCodeRequired:
		email_code=input("Please input the email verification code: ")
		user.login(email_code=email_code)
	except wa.TwoFactorCodeRequired:
		tfa_code=input("Please input the 2FA code: ")
		user.login(twofactor_code=tfa_code)
	# Copy cookies to session
	s.cookies.update(user.session.cookies)
	while True:
		try:
			entrance=s.get('https://auth-ac.my.com/social/steam?continue=https://account.my.com/social_back/?continue=https://wf.my.com/en/&failure=https://account.my.com/social_back/?soc_error=1&continue=https://wf.my.com/en/')
			openid_login={}
			html = StringIO(entrance.content.decode())
			tree = lxml.html.parse(html)
			root = tree.getroot()
			for form in root.xpath('//form[@name="loginForm"]'):
				for field in form.getchildren():
					if 'name' in field.keys():
						openid_login[field.get('name')]=field.get('value')
			s.headers.update({'referer': entrance.url})
			steam_redir=s.post('https://steamcommunity.com/openid/login', data=openid_login)
			s.get('https://auth-ac.my.com/sdc?from=https%3A%2F%2Fwf.my.com')
			get_token = s.get('https://wf.my.com/minigames/user/info').json()
			s.cookies['mg_token'] = get_token['data']['token']
			s.cookies['cur_language'] = 'en'
		except:
			continue
		break
		
def mycom_login():
	# Base header
	payload = {
		'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		'Accept-Encoding':'gzip, deflate, br',
		'Accept-Language':'en-US,en;q=0.9,it;q=0.8',
		'Cache-Control':'max-age=0',
		'Connection':'keep-alive',
		'Content-Type':'application/x-www-form-urlencoded',
		'Cookie':'s=dpr=1; amc_lang=en_US; t_0=1; _ym_isad=1',
		'DNT':'1',
		'Host':'auth-ac.my.com',
		'Origin':'https://wf.my.com',
		'Referer':'https://wf.my.com/kiwi',
		'Upgrade-Insecure-Requests':'1',
		'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'
		}
	login_data = {
		'email':email,
		'password':password,
		'continue':'https://account.my.com/login_continue/?continue=https%3A%2F%2Faccount.my.com%2Fprofile%2Fuserinfo%2F',
		'failure':'https://account.my.com/login/?continue=https%3A%2F%2Faccount.my.com%2Fprofile%2Fuserinfo%2F',
		'nosavelogin':'0'
		}
	while True:
		try: 
			s.post('https://auth-ac.my.com/auth',headers=payload,data=login_data)
			s.get('https://auth-ac.my.com/sdc?from=https%3A%2F%2Fwf.my.com')
			s.get('https://wf.my.com/')  
			get_token = s.get('https://wf.my.com/minigames/user/info').json()
			s.cookies['mg_token'] = get_token['data']['token']
			s.cookies['cur_language'] = 'en'
		except:
			continue
		break
		
def login():
	if isSteam:
		steam_login()
	else:
		mycom_login()

def get_mg_token():
	get_token = s.get('https://wf.my.com/minigames/user/info').json()
	s.cookies['mg_token'] = get_token['data']['token']

#Class for color and text customization
class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def signal_handler(signal, frame):
	print ('\n'+bcolors.WARNING+"Crate Manager was interrupted!"+bcolors.ENDC)
	sys.exit(0)

def res_count():
	main_json = s.get("https://wf.my.com/minigames/craft/api/user-info").json()
	level1=main_json['data']['user_resources'][0]['amount']
	level2=main_json['data']['user_resources'][1]['amount']
	level3=main_json['data']['user_resources'][2]['amount']
	level4=main_json['data']['user_resources'][3]['amount']
	level5=main_json['data']['user_resources'][4]['amount']
	output = "\033[92m\nCurrent resources\033[0m \nLevel 1: %d | Level 2: %d | Level 3: %d | Level 4: %d | Level 5: %d \n" % (level1,level2,level3,level4,level5)
	return output

print (bcolors.OKGREEN+bcolors.HEADER+"\nMarketplace Monitor"+bcolors.ENDC)

# LOGIN AND CHECK USER
login()
user_check_json = s.get('https://wf.my.com/minigames/bp/user-info').json()
try:
	print ("Logged in as {}".format(user_check_json['data']['username']))
except KeyError:
	print ("Login failed.")
	sys.exit(0)
# LOGIN AND CHECK USER

signal.signal(signal.SIGINT, signal_handler)
isSkin=input('Are you buying skin?(yes/no)\n')
if isSkin=='yes':
	item=input('Please input the item id of the skin: ')
	matching='item_id'
else:
	item=input('Please input the name of item you would like to buy: ')
	matching='title'
budget=input('Please input your budget: ')
done=False
while done==False:
	try:
		mp_list=s.get('https://wf.my.com/minigames/marketplace/api/all').json()
		for x in mp_list['data']:
			if x[matching].lower()==item.lower() and x['min_cost']*1.05<=int(budget):
				price=x['min_cost']
				eid=x['entity_id']
				item_type=x['type']
				data_to_buy={
					'entity_id':eid,
					'cost':price,
					'type':item_type
					}
				status=s.post('https://wf.my.com/minigames/marketplace/api/buy',data=data_to_buy).json()
				if status['state']=='Success':
					done=True
	except (KeyError,ValueError,TypeError,requests.exceptions.ChunkedEncodingError,json.decoder.JSONDecodeError,requests.exceptions.ConnectionError):
		login()
		pass
	time.sleep(1)
print ("\nUnexpected exit out of the while.")
