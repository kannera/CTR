import pandas
import requests
from matplotlib import pyplot as plt
conllu_path = "https://raw.githubusercontent.com/kannera/CTR/main/l2_conllu/"

conll_keys = ['pos', 'word', 'lemma', 'upos', 'xpos', 'feats', 'dephead', 'deprel', 'X', 'Y']
entries = []
for i in range(14):
  req = requests.get(f"https://raw.githubusercontent.com/kannera/CTR/main/l2_conllu/{i}_text_parsed.conllu")
  lines = str(req.content).split("\\n")
  lines = [x.split("\\t") for x in lines]

  for line in lines:
    if len(line) == 10:
      entry = {x:y for x,y in zip(conll_keys, line)}
      entry.update({"text_id":i, "sent_id":sent})
      entries.append(entry)
    elif "sent_id" in line[0]:
      sent = line[0].split("=")[-1].replace(" ", "")

df = pandas.DataFrame(entries)
df['len'] = [len(x) for x in df.word]
sentences = df[['text_id', 'sent_id']].drop_duplicates().groupby("text_id").count()
metadata = pandas.read_csv("https://raw.githubusercontent.com/kannera/CTR/main/l2_conllu/metadata.tsv", sep="\t", index_col=0)[['äidinkieli', 'tyyppi']]

all_rels = list(set(list(df.deprel.values)))
subjs = [x for x in all_rels if "subj" in x]
objs = [x for x in all_rels if "obj" in x]
depmap = {"konjunktio": ["conj"], "subjekti":subjs, "objekti":objs, "predikaatti":['root'], "adjektiiviattribuutti":['amod'], "adverbiaali":['advmod', 'advcl']}
posmap = {"substantiivi":"N", "adjektiivi":"A", "verbi":"V", "pronomini":"Pron", "adverbi":"Adv"}

def analyse(k, color_by = False):
  colors = ["blue", "red", "green", "orange", "purple", "lightblue", "pink"]
  if k == "virkepituus":
    depc = df.groupby("text_id").count()[['pos']]
  elif k == "sanapituus":
    depc = df[['text_id', 'len']].groupby("text_id").mean()

  elif k in depmap:
    depc = df[df.deprel.isin(depmap[k])].groupby("text_id").count()[['pos']]
  
  elif k in posmap:
    depc = df[df.xpos == posmap[k]].groupby("text_id").count()[['pos']]
  
  res = sentences.merge(depc, how="left", left_index=True, right_index=True)
  res.columns = ['text', k]
  
  if k != "sanapituus":
    scorename = f"{k} per virke"
    res[scorename] = res[k]/res['text']
  
  else:
    scorename = "sanapituus"
    res[scorename] = res[k]

  if color_by == False:
    plt.scatter(res.index, res[scorename])
  else:
    res = res.merge(metadata, how="left", left_index=True, right_index=True)
    groups = list(res[color_by].drop_duplicates().values)
    for i,g in enumerate(groups):
      g_res = res[res[color_by] == g]
      plt.scatter(g_res.index, g_res[scorename], color=colors[i], label=g)
    
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.18),
          ncol=3, fancybox=True, shadow=True)


  plt.show()
  print(res[[color_by, scorename]])
