import sys
help_fs="# HELP %s %s."
type_fs="# TYPE %s gauge"
metric_fs="%s %s"
metricL_fs="%s{%s=\"%s\"} %s"

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

metrics_f = open('metrics.txt','w')
metrics = {
  "total": 3000,
  "unique": 123,
  "rank1": 99999
}

print(metric_format("number of queries","this is its descrp",metrics))

mtrs_f = open('metrics.txt','w')
print(metric_format("number of queries","this is its descrp",metrics),file=mtrs_f)



#print(metrics, file=metrics_f)
input("hi")
