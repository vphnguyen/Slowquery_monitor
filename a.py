import yaml,datetime,pytz
import re,os

#=============================================== FMT
help_fs="# HELP %s %s."
type_fs="# TYPE %s gauge"
metric_fs="%s %s"
metricL_fs="%s{%s=\"%s\"} %s"
#=========  CHECKING INPUT FILENAME CONFIG  --
# Check config file
with open('/home/kali/Downloads//config.yml', 'r') as cf_file:
	config_content = yaml.safe_load(cf_file)
if not cf_file:
	print("cannot found config file.....")
	exit()

# Check digested path
if 'digest_filename' in config_content:
	print(config_content['digest_filename'])
else:
	config_content['digest_filename']="digested.rp"
	print("Not config filename, setted to:",config_content['digest_filename'])

def unitRender(input):
	if input.endswith("k"):
		return float(input[0:len(input)-1]) * 1000
	elif input.endswith("M"):
		return float(input[0:len(input)-1]) * 1000000
	elif input.endswith("B"):
                return float(input[0:len(input)-1]) * 1000000000
	else:
		return input

#=========
def  renderTimeRange(content):
	array  = content.strip().split(" ")
# Time range: 2022-02-15T06:54:49 to 2022-02-15T07:24:34

	dt_obj_s = datetime.datetime.fromisoformat(array[3] )
	dt_obj_e = datetime.datetime.fromisoformat(array[5] )
	dif= dt_obj_e - dt_obj_s
#Asia/ Ho_Chi_Minh
	tz = pytz.timezone('Europe/Sofia')
	dt_obj_s=dt_obj_s.astimezone(tz)
	dt_obj_e=dt_obj_e.astimezone(tz)
	stf= '%H:%M:%S -- %d/%m/%Y'
	dt_obj_s = dt_obj_s.strftime(stf)
	dt_obj_e = dt_obj_e.strftime(stf)

	print("FROM: ",  dt_obj_s)
	print("TO:   ",  dt_obj_e)

	print("About: ",str(datetime.timedelta(seconds=dif.total_seconds())) )
#=========
def render_Overall(content):
	array = content.strip().split(" ")
	#==
	global total, unique, QPS
	total = unitRender(  array[array.index('total,')-1]  )
	unique = array[array.index('unique,')-1]
	QPS = array[array.index('QPS,')-1]

#=========
def render_Rank1(content):
	array = re.sub(' +',' ',content).strip().split(" ")
	global r1_c, r1_rsp, r1_pc, r1_vm, r1_tp
	r1_c=array[5]
	r1_rsp=array[3]
	r1_pc=array[4]
	r1_vm=array[7]
	r1_tp=array[8]

#=========

def metric_format(name,help,metrics):
    name=name.replace(" ","_")
    fname = help_fs % (name.strip(), help.strip())
    ftype = type_fs % (name.strip())
    fmetric=""
    if type(metrics) is dict:
        for k,v in metrics.items():
            fmetric += metricL_fs % (name,"type",k,v) + ("\n" if list(metrics.keys())[-1] != k else "")
    else:
        fmetric = metric_fs % (name, metrics)

    return "%s\n%s\n%s" %(fname,ftype,fmetric)

#=========
ovr_keys = ['Overall' , 'total' , 'unique' , 'QPS']
i=0
#==
print("|| --begin--")
if os.path.exists(config_content['digest_filename']):
	for id,line in  enumerate(  open(config_content['digest_filename'],'r')   ):
		#
		if line.startswith("# Time range:") and "to" in line:
			renderTimeRange(line)
		if line.startswith("# Profile"):
			i = id+3
			print("======= FOUNDED RANK 1  =====: ")
		if not i  == 0 and id == i:
			render_Rank1(line)
			break
		if  line.startswith("# Overall") and all(akey in line for akey in ovr_keys):
			print("======= FOUNDED OVERALL =====")
			render_Overall(line)
else:
	print("Cannot found RAW slow_log...\n at: %s \n\t Checkout config again ! "%(config_content['digest_filename']))
	exit()
print("--end-- ||")

#==========
print("===================== OVERALL =====================")
print("- Total :",total," Queries")
print("- QPS :", QPS,"/s")
print("- UNIQUE:", unique,)

print("===================== RANK 1 =====================")
print("=== Calls:", r1_c," times")
print("=== Response:", r1_rsp, " sec")
print("=== Percentage:", r1_pc)
print("=== V/M:", r1_vm)
print("=== Type:", r1_tp)

print("===================== MORE   =====================")
pc= float(r1_pc.strip("%"))/100
print("Total consumed time:", float(r1_rsp) / pc, " sec")
print("One r1 call take about:", float(r1_rsp)/float(r1_c)," sec")
print("RATE Unique/Total:", float(unique) / float(total) * 100 ," %")

# ======  Final output for file collector  =======================
mtrs_f = open('metrics.txt','w')
#------
num1 = {
  "total": total,
  "unique": unique,
}
r1 = {
  "calls": r1_c,
  "response": r1_rsp,
  "percentage": r1_pc.replace("%",""),
  "VM": r1_vm
}
#------
print(metric_format("Number of queries","All what you need in overall",num1),file=mtrs_f)
print(metric_format("QPS during log","Number of QPS in during slow_log's",QPS),file=mtrs_f)
print(metric_format("Rank1 details","Rank1 number result",r1),file=mtrs_f)
