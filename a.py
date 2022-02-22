import yaml,datetime,pytz
import re,os


#=============================================== FMT
# Fromat cho string đầu ra dưới dạng prometheus
help_fs="# HELP %s %s."
type_fs="# TYPE %s gauge"
metric_fs="%s %s"
metricL_fs="%s{%s=\"%s\"} %s"

#=============================================== Global variables ==============
# Khởi tạo các biến global
config_content ={}
total = unique = QPS = None
ranks = []
profile_line = 0

#===============================================  CHECKING YAML CONFIG  --
# =========== Kiểm tra file config
with open('/home/kali/Downloads/slowquery_monitor/config.yml', 'r') as cf_file:
	config_content = yaml.safe_load(cf_file)
	if config_content is None:
		config_content={}
if not cf_file:
	print("cannot found config file.....")
	exit()

# ============ Kiểm tra đường dẫn File đầu VÀO
if 'digest_filename' in config_content:
	print("INPUT d: ",config_content['digest_filename'])
else:
	config_content['digest_filename']="a.txt"
	print("Not config digested, set to:",config_content['digest_filename'])

# ============ Kiểm tra đường dẫn File đầu RA
if 'metrics_output_destination' in config_content:
	print("OUTPUT :",config_content['metrics_output_destination'])
else:
	config_content['metrics_output_destination']="tesst___metrics.prom"
	print("Not config out file, set to:",config_content['metrics_output_destination'])


#=============================================== small RENDER ==================
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
	#======
	print("FROM: ",  dt_obj_s)
	print("TO:   ",  dt_obj_e)
	print("About: ",str(datetime.timedelta(seconds=dif.total_seconds())) )

#=============================================== MAIN RENDER ==================
def render_Overall(content):
	array = content.strip().split(" ")
	#==
	global total, unique, QPS
	total = unitRender(  array[array.index('total,')-1]  )
	unique = array[array.index('unique,')-1]
	QPS = array[array.index('QPS,')-1]

#=========
def render_Allrank(content):
	array = re.sub(' +',' ',content).strip().split(" ")
	if (array[1].isnumeric()):
		global ranks
		ranks.append(
		{
			"rank" : array[1],
			"calls" : array[5],
			"response" : array[3],
			"percentage": array[4],
			"vm" : array[7]
		})

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

#=============================================== MAINNNNNNNN ===================
ovr_keys = ['Overall' , 'total' , 'unique' , 'QPS']

#==
if os.path.exists(config_content['digest_filename']):
	for index, line in  enumerate(  open(config_content['digest_filename'],'r')   ):
		# --- Overall ---
		if  line.startswith("# Overall") and all(akey in line for akey in ovr_keys):
			render_Overall(line)
		# --- Time range ---
		if line.startswith("# Time range:") and "to" in line:
			renderTimeRange(line)
		# --- Profile ---
		if line.startswith("# Profile"):
			profile_line = index + 3
		if not profile_line  == 0 and index in range( profile_line , profile_line+10 ):
			if (  not line.startswith("# ") ):
				break
			render_Allrank(line)
else:
	print("Cannot found RAW slow_log...\n at: %s \n\t Checkout config again ! "%(config_content['digest_filename']))
	exit()

for i in ranks:
	print("OUT DICT:=====",i)
maxResponse = max(ranks, key=lambda x: (float(x['response'])/float(x['calls'])) )
print("Max Resp:\n",maxResponse)
print(ranks[0].keys())

#==========
print("===================== OVERALL =====================")
print("- Total :",total," Queries")
print("- QPS :", QPS,"/s")
print("- UNIQUE:", unique,)


print("===================== MORE   =====================")
# pc= float(r1_pc.strip("%"))/100
# print("Total consumed time:", float(r1_rsp) / pc, " sec")
# print("One r1 call take about:", float(r1_rsp)/float(r1_c)," sec")
# print("RATE Unique/Total:", float(unique) / float(total) * 100 ," %")

# ======  Final output for 6file collector  =======================

mtrs_f = open(config_content['metrics_output_destination'],'w')
#------
overall_array = {
  "total": total,
  "unique": unique
}
#=======================================
def to_dict(dict , ikey):
	out ={}
	for i in dict:
		out.update( {"rank%s"%i['rank'] : i[ikey]} )
	return out



#------
print(metric_format("Number of queries","All what you need in overall===============================",overall_array),file=mtrs_f)
print(metric_format("QPS during log","Number of QPS in during slow_logs=============================",QPS),file=mtrs_f)
print(metric_format("Maxsp","Number of QPS in during slow_logs=============================",maxResponse["rank"]),file=mtrs_f)

print(metric_format("response","Rank1 number result============================================",to_dict(ranks,"response")),file=mtrs_f)

print(metric_format("calls","Rank1 number result============================================",to_dict(ranks,"calls")),file=mtrs_f)

print(metric_format("percentage","Rank1 number result============================================",to_dict(ranks,"percentage")),file=mtrs_f)

print(metric_format("vm","Rank1 number result============================================",to_dict(ranks,"vm")),file=mtrs_f)
