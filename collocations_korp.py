import pandas, re, os, json, sys, urllib, time
import wget
import numpy as np

ALL = 0
BETWEEN = 1
LEFT = 2
RIGHT = 3

def get_concordance(cqp, corpora):
  CQP = urllib.parse.quote_plus(cqp)
  URL = "https://www.kielipankki.fi/korp/api8/query?default_context=1%20sentence&show=sentence%2Clemma%2Clemmacomp%2Cpos%2Cmsd%2Cdephead%2Cdeprel%2Cref%2Clex%2Chyph%2Cocr%2Ccc%2Cvpos&show_struct=text_label%2Ctext_publ_title%2Ctext_publ_id%2Ctext_issue_date%2Ctext_issue_no%2Ctext_issue_title%2Ctext_elec_date%2Ctext_language%2Ctext_page_no%2Ctext_sentcount%2Ctext_tokencount%2Ctext_img_url%2Ctext_publ_type%2Cparagraph_id%2Csentence_id%2Ctext_date%2Ctext_filename_orig%2Ctext_filename_metadata%2Ctext_version_added%2Ctext_binding_id%2Ctext_sum_lang%2Csentence_lang%2Csentence_lang_conf&start=0&end=2000&corpus=CORPUS&cqp=CQP&query_data=&context=&incremental=true&default_within=sentence&within=&sort=random"
  url = URL.replace("CQP", CQP).replace("CORPUS", "%2C".join(corpora))

  tmp = wget.download(url)

  with open(tmp, "r", encoding="utf-8") as f:
    data = json.load(f)

  os.remove(tmp)

  entries = []
  i = 0
  print("The corpora have ",len(data['kwic']), "occurrences of this word.")
  for i,row in enumerate(data['kwic']):

    start = row['match']['start']
    end = row['match']['end']
    structs = row['structs']
    structs.update({"hit":i, "nexus":0, "start": start, "end":end})
    structs["hit"] = i
    structs['nexus'] = 0
    structs['match_id'] = i

    if "structs" in structs:
      del structs['structs']

    for j,token in enumerate(row['tokens']):

      if "structs" in token:
        del token['structs']
      token.update(structs)
      #print(str(token['ref']),str(start))
      if (start+1 == j) or (end == j):
        token['nexus'] = 1


      entries.append(token)

  df = pandas.DataFrame(entries)
  df['ref'] = [int(x) for x in df.ref]
  df['start'] = [int(x) for x in df.start]
  df['end'] = [int(x) for x in df.end]
  return df

def get_collocates(df, win):

  df['collocate_left'] = [1 if (ref > start-win) and (ref < start) else 0 for ref, start, end in zip(df.ref, df.start, df.end)]
  df['collocate_between'] = [1 if (ref > start+1) and (ref < end) else 0 for ref, start, end in zip(df.ref, df.start, df.end)]
  df['collocate_right'] = [1 if (ref > end) and (ref < end+win) else 0 for ref, start, end in zip(df.ref, df.start, df.end)]

  df['collocate_all'] = df[['collocate_left', 'collocate_between', 'collocate_right']].sum(axis=1)
  df = df[(df.collocate_all >= 1) & (df.pos != "Punct")].groupby(["lemma", "pos"])[['collocate_all', 'collocate_left', 'collocate_between', 'collocate_right']].sum()

  df = df[df.collocate_all > 4]
  col_df = pandas.DataFrame(df).reset_index()

  return col_df

def get_frequency(lemma, pos, corpora):
  URL = 'https://www.kielipankki.fi/korp/api8/count?corpus=CORPUS&cqp=CQP'
  CQP = urllib.parse.quote_plus(f'[lemma="{lemma}" & pos="{pos}"]')
  url = URL.replace("CQP", CQP).replace("CORPUS", "%2C".join(corpora))
 
  try:
    tmp = wget.download(url)
  except:
    print(url)


  with open(tmp, "r", encoding="utf-8") as f:
    data = json.load(f)

  os.remove(tmp)


  return data['combined']['sums']['absolute']

def get_tf(corpora):

  URL = "https://korp.csc.fi/cgi-bin/korp/korp.cgi?command=info&corpus=CORPUS"
  url = URL.replace("CORPUS", ",".join(corpora))

  tmp = wget.download(url)

  with open(tmp, "r", encoding="utf-8") as f:
    data = json.load(f)

  os.remove(tmp)

  return data['total_size']

def LMI(*X):

  w1, w2, w12, tf = get_col_variables(X)
  if w12*w2*w1 == 0: return 0

  p1 = w1/tf
  p2 = w2/tf
  p12 = w12/tf
  return w12*np.log(p12/(p1*p2))

def get_col_variables(X):
  
  w1 = X[0]['w1']
  w2 = X[0]['w2']
 
  if X[1] == ALL:
    w12 = X[0]['collocate_all']
  elif X[1] == LEFT:
    w12 = X[0]['collocate_left']
  elif X[1] == BETWEEN:
    w12 = X[0]['collocate_between']
  elif X[1] == RIGHT:
    w12 = X[0]['collocate_right']

  tf = X[0]['tf']

  return w1, w2, w12, tf


def get_frequency_list_depr(lemma_list, corpora):

  frequencies = []
  times = []

  for lemma, pos in lemma_list:
    t0 = time.time()
    frequencies.append(get_frequency(lemma, pos, corpora))
    times.append(time.time()-t0)
    mean = sum(times)/len(times)
    left = len(lemma_list)-len(times)
    time_left = mean*left
    minutes = str(time_left/60).split(".")[0]
    seconds = str(time_left - (int(minutes)*60)).split(".")[0]
    print("\rtime left", minutes, "minutes and ", seconds, "seconds", end="")

def get_frequency_list(lemma_list, corpora):

  frequencies = []
  times = []
  df = pandas.DataFrame()
  stop = False
  URL = 'https://www.kielipankki.fi/korp/api8/count_all?group_by=lemma,pos&corpus=CORPUS&cqp=CQP&start=START&end=END'
  i = 0
  entries = []
  while stop != True:
    url = URL.replace("CORPUS", "%2C".join(corpora)).replace("START", str(i*100000)).replace("END", str((i+1)*100000))
    tmp = wget.download(url)
    with open(tmp, "r", encoding="utf-8") as f:
      data = json.load(f)
      print(url)
      for row in data['combined']['rows']:
        entry = {"lemma":row['value']['lemma'][0], "pos":row['value']['pos'][0], "freq":row['absolute']}
        entries.append(entry)
    os.remove(tmp)
    c_df = pandas.DataFrame(entries)
    min = c_df['freq'].min()
    df = pandas.concat([df, c_df])
    if min <= 5: break
    i += 1

  df = df.groupby(['lemma', 'pos']).sum()
  res = [df.loc[x]['freq'] if x in df.index else 0 for x in lemma_list]
  return res

  return frequencies

class CollocationData:

  def __init__(self, cqp, corpora):

    self.cqp = cqp
    self.corpora = corpora
    self.con_df = get_concordance(cqp, corpora)
    self.collocates = False
    self.tf = get_tf(corpora)
    print("Querying for collocate information from corpora, this may take a while...")
    self.build_collocates()
    self.measure_collocation_scores()
    print("\nDone! The word has ", self.collocates.shape[0], "collocates.")



  def new_window(self, win):
    self.build_collocates(win)
    self.measure_collocation_scores()

  def build_collocates(self, win=5):

    self.collocates = get_collocates(self.con_df, win)
    collocate_list = [(lemma, pos) for lemma, pos in zip(self.collocates.lemma, self.collocates.pos)]
    frequency_list = get_frequency_list(collocate_list, self.corpora)
    self.collocates['w2'] = frequency_list
    self.collocates['w1'] = self.con_df["match_id"].drop_duplicates().shape[0]
    self.collocates['tf'] = self.tf

  def measure_collocation_scores(self):
    self.collocates['LMI_all'] = self.collocates.apply(LMI, axis=1, args=([ALL]))
    self.collocates['LMI_between'] = self.collocates.apply(LMI, axis=1, args=([BETWEEN]))
    self.collocates['LMI_left'] = self.collocates.apply(LMI, axis=1, args=([LEFT]))
    self.collocates['LMI_right'] = self.collocates.apply(LMI, axis=1, args=([RIGHT]))


  def top_collocates(self, measure="LMI", group="all", N=10, pos="all"):
  
    if measure.lower() == "abs": 
      measure = "collocate"
    if measure.lower() == "lmi": 
      measure = "LMI"
    score = measure+'_'+group
    
    if pos.lower() == "all":
      collocates = self.collocates
    else:
      collocates = self.collocates[self.collocates.pos == pos]
    
    for x in collocates[['lemma', 'pos', score]].sort_values(score, ascending=False).head(int(N)).iterrows():
      row = x[1]
      print(row['lemma'], "\t", row['pos'],"\t", row[score])
