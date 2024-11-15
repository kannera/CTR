from scipy.stats import mannwhitneyu
import pandas

df = pandas.read_csv("https://raw.githubusercontent.com/kannera/CTR/main/kyselydata.tsv", sep="\t")

def u_test(by_group):
  
  values = list(df[by_group].drop_duplicates().values)
  result = mannwhitneyu(df[df[by_group] == values[0]]['vastaus 2'].values, df[df[by_group] == values[1]]['vastaus 2'].values, axis=None)
  print("mean for", values[0], ":", df[df[by_group] == values[0]]['vastaus 2'].mean())
  print("mean for", values[1], ":", df[df[by_group] == values[1]]['vastaus 2'].mean())
  print("p", round(result.pvalue * 100, 5), "%")
  
  return result
