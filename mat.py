import sys
import time
import argparse
import json
from termcolor import colored,cprint
import colorama
from requests_html import HTMLSession
import warnings

# mat cli design
parser = argparse.ArgumentParser(description='for Mansion-IDPS status verification and health testing.')

parser.add_argument('-t','--target',metavar='PROTOCOL:URL',required=True,
	                dest='target_url',action='store',
	                help='set the target device URL for this checking')

parser.add_argument('-u', '--username',metavar='username', required=False,
                    dest='login_username', action='store',default='root',
                    help='username for login the target device')

parser.add_argument('-p', '--password',metavar='password', required=False,
                    dest='login_password', action='store',default='mansion',
                    help='password for login the target device')

parser.add_argument('-l',dest='login_needed', action='store_true',
                    help='the target device need to login first')

parser.add_argument('-v', dest='verbose', action='store_true',
                    help='verbose mode')

args = parser.parse_args()

# Enable colored output
colorama.init()
mat_print_line_max = 64
mat_print_line_desc_max = 48

def mat_print_title(text):
	cprint("-"*mat_print_line_max,'blue')
	cprint(text,"white","on_blue")
	cprint("-"*mat_print_line_max,'blue')

def mat_print_item(desc,val,warning=False):
	t_desc_len = len(desc)
	t_line_seg_num = int(t_desc_len/mat_print_line_desc_max)
	t_line_seg_last = t_desc_len%mat_print_line_desc_max
	t_space_num = 0
	if t_line_seg_last != 0:
		t_space_num = mat_print_line_desc_max - t_line_seg_last
	for x in range(0,t_line_seg_num):
		print(desc[x*mat_print_line_desc_max:(x+1)*mat_print_line_desc_max])
	if t_line_seg_last > 0:
		print(desc[t_line_seg_num*mat_print_line_desc_max:],end="")

	if warning:
		print("=>" + " "*(t_space_num + 1) + "[ {} ]".format(colored(val,"white","on_red")))
	else:
		if val in ("Disabled","Off"):
			print("=>" + " "*(t_space_num + 1) + "[ {} ]".format(colored(val,"white")))
		else:
			print("=>" + " "*(t_space_num + 1) + "[ {} ]".format(colored(val,"white","on_green")))

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

# invalid externsion's warning output
warnings.filterwarnings('ignore')

mat_session = None
mat_session_verify = False
mat_session_rep = None
mat_session_key = None
mat_session_key_val = None
# T1: login_test
mat_print_title("<--Login System-->")
mat_session = HTMLSession()
mat_session.verify = mat_session_verify
try:
    mat_session_rep = mat_session.get(args.target_url)
except:
    mat_print_item("Connect to {}".format(args.target_url),"Failed",True)
    sys.exit(1)
mat_print_item("Connect to {}".format(args.target_url),"Success")

temp_ele = mat_session_rep.html.xpath('//form/input')
mat_session_key = temp_ele[0].attrs["name"]
mat_session_key_val = temp_ele[0].attrs["value"]
try:
    mat_session_rep = mat_session.post(args.target_url,data={
	    mat_session_key:mat_session_key_val,
	    "usernamefld":args.login_username,"passwordfld":args.login_password,"login":1})
except:
	mat_print_item("Authentication with {}:{}".format(args.login_username,args.login_password),"Failed",True)
	sys.exit(1)
if mat_session_rep.ok:
	mat_print_item("Authentication with {}:{}".format(args.login_username,args.login_password),"Success")
else:
	mat_print_item("Authentication with {}:{}".format(args.login_username,args.login_password),"Failed",True)
	sys.exit(1)

# T2: system_check
mat_print_title("<--System Check-->")
try:
	mat_session_rep = mat_session.get(args.target_url+"/widgets/api/get.php?load=system,traffic,gateway,interfaces&_="+str(time.time()))
except:
	mat_print_item("System information get","Failed",True)
	sys.exit(1)
if mat_session_rep.ok:
	mat_print_item("System information get","Success")
else:
	mat_print_item("System information get","Failed",True)
	sys.exit(1)
temp_json = json.loads(mat_session_rep.html.html)
try:
	temp_obj = temp_json["data"]["system"]
	mat_print_item("{}".format(temp_obj["versions"][0]),"OK")

	temp_obj = temp_json["data"]["system"]["cpu"]
	mat_print_item("CPU({} {} {})".format(
		temp_obj["cpus"],
	    temp_obj["max.freq"],
	    temp_obj["cur.freq"]),"OK")
	over_load = False
	for x in temp_obj["load"]:
		if float(x) > 60:
			over_load = True
			break
	mat_print_item("System cpu load({} {} {})".format(
		temp_obj["load"][0],
		temp_obj["load"][1],
		temp_obj["load"][2]),"Checked",over_load)

	over_load = False
	temp_obj = temp_json["data"]["system"]["kernel"]["memory"]
	temp_used = float(temp_obj["used"])/float(temp_obj["total"])
	if temp_used > 0.5:
		over_load = True
	mat_print_item("System mem load({}G {}G)".format(
		round(float(temp_obj["total"])/1024/1024/1024),
		round(float(temp_obj["used"])/1024/1024/1024,2)),"Checked",over_load)

	over_load = False
	temp_obj = temp_json["data"]["system"]["kernel"]["pf"]
	temp_used = float(temp_obj["states"])/float(temp_obj["maxstates"])
	if temp_used > 0.5:
		over_load = True
	mat_print_item("System pfilter table({} {})".format(
		temp_obj["maxstates"],
		temp_obj["states"]),"Checked",over_load)

	over_load = False
	temp_obj = temp_json["data"]["system"]["kernel"]["mbuf"]
	temp_used = float(temp_obj["total"])/float(temp_obj["max"])
	if temp_used > 0.5:
		over_load = True
	mat_print_item("System packet buf table({} {})".format(
		temp_obj["max"],
		temp_obj["total"]),"Checked",over_load)

	temp_obj = temp_json["data"]["system"]["disk"]["devices"]
	for x in temp_obj:
		mat_print_item("System disk({}) [{} {} {}]".format(
			x["device"],
			x["size"],x["used"],x["capacity"]),"Checked")

	temp_obj = temp_json["data"]["system"]["disk"]["swap"]
	if 0 != len(temp_obj["device"]):
	    mat_print_item("System disk swap","On",True)
	else:
		mat_print_item("System disk swap","Off")

	temp_obj = temp_json["data"]["interfaces"]
	temp_used = len(temp_obj)
	mat_print_item("System {} interface enabled".format(temp_used),"Checked")
	for x in temp_obj:
		mat_print_item("System interface {} {} {}".format(
			x["name"],x["status"],x["ipaddr"]),"Checked")

except:
	mat_print_item("System information checked","Failed",1)
	sys.exit(1)
# print(json.dumps(temp_json["data"],indent=2))

# T3: service_check
mat_print_title("<--Service Check-->")
try:
	mat_session_rep = mat_session.get(args.target_url + "/api/ids/service/status")
	if mat_session_rep.ok:
	    temp_json = json.loads(mat_session_rep.html.html)
	    if temp_json.get("status") == "running":
	        mat_print_item("Service ids status","Running")
	    else:
	    	mat_print_item("Service ids status","Stopped",True)
	else:
		mat_print_item("Service ids status","Unkonw",True)
except:
	mat_print_item("Service ids status","Unkonw",True)
	pass

try:
	mat_session_rep = mat_session.get(args.target_url + "/api/ids/settings/get")
	if mat_session_rep.ok:
		temp_json = json.loads(mat_session_rep.html.html)

		temp_obj = temp_json["ids"]["general"]
		if temp_obj.get("promisc") == "1":
			mat_print_item("Service ids interface promisc mode","Enabled")
		else:
			mat_print_item("Service ids interface promisc mode","Disabled")
		
		temp_obj = temp_json["ids"]["general"]["interfaces"]
		for k in temp_obj:
			if temp_obj[k]["selected"] == 1:
				mat_print_item("Service ids interface {}".format(temp_obj[k]["value"]),"Enabled")
			else:
				mat_print_item("Service ids interface {}".format(temp_obj[k]["value"]),"Disabled")

		temp_obj = temp_json["ids"]["general"]["syslog"]
		if temp_obj == "0":
			mat_print_item("Service ids syslog","Disabled")
		else:
			mat_print_item("Service ids syslog","Enabled")

		temp_obj = temp_json["ids"]["general"]["LogPayload"]
		if temp_obj == "0":
			mat_print_item("Service ids syslog log-payload","Disabled")
		else:
			mat_print_item("Service ids syslog log-payload","Enabled")

		temp_obj = temp_json["ids"]["general"]["homenet"]
		temp_str = ""
		for k in temp_obj:
			if temp_obj[k]["selected"] == 1: temp_str = temp_str + "|" + temp_obj[k]["value"]
		mat_print_item("Service ids homenet({})".format(temp_str),"Checked")
except:
	pass

try:
	mat_session_rep = mat_session.get(args.target_url + "/services_ntpd.php")

	temp_obj = mat_session_rep.html.find('input[name="timeservers_host[]"]')
	temp_str = ""
	for x in temp_obj:
		temp_str = temp_str + "|" + x.attrs.get("value")
	mat_print_item("Service ntp remote server({})".format(temp_str),"Checked")

	temp_obj = mat_session_rep.html.find('input[name="timeservers_prefer[]"]')
	temp_str = ""
	for x in temp_obj:
		if x.attrs.get("checked") == "checked": temp_str = temp_str + "|" + x.attrs.get("value")
	mat_print_item("Service ntp prefer server({})".format(temp_str),"Checked")

	temp_obj = mat_session_rep.html.find('input[name="timeservers_noselect[]"]')
	temp_str = ""
	for x in temp_obj:
		if x.attrs.get("checked") == "checked": temp_str = temp_str + "|" + x.attrs.get("value")
	mat_print_item("Service ntp forbiden server({})".format(temp_str),"Checked")

	#print(mat_session_rep.html.html)
except:
	mat_print_item("Service ntp status get","Failed",True)
	pass

# T4: setting_check
mat_print_title("<--Setting Check-->")
try:
    mat_session_rep = mat_session.get(args.target_url+"/system_general.php")
except:
	mat_print_item("Setting general get","Failed",True)
	pass

try:
	temp_obj = mat_session_rep.html.find('#timezone [selected="selected"]',first=True).text
	if temp_obj != "Asia/Shanghai":
		mat_print_item("Setting timezone({})".format(temp_obj),"Warning",True)
	else:
		mat_print_item("Setting timezone({})".format(temp_obj),"OK")
except:
	mat_print_item("Setting timezone get","Failed",True)
	pass

try:
    temp_obj = mat_session_rep.html.find('tbody>tr>td>input[name^="dns"]')
    for x in temp_obj:
    	if len(x.attrs["value"]) != 0:
    		temp_str = "Enabled"
    	else:
    	    temp_str = "Disabled"
    	mat_print_item("Setting dns remote [{}:{}]".format(x.attrs["name"],x.attrs["value"]),temp_str)
except:
	mat_print_item("Setting dns remote get","Failed",True)

try:
	temp_obj = mat_session_rep.html.find('[name="dnsallowoverride"]')[0]
	if temp_obj.attrs.get("checked") == "checked":
		temp_str = "Yes"
	else:
		temp_str = "No"
	mat_print_item("Setting dns override by SP setting",temp_str)
except:
	mat_print_item("Setting dns override by SP setting","Unkonw",True)
	pass

try:
	mat_session_rep = mat_session.get(args.target_url + "/system_advanced_admin.php")

	# sshd
	temp_obj = mat_session_rep.html.find('[name="enablesshd"]')[0]
	if temp_obj.attrs.get("checked") == "checked":
		temp_str = "Enabled"
	else:
		temp_str = "Disabled"
	mat_print_item("Setting admin ssh login",temp_str)

	temp_obj = mat_session_rep.html.find('[name="sshdpermitrootlogin"]')[0]
	if temp_obj.attrs.get("checked") == "checked":
		temp_str = "Enabled"
	else:
		temp_str = "Disabled"
	mat_print_item("Setting admin ssh root login",temp_str)

	temp_obj = mat_session_rep.html.find('[name="sshpasswordauth"]')[0]
	if temp_obj.attrs.get("checked") == "checked":
		temp_str = "Enabled"
	else:
		temp_str = "Disabled"
	mat_print_item("Setting admin ssh passwd login",temp_str)

	temp_obj = mat_session_rep.html.find('[name="sshport"]')[0]
	mat_print_item("Setting admin ssh port({})".format(temp_obj.attrs["placeholder"]),"Checked")

	# console
	temp_obj = mat_session_rep.html.find('[name="usevirtualterminal"]')[0]
	if temp_obj.attrs.get("checked") == "checked":
		temp_str = "Enabled"
	else:
		temp_str = "Disabled"
	mat_print_item("Setting admin console login",temp_str)

	temp_obj = mat_session_rep.html.find('[name="primaryconsole"]>option[selected="selected"]')[0]
	mat_print_item("Setting admin console primary({})".format(temp_obj.attrs["value"]),"Checked")

	temp_obj = mat_session_rep.html.find('[name="secondaryconsole"]>option[selected="selected"]')[0]
	mat_print_item("Setting admin console secondary({})".format(temp_obj.attrs["value"]),"Checked")

	temp_obj = mat_session_rep.html.find('[name="serialspeed"]>option[selected="selected"]')[0]
	mat_print_item("Setting admin console serial speed({})".format(temp_obj.attrs["value"]),"Checked")

	temp_obj = mat_session_rep.html.find('[name="disableconsolemenu"]')[0]
	if temp_obj.attrs.get("checked") == "checked":
		temp_str = "Enabled"
	else:
		temp_str = "Disabled"
	mat_print_item("Setting admin console passwd protected",temp_str)

except:
	mat_print_item("Setting admin get","Failed",True)
	sys.exit(1)

try:
	mat_session_rep = mat_session.get(args.target_url + "/diag_logs_settings.php")

	# syslog remote
	temp_obj = mat_session_rep.html.find('input[name^="remoteserver"]')
	temp_str = ""
	temp_str1 = "Disabled"
	for x in temp_obj:
		temp_str = temp_str + "|" + x.attrs["value"]
		if len(x.attrs["value"]) > 0: temp_str1 = "Enabled"
	mat_print_item("Setting syslog remote({})".format(temp_str),temp_str1)

	temp_obj = mat_session_rep.html.find('input[name="logall"]')[0]
	temp_str = ""
	if temp_obj.attrs.get("checked") == "checked":
		temp_str = temp_obj.attrs["name"]
	else:
		temp_obj = mat_session_rep.html.find('input[name="system"]')[0]
		if temp_obj.attrs.get("checked") == "checked": temp_str = temp_str + "|" + temp_obj.attrs["name"]
		temp_obj = mat_session_rep.html.find('input[name="filter"]')[0]
		if temp_obj.attrs.get("checked") == "checked": temp_str = temp_str + "|" + temp_obj.attrs["name"]
		temp_obj = mat_session_rep.html.find('input[name="dhcp"]')[0]
		if temp_obj.attrs.get("checked") == "checked": temp_str = temp_str + "|" + temp_obj.attrs["name"]
		temp_obj = mat_session_rep.html.find('input[name="dns"]')[0]
		if temp_obj.attrs.get("checked") == "checked": temp_str = temp_str + "|" + temp_obj.attrs["name"]
		temp_obj = mat_session_rep.html.find('input[name="ids"]')[0]
		if temp_obj.attrs.get("checked") == "checked": temp_str = temp_str + "|" + temp_obj.attrs["name"]
	mat_print_item("Setting syslog service({})".format(temp_str),"Checked")
except:
	mat_print_item("Setting log get","Failed",True)
	pass

# T5: license_check
mat_print_title("<--License Check-->")
try:
	mat_session_rep = mat_session.get(args.target_url+"/license.php")
except:
	mat_print_item("License check","Failed",True)
try:
	temp_obj = mat_session_rep.html.search('<div class="alert {alert_lic}" role="alert"')["alert_lic"]
	if temp_obj != "alert-info":
		mat_print_item("License check","Failed",True)
	else:
		mat_print_item("License check","Success")
except:
	mat_print_item("License check","Unkown",True)
	sys.exit(1)
