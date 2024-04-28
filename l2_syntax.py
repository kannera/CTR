import pandas
import os

fils = os.listdir("l2_conllu/")
df = pandas.DataFrame()
for fl in fils:
  data = pandas.read.csv("l2_conllu/"+fl, sep="\t")
  data['text'] = fl
  df = pandas.concat([df, data])
  
