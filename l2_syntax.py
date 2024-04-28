import pandas
import os
conllu_path = "https://raw.githubusercontent.com/kannera/CTR/main/l2_conllu/"
fils = os.listdir(conllu_path)
df = pandas.DataFrame()
for fl in fils:
  data = pandas.read.csv(conllu_path+fl, sep="\t")
  data['text'] = fl
  df = pandas.concat([df, data])
  
