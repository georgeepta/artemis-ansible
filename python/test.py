import subprocess


subprocess.Popen(
                ["/home/george/UOC-CSD/Diploma_Thesis/python/mitigation_trigger.py", "-i", "{\"key\": \"xxxx\", \"prefix\": \"130.10.1.0/25\"}"],
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
)
