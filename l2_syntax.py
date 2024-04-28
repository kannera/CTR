import pandas
import os
conllu_path = "https://raw.githubusercontent.com/kannera/CTR/main/l2_conllu/"

df = pandas.DataFrame()
for i in range(14):
  text_path = f"https://raw.githubusercontent.com/kannera/CTR/main/l2_conllu/{i}_text_parsed.conllu.csv"
  data = pandas.read_csv(text_path, sep="\t")
  data['text_id'] = i
  df = pandas.concat([df, data])
   
