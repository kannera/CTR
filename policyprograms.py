# -*- coding: utf-8 -*-
"""Untitled0.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1eangGmooMnR6949cJpsKtdraJSbW0Ryy
"""

import requests
import pandas
import matplotlib.pyplot as plt
import io
import time
import numpy as np

def download_party_corpus(party):
  url = f"https://media.githubusercontent.com/media/kannera/CTR/main/pol_programs/{party}_full_corpus.tsv"
  corpus = requests.get(url).content
  corpus = pandas.read_csv(io.StringIO(corpus.decode('utf-8')), sep="\t", index_col=0)
  return corpus

def lmi(f1, f2, f12, N):
  p1 = f1/N
  p2 = f2/N
  p12 = f12/N
  score = np.log(p12/(p1*p2))*f12
  return score

def pmi(f1, f2, f12, N):
  p1 = f1/N
  p2 = f2/N
  p12 = f12/N
  score = np.log(p12/(p1*p2))
  return score

class PolicyCorpus:

  def __init__(self):

    self.download_metadata()
    self.download_full_corpus()
    self.get_full_frequency_chart()

  def download_metadata(self):
    url = "https://raw.githubusercontent.com/kannera/CTR/main/pol_programs/metadata.tsv"
    self.metadata = requests.get(url).content
    self.metadata = pandas.read_csv(io.StringIO(self.metadata.decode("utf-8")), sep="\t", index_col=0)
    self.metadata['year'] = [int(x) if x != "-" else 0 for x in self.metadata['year']]
  

  def download_full_corpus(self):
    parties = self.metadata['party_abbr'].drop_duplicates()
    party_corpora = []
    for p in parties:
      print("downloading", p)
      try:
        df = download_party_corpus(p)
      except:
        continue
        print("missed", p, "for whatever reason")
      party_corpora.append(df)
    self.corpus = pandas.concat(party_corpora)
 
  def get_full_frequency_chart(self):
    self.ff = self.corpus.groupby("lemma").count()[['doc_id']]
    self.ff.columns = ["f2"]
    self.ff['N'] = self.corpus.shape[0]
    self.ff = self.ff[self.ff.f2 > 4]


  def get_subcorpus(self, lemma="all", party="all", start_year="all", end_year="all", p_type="all"):
    articles = self.metadata

    if party != "all":
      if type(party) == str:
        articles = articles[articles.party_abbr == party]
      elif type(party) in (list, tuple):
        articles = articles[articles.party_abbr.isin(party)]
    if p_type != "all":
      if type(p_type) == str: 
        articles = articles[articles.type == type]
      elif type(p_type) in (list, tuple):
        articles = articles[articles.type.isin(p_type)]
    if start_year != "all":
      articles = articles[articles.year >= start_year]
    if end_year != "all":
      articles = articles[articles.year <= end_year]
    if lemma != "all":
      if type(lemma) == str:
        occs = self.corpus[self.corpus.lemma == lemma]['doc_id'].drop_duplicates().to_list()
      elif type(lemma) in (list, tuple):
        occs = self.corpus[self.corpus.lemma.isin(lemma)]['doc_id'].drop_duplicates().to_list()
      articles = articles[articles.doc_id.isin(occs)]

    subcorpus = articles[['doc_id', 'year']].merge(self.corpus, how="inner", left_on="doc_id", right_on="doc_id")
    return subcorpus

  def get_relative_frequency_for_lemma(self, lemma, party="all", start_year="all", end_year="all", p_type="all", by=['year']):
    subcorpus = self.get_subcorpus(party=party, start_year=start_year, end_year=end_year, p_type=p_type)
    subcorpus = subcorpus.merge(self.metadata[['doc_id', 'party_abbr', 'type']], how='left', left_on="doc_id", right_on="doc_id")
    if type(lemma) == str:
      lemma_frequencies = subcorpus[subcorpus.lemma == lemma].groupby(by).count()[['word']]
    elif type(lemma) in (list, tuple):
      lemma_frequencies = subcorpus[subcorpus.lemma.isin(lemma)].groupby(by).count()[['word']]
    total_frequencies = subcorpus.groupby(by).count()[['doc_id']]
    frequencies = total_frequencies.merge(lemma_frequencies, how="left", left_index=True, right_index=True).fillna(0)
    frequencies.columns = ['N', 'f']
    frequencies['r'] = frequencies['f']/frequencies['N']
    return frequencies

  def get_keywords_for(self, lemma="all", party="all", start_year="all", end_year="all", p_type="all"):
    subcorpus = self.get_subcorpus(lemma=lemma, party=party, start_year=start_year, end_year=end_year, p_type=p_type)
    Ns = subcorpus.shape[0]
    subcorpus = subcorpus.groupby("lemma").count()[['word', 'doc_id']]
    subcorpus['Ns'] = Ns
    subcorpus = subcorpus[['word', 'Ns']]
    subcorpus.columns = ['f1', 'Ns']

    subcorpus = subcorpus.merge(self.ff, how="left", left_index=True, right_index=True)[['f1', 'f2', 'N', 'Ns']]
    subcorpus = subcorpus[~np.isnan(subcorpus.N)]

    subcorpus['Nc'] = subcorpus['N'] - subcorpus['Ns']
    subcorpus['fc'] = subcorpus['f2'] - subcorpus['f1']

    subcorpus['f1d'] = subcorpus['f1'] + 1
    subcorpus['fcd'] = subcorpus['fc'] + 1
    subcorpus['Ncd'] = subcorpus['Nc'] + subcorpus.shape[0]
    subcorpus['Nsd'] = subcorpus['Ns'] + subcorpus.shape[0]

      
    subcorpus['%diff'] = (subcorpus['f1d']/subcorpus['Nsd'] - subcorpus['fcd']/subcorpus['Ncd'])/(subcorpus['fcd']/subcorpus['Ncd'])
    subcorpus = subcorpus[['f1','f2','fc','%diff']]
    return subcorpus




  def get_collocates_for(self, lemma, party="all", start_year="all", end_year="all", p_type="all"):
    subcorpus = self.get_subcorpus(party=party, start_year=start_year, end_year=end_year, p_type=p_type)

    lemma_occs = subcorpus[subcorpus.lemma == lemma][['doc_id', 's_rank', 'pos']]
    lemma_occs['hit_pos'] = lemma_occs['pos']
    lemma_occs = lemma_occs[['doc_id', 's_rank', 'hit_pos']]

    f1 = lemma_occs.shape[0]
    subcorpus = subcorpus.merge(lemma_occs, how="left")
    subcorpus = subcorpus[~np.isnan(subcorpus.hit_pos)]

    subcorpus['collocate'] = [1 if (pos > hit_pos-5) and (pos < hit_pos+5) else 0 for pos, hit_pos in zip(subcorpus['pos'], subcorpus['hit_pos'])]
    subcorpus = subcorpus[subcorpus.collocate == 1]
    subcorpus = subcorpus.groupby("lemma").count()[['doc_id', 'word']]
    subcorpus.columns=['f12', "x"]
    subcorpus = subcorpus[subcorpus.f12 > 4]

    subcorpus = subcorpus.merge(self.ff, how="left", left_index=True, right_index=True)[['f12', 'f2', 'N']]

    subcorpus['f1'] = f1
    subcorpus['LMI'] = [lmi(f1, f2, f12, N) for f1, f2, f12, N in zip(subcorpus['f1'], subcorpus['f2'], subcorpus['f12'], subcorpus['N'])]
    subcorpus['PMI'] = [pmi(f1, f2, f12, N) for f1, f2, f12, N in zip(subcorpus['f1'], subcorpus['f2'], subcorpus['f12'], subcorpus['N'])]

    return subcorpus


  def reconstruct_text(self, doc_id):
    res = ""
    sub = self.corpus[self.corpus.doc_id == doc_id][['par_id', 'word']]
    pars = []
    chunk = []
    this_p = 0

    for p,w in zip(sub['par_id'], sub['word']):

      if p > this_p:
        pars.append(" ".join(chunk))
        chunk = [str(w)]
        this_p = p
      else:
        chunk.append(str(w))

    return "".join(pars)
