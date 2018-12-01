import argparse
import json
from termcolor import colored,cprint
import colorama

# mat cli design
parser = argparse.ArgumentParser(description='for Mansion-IDPS status verification and health testing.')

parser.add_argument('-t','--target',metavar='PROTOCOL:URL',required=True,
	                dest='target_url',action='store',
	                help='set the target device URL for this checking')

parser.add_argument('-u', '--username',metavar='username', required=False,
                    dest='login_username', action='store',
                    help='username for login the target device')

parser.add_argument('-p', '--password',metavar='password', required=False,
                    dest='login_password', action='store',
                    help='password for login the target device')

parser.add_argument('-l',dest='login_needed', action='store_true',
                    help='the target device need to login first')

parser.add_argument('-v', dest='verbose', action='store_true',
                    help='verbose mode')

args = parser.parse_args()

# Enable colored output
colorama.init()

def mat_print_title(text):
	cprint("-"*64,'blue')
	cprint(text,"white","on_blue")
	cprint("-"*64,'blue')

def mat_print_item(desc,val,warning=False):
	if warning:
		print("{}:\t\t[ {} ]".format(desc,colored(val,"white","on_red")))
	else:
	    print("{}:\t\t[ {} ]".format(desc,colored(val,"white","on_green")))

# Output the collected arguments
if args.verbose:
	mat_print_title("<--MAT parameters-->")
	mat_print_item("target setting",args.target_url)
	mat_print_item("login needed",args.login_needed)
	mat_print_item("login username",args.login_username)
	mat_print_item("login password",args.login_password)

# Test case,test procedure will be blocked by ERROR
mat_tcs_setting = {
	"login_test":{
	    "desc": "Login Mansion System"
	},
	"service_check":{
	    "desc": "Checking Mansion Service Status"
	},
	"setting_check":{
	    "desc": "Checking Mansion Service Setting"
	},
	"hardware_check":{
	    "desc": "Checking Mansion Hardware Setting"
	},
	"license_check":{
	    "desc": "Checking Mansion License"
	}
}

# T1: login_test
# T2: hardware_check
# T3: service_check
# T4: setting_check
# T5: license_check
