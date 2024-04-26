from scipy.stats import mannwhitneyu
import pandas

def u_test(by_group):
  df = pandas.read_csv("https://raw.githubusercontent.com/kannera/CTR/main/kyselydata.tsv", sep="\t")

  by_group = "lukijaryhmä"
  values = list(df[by_group].drop_duplicates().values)
  print(mannwhitneyu(df[df[by_group] == values[0]]['vastaus 2'].values, df[df[by_group] == values[1]]['vastaus 2'].values))
